/**
 * Graphique radar interactif (Chart.js), Phase 6 (US4.1) du plan de
 * modernisation de l'interface (voir docs/UI_MODERNIZATION_PROPOSAL.md).
 *
 * Avant cette phase, le radar (scores moyens par dimension DICP) n'existait
 * qu'en image PNG statique générée côté serveur par matplotlib
 * (`ADM.services.generate_radar_chart`) : pas de survol pour lire une valeur
 * exacte, pas de zoom. Chart.js (vendorisé dans
 * `static/vendor/chartjs/chart.umd.min.js`, pas de CDN, dans le même esprit
 * que Bootstrap/htmx/Alpine.js) affiche la même donnée de façon interactive
 * (tooltip au survol d'un axe), sans rien changer côté serveur au calcul des
 * scores lui-même (`ADM.services.axis_scores`) : seule sa mise en forme
 * change (`ADM.services.radar_chart_data`, qui produit exactement les mêmes
 * catégories/scores/échelle que le PNG, pour que les deux représentations
 * restent cohérentes entre elles).
 *
 * Le PNG matplotlib n'est pas supprimé : il reste généré et servi tel quel
 * (route `/radar/<name>` inchangée, testée par
 * `tests/test_routes_applications.py`) et sert de repli `<noscript>` sur les
 * pages qui affichent un radar au chargement (résumé d'application, radar
 * moyen de la synthèse) — voir `resume.html`/`synthese.html`.
 */

// Couleur de marque (voir app.css, section 5/9 du plan : vert forêt validé en
// Phase 0). Reprise ici en dur plutôt que lue depuis une variable CSS
// calculée : Chart.js construit son dégradé de remplissage en JavaScript, et
// une constante partagée avec la valeur déjà choisie ailleurs est plus
// simple et plus robuste qu'un accès au DOM stylé à ce stade.
var ADM_RADAR_COLOR = "#0e6b5c";
var ADM_RADAR_FILL_COLOR = "rgba(14, 107, 92, 0.25)"; // même opacité que le PNG matplotlib (alpha=0.25)

/**
 * Construit la configuration Chart.js d'un radar à partir des données
 * produites par `ADM.services.radar_chart_data` (``{labels, scores, max}``).
 */
function admRadarChartConfig(radarData) {
  return {
    type: "radar",
    data: {
      labels: radarData.labels,
      datasets: [
        {
          data: radarData.scores,
          backgroundColor: ADM_RADAR_FILL_COLOR,
          borderColor: ADM_RADAR_COLOR,
          borderWidth: 2,
          pointBackgroundColor: ADM_RADAR_COLOR,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      // Correctif (US4.1, post-Phase 6) : carré explicite plutôt que de
      // dépendre du ratio par défaut de Chart.js pour le type "radar" —
      // combiné à `.radar-chart-wrapper` (voir app.css), qui plafonne la
      // largeur disponible, ce carré évite qu'un radar placé dans une carte
      // pleine largeur (resume.html) s'affiche démesurément plus grand que
      // le PNG qu'il remplace.
      aspectRatio: 1,
      // Correctif (US4.1, post-Phase 6) : sans ceci, Chart.js anime le
      // remplacement du PNG par le graphique interactif (l'échelle radiale
      // grandit progressivement depuis le centre, ~1 seconde par défaut) —
      // visuellement perçu comme une seconde image qui se superpose à la
      // première avec un effet de zoom, plutôt qu'un simple remplacement.
      // Désactiver l'animation rend ce remplacement instantané, une seule
      // couche visible à la fois, comme avec le PNG qu'il remplace.
      animation: false,
      scales: {
        r: {
          beginAtZero: true,
          min: 0,
          max: radarData.max,
          ticks: { stepSize: 1 },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
  };
}

/**
 * Crée (et retourne) un graphique radar Chart.js sur le <canvas> donné, ou
 * ``null`` en cas d'échec (Chart.js non chargé, donnée invalide, etc.) :
 * jamais d'exception remontée à l'appelant, pour que le repli PNG (voir
 * ``admShowRadarChart`` ci-dessous) puisse toujours s'appliquer proprement.
 */
function admRenderRadarChart(canvas, radarData) {
  try {
    return new Chart(canvas, admRadarChartConfig(radarData));
  } catch (e) {
    return null;
  }
}

/**
 * Variante pour les pages qui intègrent déjà leurs données radar au rendu
 * serveur (résumé d'application, synthèse) : lit le JSON déposé dans un
 * <script type="application/json"> voisin plutôt que d'aller le chercher en
 * réseau, puisque la page qui l'affiche l'a déjà calculé pour son propre
 * rendu (voir `ADM.routes.resume`/`ADM.routes.synthese`).
 */
function admRenderRadarChartFromElement(canvasId, dataElementId) {
  var canvas = document.getElementById(canvasId);
  var dataEl = document.getElementById(dataElementId);
  if (!canvas || !dataEl) {
    return null;
  }
  var radarData;
  try {
    radarData = JSON.parse(dataEl.textContent);
  } catch (e) {
    return null;
  }
  return admRenderRadarChart(canvas, radarData);
}

/**
 * Bascule l'affichage d'un radar du PNG (repli, affiché par défaut dans le
 * gabarit) vers le graphique interactif Chart.js une fois celui-ci rendu
 * avec succès ; revient au PNG si le rendu échoue pour une raison
 * quelconque, plutôt que de laisser un <canvas> vide à l'écran. Le
 * graphique Chart.js n'est jamais créé pendant que son <canvas> est masqué
 * (``display: none``) : Chart.js le dimensionnerait alors à 0×0, un piège
 * classique de son mode ``responsive`` — le <canvas> est donc rendu visible
 * (et le PNG masqué) avant l'appel à ``renderChart``, avec retour en arrière
 * en cas d'échec.
 *
 * ``renderChart`` ne reçoit aucun argument (les pages appelantes savent déjà
 * quelles données utiliser, voir ``resume.html``/``synthese.html``) et doit
 * renvoyer l'instance Chart.js créée, ou une valeur fausse en cas d'échec.
 */
function admShowRadarChart(canvasId, imageSelector, renderChart) {
  var canvas = document.getElementById(canvasId);
  var image = document.querySelector(imageSelector);
  if (!canvas) {
    return null;
  }
  canvas.classList.remove("d-none");
  if (image) {
    image.classList.add("d-none");
  }
  var chart = null;
  try {
    chart = renderChart();
  } catch (e) {
    chart = null;
  }
  if (!chart) {
    canvas.classList.add("d-none");
    if (image) {
      image.classList.remove("d-none");
    }
  }
  return chart;
}
