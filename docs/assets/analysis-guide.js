(function () {
  const STORAGE_KEY = "data-workbench:global-superstore:progress";
  const STAGES = [
    { id: "overview", title: "Business framing" },
    { id: "structure", title: "Data architecture" },
    { id: "query", title: "Analytical SQL" },
    { id: "eda", title: "EDA & evidence" },
    { id: "dashboard", title: "Decision dashboard" },
  ];

  const stageIds = new Set(STAGES.map((stage) => stage.id));
  const stageSections = Array.from(document.querySelectorAll("[data-stage]"));
  const navItems = Array.from(document.querySelectorAll("[data-stage-target]"));
  const progress = document.querySelector("[data-progress]");
  const progressLabel = document.querySelector("[data-progress-label]");
  const stagePosition = document.querySelector("[data-stage-position]");
  const stageTitle = document.querySelector("[data-stage-title]");
  const saveState = document.querySelector("[data-save-state]");
  const previousButton = document.querySelector("[data-prev-stage]");
  const nextButton = document.querySelector("[data-next-stage]");
  const completeButton = document.querySelector("[data-toggle-complete]");
  const resetButton = document.querySelector("[data-reset-progress]");
  const sidebarButton = document.querySelector("[data-sidebar-toggle]");
  const toast = document.querySelector("[data-copy-toast]");

  if (!stageSections.length || !navItems.length) return;

  function readState() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      const completed = Array.isArray(saved?.completed)
        ? saved.completed.filter((id) => stageIds.has(id))
        : [];
      return {
        activeStage: stageIds.has(saved?.activeStage) ? saved.activeStage : "overview",
        completed: new Set(completed),
        sidebarCollapsed: Boolean(saved?.sidebarCollapsed),
      };
    } catch (error) {
      return { activeStage: "overview", completed: new Set(), sidebarCollapsed: false };
    }
  }

  const state = readState();
  const hashStage = window.location.hash.replace("#", "");
  if (stageIds.has(hashStage)) state.activeStage = hashStage;

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        activeStage: state.activeStage,
        completed: Array.from(state.completed),
        sidebarCollapsed: state.sidebarCollapsed,
      })
    );
  }

  function renderProgress() {
    const completedCount = state.completed.size;
    progress.value = completedCount;
    progressLabel.textContent = `${completedCount}/${STAGES.length} chặng`;
    navItems.forEach((item) => {
      item.dataset.completed = String(state.completed.has(item.dataset.stageTarget));
    });
  }

  function renderSidebar() {
    document.body.dataset.sidebarCollapsed = String(state.sidebarCollapsed);
    if (sidebarButton) {
      const label = state.sidebarCollapsed ? "Mở rộng thanh điều hướng" : "Thu gọn thanh điều hướng";
      sidebarButton.setAttribute("aria-label", label);
      const copy = sidebarButton.querySelector(".nav-copy");
      if (copy) copy.textContent = state.sidebarCollapsed ? "Mở rộng" : "Thu gọn";
    }
  }

  function renderStage(stageId, updateUrl) {
    if (!stageIds.has(stageId)) return;
    state.activeStage = stageId;
    const activeIndex = STAGES.findIndex((stage) => stage.id === stageId);

    stageSections.forEach((section) => {
      section.hidden = section.dataset.stage !== stageId;
    });
    navItems.forEach((item) => {
      if (item.dataset.stageTarget === stageId) item.setAttribute("aria-current", "step");
      else item.removeAttribute("aria-current");
    });

    stagePosition.textContent = `Chặng ${activeIndex + 1}/${STAGES.length}`;
    stageTitle.textContent = STAGES[activeIndex].title;
    previousButton.disabled = activeIndex === 0;
    nextButton.textContent = activeIndex === STAGES.length - 1 ? "Hoàn tất project" : "Tiếp tục";

    const isCompleted = state.completed.has(stageId);
    completeButton.dataset.completed = String(isCompleted);
    completeButton.textContent = isCompleted ? "Đã hoàn thành" : "Đánh dấu hoàn thành";
    saveState.textContent = state.completed.size === STAGES.length
      ? "Project đã hoàn thành"
      : "Tiến độ lưu trên trình duyệt";

    if (updateUrl) history.replaceState(null, "", `#${stageId}`);
    persist();
    window.scrollTo({ top: 0, behavior: "auto" });
    window.dispatchEvent(new CustomEvent("analysis:stagechange", { detail: { stage: stageId } }));
  }

  function markComplete(stageId, completed) {
    if (completed) state.completed.add(stageId);
    else state.completed.delete(stageId);
    renderProgress();
    renderStage(stageId, false);
  }

  navItems.forEach((item) => {
    item.addEventListener("click", () => renderStage(item.dataset.stageTarget, true));
  });

  previousButton.addEventListener("click", () => {
    const index = STAGES.findIndex((stage) => stage.id === state.activeStage);
    if (index > 0) renderStage(STAGES[index - 1].id, true);
  });

  nextButton.addEventListener("click", () => {
    const index = STAGES.findIndex((stage) => stage.id === state.activeStage);
    markComplete(state.activeStage, true);
    if (index < STAGES.length - 1) renderStage(STAGES[index + 1].id, true);
  });

  completeButton.addEventListener("click", () => {
    markComplete(state.activeStage, !state.completed.has(state.activeStage));
  });

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      if (!window.confirm("Đặt lại toàn bộ tiến độ của project này?")) return;
      state.completed.clear();
      renderProgress();
      renderStage("overview", true);
    });
  }

  if (sidebarButton) {
    sidebarButton.addEventListener("click", () => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
      renderSidebar();
      persist();
    });
  }

  let toastTimer;
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(() => {
      toast.hidden = true;
    }, 1600);
  }

  async function copyText(text, button) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        const input = document.createElement("textarea");
        input.value = text;
        input.setAttribute("readonly", "");
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        input.remove();
      }
      const original = button.textContent;
      button.textContent = "Đã sao chép";
      showToast("Đã sao chép vào clipboard");
      window.setTimeout(() => {
        button.textContent = original;
      }, 1400);
    } catch (error) {
      showToast("Không thể sao chép tự động");
    }
  }

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-target], [data-copy-text]");
    if (!button) return;
    const target = button.dataset.copyTarget
      ? document.getElementById(button.dataset.copyTarget)
      : null;
    const text = target ? target.textContent : button.dataset.copyText;
    if (text) copyText(text.trim(), button);
  });

  window.addEventListener("hashchange", () => {
    const requestedStage = window.location.hash.replace("#", "");
    if (stageIds.has(requestedStage)) renderStage(requestedStage, false);
  });

  renderSidebar();
  renderProgress();
  renderStage(state.activeStage, !window.location.hash);
})();
