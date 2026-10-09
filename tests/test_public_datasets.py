"""Regression checks for failure handling and external consumer entry points.

Run: python -m unittest discover -s tests -v
DuckDB query checks run when the optional duckdb package is installed.
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd

import ingest_public_datasets as ingestion
import scaffold_project
from public_dataset_specs import SOURCES
from validate_public_datasets import validate_frames


class DomainFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / "data/bike_sharing"
        cls.frames = {name: pd.read_parquet(base / "prepared" / f"{name}.parquet")
                      for name in ["hourly_rentals", "daily_rentals"]}
        cls.mart = pd.read_parquet(base / "marts/monthly_rentals.parquet")

    def setUp(self):
        self.frames = {key: frame.copy(deep=True) for key, frame in self.__class__.frames.items()}
        self.mart = self.__class__.mart.copy(deep=True)

    def validate(self):
        return validate_frames("bike_sharing", self.frames, "monthly_rentals", self.mart)

    def test_duplicate_snapshot_key_is_rejected(self):
        frame = self.frames["hourly_rentals"]
        frame.loc[1, "record_id"] = frame.loc[0, "record_id"]
        with self.assertRaisesRegex(ValueError, "unique snapshot keys"):
            self.validate()

    def test_source_row_cannot_be_reordered(self):
        self.frames["hourly_rentals"] = self.frames["hourly_rentals"].iloc[::-1].reset_index(drop=True)
        with self.assertRaisesRegex(ValueError, "contiguous source rows"):
            self.validate()

    def test_component_target_corruption_is_rejected(self):
        self.frames["hourly_rentals"].loc[0, "casual_count"] += 1
        with self.assertRaisesRegex(ValueError, "component counts reconcile"):
            self.validate()

    def test_required_missing_value_is_rejected(self):
        self.frames["hourly_rentals"].loc[0, "temperature_normalized"] = float("nan")
        with self.assertRaisesRegex(ValueError, "required values present"):
            self.validate()

    def test_mart_population_corruption_is_rejected(self):
        self.mart.loc[0, "source_records"] += 1
        with self.assertRaises(AssertionError):
            self.validate()


class SourcePinTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root / "data/wine_quality/raw/source.zip"
        self.lock = self.root / "sources.lock.json"
        self.root_patch = patch.object(ingestion, "ROOT", self.root)
        self.lock_patch = patch.object(ingestion, "LOCK", self.lock)
        self.root_patch.start()
        self.lock_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.lock_patch.stop)

    def create_pin(self):
        self.archive.parent.mkdir(parents=True)
        with ZipFile(self.archive, "w") as archive:
            archive.writestr("sample.csv", "x\n1\n")
        ingestion.write_json(self.lock, {"wine_quality": {
            "download_url": SOURCES["wine_quality"]["download_url"],
            "sha256": ingestion.sha256(self.archive), "size_bytes": self.archive.stat().st_size,
            "retrieved_at_utc": "2026-10-09T00:00:00+00:00"}})

    def test_cached_corruption_never_bypasses_pin(self):
        self.create_pin()
        with self.archive.open("ab") as archive:
            archive.write(b"changed")
        with self.assertRaisesRegex(ValueError, "cached archive SHA-256 mismatch"):
            ingestion.fetch("wine_quality", offline=True)

    def test_changed_upstream_is_not_published(self):
        self.create_pin()
        self.archive.unlink()  # Disposable test fixture only.
        buffer = io.BytesIO()
        with ZipFile(buffer, "w") as archive:
            archive.writestr("sample.csv", "x\n2\n")
        with patch.object(ingestion, "urlopen", return_value=io.BytesIO(buffer.getvalue())):
            with self.assertRaisesRegex(ValueError, "upstream content changed"):
                ingestion.fetch("wine_quality")
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.archive.with_suffix(".download").exists())

    def test_failed_network_leaves_no_partial_archive(self):
        with patch.object(ingestion, "urlopen", side_effect=URLError("test failure")), patch.object(ingestion.time, "sleep"):
            with self.assertRaises(URLError):
                ingestion.fetch("wine_quality")
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.archive.with_suffix(".download").exists())


class ConsumerTests(unittest.TestCase):
    def test_registry_paths_resolve_for_all_models(self):
        registry = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
        self.assertTrue((set(SOURCES) | {"global_superstore"}) <= {item["id"] for item in registry["projects"]})
        for project in registry["projects"]:
            self.assertTrue((ROOT / project["readme"]).is_file())
            for path in project["datasets"].values():
                self.assertTrue(list(ROOT.glob(path)), path)

    def test_source_to_prepared_column_mapping_is_complete(self):
        for project_id in SOURCES:
            catalog = json.loads((ROOT / "data" / project_id / "metadata/data_catalog.json").read_text(encoding="utf-8"))
            for dataset in catalog["logical_datasets"].values():
                if dataset["layer"] != "prepared":
                    continue
                derived = {"record_id", "source_file", "source_row", "subject", "wine_type",
                           "is_cancellation", "line_amount_gbp", "timestamp"}
                for field in dataset["schema"]:
                    self.assertEqual(field["source_column"] is None, field["name"] in derived)

    def test_sql_queries_run_with_real_data(self):
        try:
            import duckdb
        except ImportError:
            self.skipTest("Install optional duckdb to run SQL consumer checks")
        # Turn all repository-relative paths into absolute paths, then execute
        # outside the repo to prove that consumer loading does not need cwd.
        with tempfile.TemporaryDirectory() as temporary:
            import os
            previous = Path.cwd()
            try:
                os.chdir(temporary)
                with duckdb.connect() as connection:
                    for project_id in SOURCES:
                        query = (ROOT / "sql" / f"{project_id}_analysis.sql").read_text(encoding="utf-8")
                        query = query.replace("'data/", "'" + ROOT.as_posix().replace("'", "''") + "/data/")
                        result = connection.execute(query).df()
                        self.assertGreater(len(result), 0, project_id)
                        count, distinct, nulls = connection.execute(
                            "SELECT count(*), count(DISTINCT record_id), count(*) FILTER (WHERE record_id IS NULL) FROM source_data").fetchone()
                        self.assertEqual(count, SOURCES[project_id]["expected_rows"])
                        self.assertEqual((distinct, nulls), (count, 0))
            finally:
                os.chdir(previous)

    def test_tabular_scaffold_uses_observation_layers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(scaffold_project, "REPOSITORY_ROOT", root), patch.object(sys, "argv", [
                "scaffold_project.py", "example_snapshot", "Example", "--storage-model", "tabular_snapshot"]):
                scaffold_project.main()
            base = root / "data/example_snapshot"
            self.assertEqual({path.name for path in base.iterdir() if path.is_dir()}, {"raw", "prepared", "marts", "metadata"})
            catalog = json.loads((base / "metadata/data_catalog.json").read_text(encoding="utf-8"))
            self.assertIn("logical_datasets", catalog)


if __name__ == "__main__":
    unittest.main()
