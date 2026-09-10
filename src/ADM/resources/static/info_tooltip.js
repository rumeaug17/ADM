/**
 * Infobulle contextuelle pour les icônes ".info-icon" (aide en ligne des
 * questions et des champs de formulaire), sans dépendance à jQuery.
 *
 * Utilisation : ADM.initInfoTooltips("/static/info_texts.json");
 */
window.ADM = window.ADM || {};

ADM.initInfoTooltips = function initInfoTooltips(infoTextsUrl) {
  "use strict";

  var infoTexts = {};

  fetch(infoTextsUrl)
    .then(function (response) {
      return response.json();
    })
    .then(function (data) {
      infoTexts = data;
      // Certains textes sont fournis sous forme de tableau de lignes.
      Object.keys(infoTexts).forEach(function (key) {
        if (Array.isArray(infoTexts[key])) {
          infoTexts[key] = infoTexts[key].join("");
        }
      });
    })
    .catch(function () {
      // Les infobulles resteront indisponibles ; l'icône affichera le
      // message par défaut défini plus bas.
    });

  function removeTooltip() {
    var existing = document.querySelector(".info-tooltip");
    if (existing) {
      existing.remove();
    }
  }

  document.addEventListener("click", function (event) {
    var icon = event.target.closest(".info-icon");
    if (icon) {
      event.stopPropagation();
      removeTooltip();

      var key = icon.getAttribute("data-key");
      var infoText = infoTexts[key] || "Information non disponible.";

      var tooltip = document.createElement("div");
      tooltip.className = "info-tooltip";
      tooltip.innerHTML = infoText;
      document.body.appendChild(tooltip);

      var iconRect = icon.getBoundingClientRect();
      tooltip.style.position = "absolute";
      tooltip.style.top = window.scrollY + iconRect.bottom + 8 + "px";
      tooltip.style.left = window.scrollX + iconRect.left + "px";
      tooltip.style.display = "block";
      return;
    }

    // Un clic à l'intérieur de l'infobulle ne doit pas la fermer.
    if (event.target.closest(".info-tooltip")) {
      event.stopPropagation();
      return;
    }

    removeTooltip();
  });
};
