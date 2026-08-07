(function () {
  const explorer = document.querySelector("[data-model-explorer]");
  if (!explorer) return;

  const nodeDetails = {
    "dim-date": {
      kind: "Role-playing dimension",
      title: "dim_date",
      copy: "Một calendar dimension được tái sử dụng cho hai ngữ cảnh. Query phải đặt alias rõ ràng để phân biệt order date và ship date.",
      grain: "1 row = 1 calendar date",
      key: "date_key",
      relations: "2 foreign key roles to fact_order",
    },
    "dim-customer": {
      kind: "Conformed dimension",
      title: "dim_customer",
      copy: "Giữ business identity và segment của khách hàng ở một nơi, thay vì lặp tên khách hàng trên từng dòng giao dịch.",
      grain: "1 row = 1 source customer",
      key: "customer_key",
      relations: "1-to-many with fact_order",
    },
    "dim-geography": {
      kind: "Conformed dimension",
      title: "dim_geography",
      copy: "Đóng gói market, region, country, state, city và postal code thành analytical member có khoá ổn định.",
      grain: "1 row = 1 geography combination",
      key: "geography_key",
      relations: "1-to-many with fact_order",
    },
    "dim-ship-mode": {
      kind: "Conformed dimension",
      title: "dim_ship_mode",
      copy: "Chuẩn hoá cách giao hàng để so sánh service level và shipping cost ở đúng grain order.",
      grain: "1 row = 1 shipping mode",
      key: "ship_mode_key",
      relations: "1-to-many with fact_order",
    },
    "dim-priority": {
      kind: "Conformed dimension",
      title: "dim_order_priority",
      copy: "Tách mức ưu tiên khỏi fact để filter và phân tích SLA không phụ thuộc vào free text trong source.",
      grain: "1 row = 1 priority label",
      key: "order_priority_key",
      relations: "1-to-many with fact_order",
    },
    "fact-order": {
      kind: "Fact table",
      title: "fact_order",
      copy: "Đại diện một order header duy nhất và là điểm nối giữa customer, geography, shipping, priority cùng hai vai trò date.",
      grain: "1 row = 1 order header",
      key: "order_key",
      relations: "6 incoming, 1 outgoing",
    },
    "fact-order-line": {
      kind: "Fact table",
      title: "fact_order_line",
      copy: "Chứa measures theo dòng sản phẩm. Sales, quantity, discount, profit và shipping cost được tổng hợp từ bảng này.",
      grain: "1 row = 1 product line",
      key: "line_item_key",
      relations: "2 incoming, feeds serving marts",
    },
    "dim-product": {
      kind: "Conformed dimension",
      title: "dim_product",
      copy: "Product key được tạo từ thuộc tính đầy đủ vì Product ID nguồn có thể gắn với nhiều mô tả sản phẩm.",
      grain: "1 row = 1 product attribute set",
      key: "product_key",
      relations: "1-to-many with fact_order_line",
    },
    marts: {
      kind: "Serving marts",
      title: "monthly_sales_kpis + country_sales_kpis",
      copy: "Aggregate đã tái tạo được từ facts và dimensions. Dùng cho dashboard nhanh, không thay thế fact source.",
      grain: "1 row = month hoặc country",
      key: "month_start / country",
      relations: "downstream aggregate from fact_order_line",
    },
  };

  const nodes = Array.from(explorer.querySelectorAll("[data-model-node]"));
  const links = Array.from(explorer.querySelectorAll("[data-model-link]"));
  const resetButton = explorer.querySelector("[data-model-reset]");
  const inspector = {
    kind: explorer.querySelector("[data-model-inspector-kind]"),
    title: explorer.querySelector("[data-model-inspector-title]"),
    copy: explorer.querySelector("[data-model-inspector-copy]"),
    grain: explorer.querySelector("[data-model-inspector-grain]"),
    key: explorer.querySelector("[data-model-inspector-key]"),
    relations: explorer.querySelector("[data-model-inspector-relations]"),
  };

  function updateLinks(activeNode, hoverNode) {
    links.forEach((link) => {
      const connectedNodes = link.dataset.modelLink.split(" ");
      link.classList.toggle("is-active", connectedNodes.includes(activeNode));
      link.classList.toggle("is-hovered", Boolean(hoverNode && connectedNodes.includes(hoverNode)));
    });
  }

  function activate(nodeId, focusNode) {
    const detail = nodeDetails[nodeId];
    if (!detail) return;
    explorer.dataset.activeNode = nodeId;
    nodes.forEach((node) => {
      const selected = node.dataset.modelNode === nodeId;
      node.setAttribute("aria-pressed", String(selected));
      node.classList.toggle("is-selected", selected);
      if (selected && focusNode) node.focus();
    });
    inspector.kind.textContent = detail.kind;
    inspector.title.textContent = detail.title;
    inspector.copy.textContent = detail.copy;
    inspector.grain.textContent = detail.grain;
    inspector.key.textContent = detail.key;
    inspector.relations.textContent = detail.relations;
    updateLinks(nodeId, null);
  }

  nodes.forEach((node) => {
    node.addEventListener("click", () => activate(node.dataset.modelNode, false));
    node.addEventListener("focus", () => activate(node.dataset.modelNode, false));
    node.addEventListener("mouseenter", () => updateLinks(explorer.dataset.activeNode, node.dataset.modelNode));
    node.addEventListener("mouseleave", () => updateLinks(explorer.dataset.activeNode, null));
  });

  if (resetButton) resetButton.addEventListener("click", () => activate("fact-order", true));
  activate("fact-order", false);
})();
