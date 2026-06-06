(function () {
  "use strict";

  var overview = document.querySelector(".sc-overview-grid");
  if (!overview) return;

  overview.setAttribute("role", "region");
  overview.setAttribute("aria-label", "Safety overview statistics");

  document.querySelectorAll(".sc-table-wrap table").forEach(function (table) {
    table.setAttribute("role", "table");
  });

  document.querySelectorAll(".sc-notification-list").forEach(function (list) {
    list.setAttribute("role", "list");
  });
})();
