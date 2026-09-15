"""Résolution d'un chemin persistant pour un fichier de configuration éditable.

Facteur commun entre ``config.json`` (US4.2, ``ADM_CONFIG_PATH``) et le
questionnaire (``questions.json``/``info_texts.json``, US4.3,
``ADM_QUESTIONS_PATH``/``ADM_INFO_TEXTS_PATH``) : ces fichiers sont réécrits à
chaud depuis l'interface d'administration. Les laisser par défaut sous
``PACKAGE_RESOURCES`` fonctionne, mais ce chemin se trouve à l'intérieur du
paquet installé (site-packages ou virtualenv) : une mise à jour du wheel (voir
INSTALL.md, section 12) le remplace intégralement et efface silencieusement
toute personnalisation. Une variable d'environnement dédiée permet de pointer
vers un emplacement persistant, à l'image d'``ADM_DATABASE_URL`` ou
``ADM_ACCOUNTS_URL``. Si elle désigne un fichier qui n'existe pas encore, il
est initialisé à partir du gabarit empaqueté.
"""

from pathlib import Path


def resolve_persistent_path(configured: str, package_template: Path) -> Path:
    """Retourne le chemin persistant à utiliser, en le créant si nécessaire.

    ``configured`` est soit le chemin par défaut (à l'intérieur du paquet),
    soit celui fourni par une variable d'environnement dédiée. ``package_template``
    est le gabarit empaqueté utilisé pour initialiser le fichier s'il est absent.
    """
    path = Path(configured)
    if not path.exists():
        default_content = package_template.read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_content, encoding="utf-8")
    return path
