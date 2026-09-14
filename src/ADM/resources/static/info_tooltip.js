/**
 * Aide contextuelle des icônes ".info-icon" (aide en ligne des questions et
 * des champs de formulaire).
 *
 * Tâche 4.5 du backlog : ce composant s'appuie sur le popover Bootstrap
 * natif (déjà utilisé par ailleurs dans l'application via
 * data-bs-toggle="tooltip", cf. base.html) plutôt que sur une infobulle
 * maison positionnée en absolu avec une largeur fixée en dur, différente
 * selon la page. Le popover Bootstrap est accessible au clavier (il
 * s'affiche aussi au focus, pas seulement au clic) et responsive (largeur
 * plafonnée par la règle CSS ".popover" de base.html, positionnement
 * automatique géré par Popper pour rester dans la fenêtre visible).
 *
 * Utilisation : ADM.initInfoTooltips("/static/info_texts.json").
 */
window.ADM = window.ADM || {};

ADM.initInfoTooltips = function initInfoTooltips(infoTextsUrl) {
  "use strict";

  function resolveText(value) {
    // Certains textes sont fournis sous forme de tableau de lignes HTML.
    return Array.isArray(value) ? value.join("") : value;
  }

  fetch(infoTextsUrl)
    .then(function (response) {
      return response.json();
    })
    .then(function (infoTexts) {
      var icons = document.querySelectorAll(".info-icon[data-key]");
      icons.forEach(function (icon) {
        var key = icon.getAttribute("data-key");
        var content = resolveText(infoTexts[key]) || "Information non disponible.";
        new bootstrap.Popover(icon, {
          content: content,
          html: true,
          trigger: "focus click",
          placement: "auto",
        });
      });
    })
    .catch(function () {
      // Les infobulles resteront indisponibles ; les icônes restent
      // affichées mais n'ouvrent pas de popover.
    });
};
