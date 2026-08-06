(function () {
  const button = document.querySelector("[data-menu-button]");
  const menu = document.querySelector("[data-menu]");

  if (!button || !menu) return;

  button.addEventListener("click", () => {
    const isOpen = menu.getAttribute("data-open") === "true";
    menu.setAttribute("data-open", String(!isOpen));
    button.setAttribute("aria-expanded", String(!isOpen));
  });
})();
