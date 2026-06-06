(function () {
  function toggleForm(id, show) {
    const form = document.getElementById(id);
    if (!form) return;
    form.classList.toggle("hidden", !show);
  }

  document.querySelectorAll(".js-edit-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-target");
      if (target) toggleForm(target, true);
    });
  });

  document.querySelectorAll(".js-edit-cancel").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-target");
      if (target) toggleForm(target, false);
    });
  });
})();
