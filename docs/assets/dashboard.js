(function () {
  const DATA_PATH = "../assets/data/global-superstore.json";
  const currency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
  const number = new Intl.NumberFormat("vi-VN");
  const decimal = new Intl.NumberFormat("vi-VN", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  const compactCurrency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  });

  const themeColor = (token) => getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  const byId = (id) => document.getElementById(id);
  const elements = {
    select: byId("year-filter"),
    loading: byId("dashboard-loading"),
    error: byId("dashboard-error"),
    content: byId("dashboard-content"),
    status: byId("status-message"),
    sales: byId("metric-sales"),
    lines: byId("metric-lines"),
    profit: byId("metric-profit"),
    profitGrowth: byId("metric-profit-growth"),
    margin: byId("metric-margin-value"),
    salesGrowth: byId("metric-sales-growth"),
    growthContext: byId("metric-growth-context"),
    averageOrderValue: byId("metric-aov"),
    shippingRatio: byId("metric-shipping-ratio"),
    orders: byId("metric-orders"),
    customers: byId("metric-customers-value"),
    salesPerCustomer: byId("metric-sales-customer"),
    repeatRate: byId("metric-repeat-rate"),
    concentration: byId("metric-concentration"),
    countries: byId("metric-countries"),
    averageDiscount: byId("metric-average-discount"),
    lossLines: byId("metric-loss-lines"),
    lossProducts: byId("metric-loss-products"),
    profitPerOrder: byId("metric-profit-order"),
    trend: byId("trend-chart"),
    categories: byId("category-chart"),
    markets: byId("market-rows"),
    shipping: byId("shipping-rows"),
    country: byId("country-rows"),
    segments: byId("segment-rows"),
    discounts: byId("discount-rows"),
    lossProductRows: byId("loss-product-rows"),
    overviewLines: byId("overview-lines"),
    overviewOrders: byId("overview-orders"),
    overviewCustomers: byId("overview-customers"),
    overviewCountries: byId("overview-countries"),
    modelOrderRows: byId("model-order-rows"),
    modelLineRows: byId("model-line-rows"),
    qualityPrimary: byId("quality-primary"),
    qualityForeign: byId("quality-foreign"),
    qualityDomain: byId("quality-domain"),
    qualityTemporal: byId("quality-temporal"),
    edaGrowth: byId("eda-yoy-growth"),
    edaCagr: byId("eda-cagr"),
    edaTopMarket: byId("eda-top-market"),
    edaMarketShare: byId("eda-market-share"),
    edaTopCategory: byId("eda-top-category"),
    edaCategoryMargin: byId("eda-category-margin"),
    edaDiscountRisk: byId("eda-discount-risk"),
    edaLossProducts: byId("eda-loss-products"),
    edaLossProductShare: byId("eda-loss-product-share"),
    edaCustomerConcentration: byId("eda-customer-concentration"),
    edaShippingRatio: byId("eda-shipping-ratio"),
    evidenceGrowth: byId("evidence-growth-measure"),
    evidenceDiscount: byId("evidence-discount-measure"),
    evidenceLoss: byId("evidence-loss-measure"),
    evidenceConcentration: byId("evidence-concentration-measure"),
    evidenceShipping: byId("evidence-shipping-measure"),
  };
  const dashboardTabs = Array.from(document.querySelectorAll("[data-dashboard-tab-target]"));
  const dashboardPanels = Array.from(document.querySelectorAll("[data-dashboard-panel]"));

  let payload;
  let selectedScope = "all";
  let activeDashboardTab = "executive";
  let resizeFrame;

  function money(value) {
    return currency.format(value);
  }

  function percent(value) {
    return `${decimal.format(value)}%`;
  }

  function signedPercent(value) {
    if (value === null || Number.isNaN(value)) return "N/A";
    return `${value > 0 ? "+" : ""}${decimal.format(value)}%`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function canvasContext(canvas) {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const { width, height } = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(width * ratio));
    canvas.height = Math.max(1, Math.floor(height * ratio));
    const context = canvas.getContext("2d");
    context.scale(ratio, ratio);
    return { context, width, height };
  }

  function drawEmpty(canvas, message) {
    const { context, width, height } = canvasContext(canvas);
    context.fillStyle = themeColor("--ink-muted");
    context.font = "14px system-ui";
    context.textAlign = "center";
    context.fillText(message, width / 2, height / 2);
  }

  function drawTrend(data) {
    if (!data.length) return drawEmpty(elements.trend, "Không có dữ liệu trong phạm vi này");
    const { context, width, height } = canvasContext(elements.trend);
    const pad = { top: 16, right: 14, bottom: 32, left: 56 };
    const chartWidth = width - pad.left - pad.right;
    const chartHeight = height - pad.top - pad.bottom;
    const max = Math.max(...data.flatMap((item) => [item.sales, item.profit]), 1) * 1.08;
    const gridColor = themeColor("--line");
    const muted = themeColor("--ink-muted");
    const accent = themeColor("--accent");

    context.clearRect(0, 0, width, height);
    context.strokeStyle = gridColor;
    context.fillStyle = muted;
    context.font = "11px system-ui";
    context.textAlign = "right";
    for (let step = 0; step <= 4; step += 1) {
      const y = pad.top + (chartHeight / 4) * step;
      context.beginPath();
      context.moveTo(pad.left, y);
      context.lineTo(width - pad.right, y);
      context.stroke();
      context.fillText(compactCurrency.format(max - (max / 4) * step), pad.left - 8, y + 4);
    }

    const x = (index) => pad.left + (data.length === 1 ? chartWidth / 2 : (chartWidth * index) / (data.length - 1));
    const y = (value) => pad.top + chartHeight - (value / max) * chartHeight;
    const plotLine = (key, color) => {
      context.beginPath();
      data.forEach((item, index) => {
        if (index === 0) context.moveTo(x(index), y(item[key]));
        else context.lineTo(x(index), y(item[key]));
      });
      context.strokeStyle = color;
      context.lineWidth = 2.4;
      context.stroke();
      data.forEach((item, index) => {
        context.beginPath();
        context.fillStyle = color;
        context.arc(x(index), y(item[key]), 2.7, 0, Math.PI * 2);
        context.fill();
      });
    };
    plotLine("sales", accent);
    plotLine("profit", muted);

    const labelIndexes = data.length > 12
      ? [0, Math.floor(data.length / 2), data.length - 1]
      : data.map((_, index) => index);
    context.fillStyle = muted;
    context.textAlign = "center";
    labelIndexes.forEach((index) => {
      const [year, month] = data[index].year_month.split("-");
      context.fillText(`T${Number(month)}/${year.slice(2)}`, x(index), height - 10);
    });
  }

  function drawCategories(data) {
    if (!data.length) return drawEmpty(elements.categories, "Không có dữ liệu trong phạm vi này");
    const { context, width, height } = canvasContext(elements.categories);
    const pad = { top: 20, right: 20, bottom: 12, left: 96 };
    const chartWidth = width - pad.left - pad.right;
    const chartHeight = height - pad.top - pad.bottom;
    const max = Math.max(...data.map((item) => item.sales), 1);
    const rowHeight = chartHeight / data.length;
    const accent = themeColor("--accent");
    const muted = themeColor("--ink-muted");
    const soft = themeColor("--surface-muted");
    context.clearRect(0, 0, width, height);
    context.font = "12px system-ui";
    data.forEach((item, index) => {
      const y = pad.top + index * rowHeight + rowHeight * 0.25;
      const barHeight = Math.min(34, rowHeight * 0.47);
      context.fillStyle = muted;
      context.textAlign = "right";
      context.fillText(item.category, pad.left - 10, y + barHeight * 0.72);
      context.fillStyle = soft;
      context.fillRect(pad.left, y, chartWidth, barHeight);
      context.fillStyle = accent;
      context.fillRect(pad.left, y, (item.sales / max) * chartWidth, barHeight);
      context.fillStyle = muted;
      context.textAlign = "right";
      context.fillText(compactCurrency.format(item.sales), width - pad.right, y + barHeight * 0.72);
    });
  }

  function stageIsVisible() {
    const stage = document.querySelector('[data-stage="dashboard"]');
    return Boolean(stage && !stage.hidden);
  }

  function chartsAreVisible() {
    return stageIsVisible()
      && activeDashboardTab === "executive"
      && elements.trend.getBoundingClientRect().width > 10;
  }

  function setRows(target, html) {
    if (target) target.innerHTML = html;
  }

  function renderTables(data) {
    setRows(
      elements.markets,
      data.markets.map((item) => `
        <tr>
          <td>${escapeHtml(item.market)}</td>
          <td>${number.format(item.orders)}</td>
          <td>${money(item.sales)}</td>
          <td class="${item.profit < 0 ? "profit-negative" : ""}">${money(item.profit)}</td>
          <td>${percent(item.profit_margin)}</td>
        </tr>`).join("")
    );
    setRows(
      elements.shipping,
      data.shipping.map((item) => `
        <tr>
          <td>${escapeHtml(item.ship_mode)}</td>
          <td>${number.format(item.orders)}</td>
          <td>${decimal.format(item.avg_ship_days)}</td>
          <td>${money(item.sales)}</td>
          <td>${money(item.shipping_cost)}</td>
          <td>${percent(item.shipping_cost_ratio)}</td>
        </tr>`).join("")
    );
    setRows(
      elements.country,
      data.countries.map((item) => `
        <tr>
          <td>${escapeHtml(item.country)}</td>
          <td>${number.format(item.orders)}</td>
          <td>${money(item.sales)}</td>
          <td class="${item.profit < 0 ? "profit-negative" : ""}">${money(item.profit)}</td>
          <td>${percent(item.profit_margin)}</td>
        </tr>`).join("")
    );
    setRows(
      elements.segments,
      data.segments.map((item) => `
        <tr>
          <td>${escapeHtml(item.segment)}</td>
          <td>${number.format(item.customers)}</td>
          <td>${number.format(item.orders)}</td>
          <td>${money(item.sales)}</td>
          <td>${percent(item.profit_margin)}</td>
          <td>${money(item.average_order_value)}</td>
        </tr>`).join("")
    );
    setRows(
      elements.discounts,
      data.discount_bands.map((item) => `
        <tr>
          <td>${escapeHtml(item.discount_band)}</td>
          <td>${number.format(item.line_items)}</td>
          <td>${money(item.sales)}</td>
          <td class="${item.profit < 0 ? "profit-negative" : ""}">${money(item.profit)}</td>
          <td class="${item.profit_margin < 0 ? "profit-negative" : ""}">${percent(item.profit_margin)}</td>
        </tr>`).join("")
    );
    setRows(
      elements.lossProductRows,
      data.loss_products.map((item) => `
        <tr>
          <td class="truncate-cell" title="${escapeHtml(item.product_name)}">${escapeHtml(item.product_name)}</td>
          <td>${escapeHtml(item.category)}</td>
          <td>${money(item.sales)}</td>
          <td class="profit-negative">${money(item.profit)}</td>
        </tr>`).join("")
    );
  }

  function comparisonForScope() {
    const years = payload.filters.years;
    const currentYear = selectedScope === "all" ? payload.analysis.latest_year : Number(selectedScope);
    const currentIndex = years.indexOf(currentYear);
    if (currentIndex <= 0) {
      return { salesGrowth: null, profitGrowth: null, label: "Không có năm so sánh" };
    }
    const previousYear = years[currentIndex - 1];
    const current = payload.dashboard.years[String(currentYear)].summary;
    const previous = payload.dashboard.years[String(previousYear)].summary;
    return {
      salesGrowth: (current.sales / previous.sales - 1) * 100,
      profitGrowth: (current.profit / previous.profit - 1) * 100,
      label: `${currentYear} so với ${previousYear}`,
    };
  }

  function renderGuide(data) {
    const summary = data.dashboard.all.summary;
    elements.overviewLines.textContent = number.format(summary.line_items);
    elements.overviewOrders.textContent = number.format(summary.orders);
    elements.overviewCustomers.textContent = number.format(summary.customers);
    elements.overviewCountries.textContent = number.format(summary.countries);
    elements.modelOrderRows.textContent = number.format(summary.orders);
    elements.modelLineRows.textContent = number.format(summary.line_items);

    const quality = data.model.quality;
    const allPrimaryKeysValid = quality.dimension_primary_keys_unique
      && quality.order_primary_key_unique
      && quality.line_primary_key_unique;
    elements.qualityPrimary.textContent = allPrimaryKeysValid
      ? "8 dataset primary keys duy nhất"
      : "Primary key contract không đạt";
    const orphanKeys = Object.entries(quality)
      .filter(([key]) => key.startsWith("orphan_"))
      .reduce((total, [, value]) => total + value, 0);
    elements.qualityForeign.textContent = orphanKeys === 0
      ? "0 orphan key trên 8 quan hệ"
      : `${number.format(orphanKeys)} orphan key cần xử lý`;
    const domainErrors = quality.null_measure_rows
      + quality.invalid_quantity_rows
      + quality.negative_sales_rows
      + quality.negative_shipping_cost_rows
      + quality.invalid_discount_rows;
    elements.qualityDomain.textContent = domainErrors === 0
      ? "0 vi phạm measure domain"
      : `${number.format(domainErrors)} vi phạm domain rule`;
    elements.qualityTemporal.textContent = quality.ship_before_order_rows === 0
      ? "0 ship date trước order date"
      : `${number.format(quality.ship_before_order_rows)} temporal error`;

    const allData = data.dashboard.all;
    elements.edaGrowth.textContent = signedPercent(data.analysis.sales_growth_pct);
    elements.edaCagr.textContent = signedPercent(data.analysis.sales_cagr_pct);
    const topMarket = allData.markets[0];
    elements.edaTopMarket.textContent = topMarket.market;
    elements.edaMarketShare.textContent = `${percent(topMarket.sales / summary.sales * 100)} tổng sales.`;
    const topCategory = allData.categories[0];
    elements.edaTopCategory.textContent = topCategory.category;
    elements.edaCategoryMargin.textContent = `${percent(topCategory.profit_margin)} profit margin.`;
    const highDiscount = allData.discount_bands.find((item) => item.discount_band.startsWith("Trên"));
    elements.edaDiscountRisk.textContent = percent(highDiscount.profit_margin);
    elements.edaLossProducts.textContent = number.format(summary.loss_making_products);
    elements.edaLossProductShare.textContent = `${percent(summary.loss_making_product_share)} product member.`;
    elements.edaCustomerConcentration.textContent = percent(summary.top_20_customer_sales_share);
    elements.edaShippingRatio.textContent = percent(summary.shipping_cost_ratio);
    elements.evidenceGrowth.textContent = `Sales ${signedPercent(data.analysis.sales_growth_pct)}; profit ${signedPercent(data.analysis.profit_growth_pct)}; gap ${decimal.format(data.analysis.revenue_profit_gap_pct)} điểm %`;
    elements.evidenceDiscount.textContent = `Band trên 30% có margin ${percent(highDiscount.profit_margin)}`;
    elements.evidenceLoss.textContent = `${percent(summary.loss_making_product_share)} product member có total profit âm`;
    elements.evidenceConcentration.textContent = `Top 20% customer tạo ${percent(summary.top_20_customer_sales_share)} sales`;
    elements.evidenceShipping.textContent = `Shipping cost ratio ${percent(summary.shipping_cost_ratio)}`;
  }

  function activeData() {
    return selectedScope === "all" ? payload.dashboard.all : payload.dashboard.years[selectedScope];
  }

  function renderMetrics(data) {
    const summary = data.summary;
    const comparison = comparisonForScope();
    elements.sales.textContent = money(summary.sales);
    elements.lines.textContent = `${number.format(summary.line_items)} dòng giao dịch`;
    elements.profit.textContent = money(summary.profit);
    elements.profitGrowth.textContent = comparison.profitGrowth === null
      ? comparison.label
      : `${signedPercent(comparison.profitGrowth)} YoY`;
    elements.margin.textContent = percent(summary.profit_margin);
    elements.salesGrowth.textContent = signedPercent(comparison.salesGrowth);
    elements.growthContext.textContent = comparison.label;
    elements.averageOrderValue.textContent = money(summary.average_order_value);
    elements.shippingRatio.textContent = percent(summary.shipping_cost_ratio);
    elements.orders.textContent = number.format(summary.orders);
    elements.customers.textContent = number.format(summary.customers);
    elements.salesPerCustomer.textContent = money(summary.sales_per_customer);
    elements.repeatRate.textContent = percent(summary.repeat_customer_rate);
    elements.concentration.textContent = percent(summary.top_20_customer_sales_share);
    elements.countries.textContent = number.format(summary.countries);
    elements.averageDiscount.textContent = percent(summary.average_discount);
    elements.lossLines.textContent = percent(summary.loss_making_line_share);
    elements.lossProducts.textContent = `${number.format(summary.loss_making_products)} (${percent(summary.loss_making_product_share)})`;
    elements.profitPerOrder.textContent = money(summary.profit_per_order);
  }

  function render() {
    const data = activeData();
    renderMetrics(data);
    renderTables(data);
    elements.status.textContent = selectedScope === "all"
      ? `Full snapshot ${payload.project.period} | growth signal ${payload.analysis.latest_year} vs ${payload.analysis.comparison_year}`
      : `Calendar year ${selectedScope}`;
    if (chartsAreVisible()) {
      drawTrend(data.monthly);
      drawCategories(data.categories);
    }
  }

  function activateDashboardTab(tabId, focusTab) {
    activeDashboardTab = tabId;
    dashboardTabs.forEach((tab) => {
      const active = tab.dataset.dashboardTabTarget === tabId;
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active && focusTab) tab.focus();
    });
    dashboardPanels.forEach((panel) => {
      panel.hidden = panel.dataset.dashboardPanel !== tabId;
    });
    if (payload) window.requestAnimationFrame(render);
  }

  dashboardTabs.forEach((tab, index) => {
    tab.addEventListener("click", () => activateDashboardTab(tab.dataset.dashboardTabTarget, false));
    tab.addEventListener("keydown", (event) => {
      if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault();
      const direction = event.key === "ArrowRight" ? 1 : -1;
      const nextIndex = (index + direction + dashboardTabs.length) % dashboardTabs.length;
      activateDashboardTab(dashboardTabs[nextIndex].dataset.dashboardTabTarget, true);
    });
  });

  function initialize(data) {
    payload = data;
    renderGuide(data);
    elements.select.innerHTML = [
      '<option value="all">Toàn bộ snapshot</option>',
      ...payload.filters.years.map((year) => `<option value="${year}">${year}</option>`),
    ].join("");
    elements.select.disabled = false;
    elements.select.addEventListener("change", () => {
      selectedScope = elements.select.value;
      render();
    });
    window.addEventListener("resize", () => {
      window.cancelAnimationFrame(resizeFrame);
      resizeFrame = window.requestAnimationFrame(render);
    });
    elements.loading.hidden = true;
    elements.content.hidden = false;
    activateDashboardTab("executive", false);
    render();
  }

  window.addEventListener("analysis:stagechange", (event) => {
    if (event.detail?.stage === "dashboard" && payload) {
      window.requestAnimationFrame(render);
    }
  });

  fetch(DATA_PATH)
    .then((response) => {
      if (!response.ok) throw new Error(`Dashboard asset returned ${response.status}`);
      return response.json();
    })
    .then(initialize)
    .catch((error) => {
      console.error(error);
      elements.loading.hidden = true;
      elements.error.hidden = false;
      elements.status.textContent = "Lỗi tải dữ liệu";
    });
})();
