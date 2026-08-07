"""Create the standard folder and metadata skeleton for a new analysis project.

Example:
    python scripts/scaffold_project.py customer_churn "Customer Churn" --domain crm_analytics
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scaffold a Parquet analysis project.")
    parser.add_argument("project_id", help="snake_case identifier, for example customer_churn")
    parser.add_argument("name", help="Human-readable project name")
    parser.add_argument("--domain", default="general_analytics", help="Analytics domain identifier")
    parser.add_argument("--difficulty", default="beginner", help="Learning difficulty label")
    return parser.parse_args()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if not PROJECT_ID_PATTERN.fullmatch(args.project_id):
        raise SystemExit("project_id must use snake_case and start with a letter")

    project_root = REPOSITORY_ROOT / "data" / args.project_id
    if project_root.exists():
        raise SystemExit(f"Project already exists: {project_root.relative_to(REPOSITORY_ROOT)}")

    for layer in ("dimensions", "facts", "marts", "metadata"):
        (project_root / layer).mkdir(parents=True, exist_ok=False)

    slug = args.project_id.replace("_", "-")
    write_json(
        project_root / "metadata" / "project.json",
        {
            "schema_version": 1,
            "id": args.project_id,
            "slug": slug,
            "name": args.name,
            "domain": args.domain,
            "difficulty": args.difficulty,
            "status": "draft",
            "description": "Mô tả ngắn bài toán và phạm vi dữ liệu.",
            "business_questions": ["Câu hỏi kinh doanh chính cần trả lời là gì?"],
            "learning_path": [
                {"id": "structure", "title": "Tổ chức dữ liệu", "output": "Mô tả đầu ra"},
                {"id": "query", "title": "Truy vấn", "output": "Mô tả đầu ra"},
                {"id": "eda", "title": "EDA", "output": "Mô tả đầu ra"},
                {"id": "dashboard", "title": "Dashboard", "output": "Mô tả đầu ra"},
            ],
        },
    )
    write_json(
        project_root / "metadata" / "data_catalog.json",
        {
            "schema_version": 1,
            "project_id": args.project_id,
            "datasets": {},
            "relationships": [],
            "files": [],
        },
    )
    (project_root / "README.md").write_text(
        f"# {args.name}\n\nMô tả source, pipeline build, validation và câu hỏi phân tích tại đây.\n",
        encoding="utf-8",
    )
    print(f"Created data project skeleton at {project_root.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
