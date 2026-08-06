(function () {
  const DATA_PATH = "../assets/data/global-superstore.json";
  const currency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
  const number = new Intl.NumberFormat("en-US");
  const compactCurrency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  });

  const themeColor = (token) => getComputedStyle(document.documentElement).getPropertyValue(token).trim();
  const elements = {
    select: document.querySelector("#year-filter"),
    loading: document.querySelector("#dashboard-loading"),
    error: document.querySelector("#dashboard-error"),
    content: document.querySelector("#dashboard-content"),
    status: document.querySelector("#status-message"),
    sales: document.querySelector("#metric-sales"),
    lines: document.querySelector("#metric-lines"),
    profit: document.querySelector("#metric-profit"),
    margin: document.querySelector("#metric-margin"),
    orders: document.querySelector("#metric-orders"),
    customers: document.querySelector("#metric-customers"),
    countries: document.querySelector("#metric-countries"),
    trend: document.querySelector("#trend-chart"),
    categories: document.querySelector("#category-chart"),
    markets: document.querySelector("#market-rows"),
    shipping: document.querySelector("#shipping-rows"),
    country: document.querySelector("#country-rows"),
  };
  let payload;
  let selectedScope = "all";

  function money(value) {
    return currency.format(value);
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

    const labelIndexes = data.length > 12 ? [0, Math.floor(data.length / 2), data.length - 1] : data.map((_, index) => index);
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

  function setRows(target, html) {
    target.innerHTML = html;
  }

  function renderTables(data) {
    setRows(
      elements.markets,
      data.markets
        .map((item) => `<tr><td>${item.market}</td><td>${money(item.sales)}</td><td class="${item.profit < 0 ? "profit-negative" : ""}">${money(item.profit)}</td></tr>`)
        .join("")
    );
    setRows(
      elements.shipping,
      data.shipping
        .map((item) => `<tr><td>${item.ship_mode}</td><td>${number.format(item.orders)}</td><td>${item.avg_ship_days.toFixed(1)}</td></tr>`)
        .join("")
    );
    setRows(
      elements.country,
      data.countries
        .map((item) => `<tr><td>${item.country}</td><td>${number.format(item.orders)}</td><td>${money(item.sales)}</td><td class="${item.profit < 0 ? "profit-negative" : ""}">${money(item.profit)}</td></tr>`)
        .join("")
    );
  }

  function activeData() {
    return selectedScope === "all" ? payload.dashboard.all : payload.dashboard.years[selectedScope];
  }

  function render() {
    const data = activeData();
    const summary = data.summary;
    elements.sales.textContent = money(summary.sales);
    elements.lines.textContent = `${number.format(summary.line_items)} line items`;
    elements.profit.textContent = money(summary.profit);
    elements.margin.textContent = `${summary.profit_margin.toFixed(1)}% profit margin`;
    elements.orders.textContent = number.format(summary.orders);
    elements.customers.textContent = `${number.format(summary.customers)} khách hàng`;
    elements.countries.textContent = number.format(summary.countries);
    elements.status.textContent = selectedScope === "all" ? `Toàn bộ giai đoạn ${payload.project.period}` : `Năm ${selectedScope}`;
    drawTrend(data.monthly);
    drawCategories(data.categories);
    renderTables(data);
  }

  function initialize(data) {
    payload = data;
    elements.select.innerHTML = [
      '<option value="all">Tất cả năm</option>',
      ...payload.filters.years.map((year) => `<option value="${year}">${year}</option>`),
    ].join("");
    elements.select.disabled = false;
    elements.select.addEventListener("change", () => {
      selectedScope = elements.select.value;
      render();
    });
    window.addEventListener("resize", () => requestAnimationFrame(render));
    elements.loading.hidden = true;
    elements.content.hidden = false;
    render();
  }

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
