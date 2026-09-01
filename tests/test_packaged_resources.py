"""Vérifie que les ressources d’exécution ont une source unique dans le paquet."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGED_RESOURCES = PROJECT_ROOT / "src" / "ADM" / "resources"


def test_runtime_resources_only_exist_in_package() -> None:
    expected_resources = {
        Path("config.json"),
        Path("static/info_texts.json"),
        Path("static/logo.svg"),
        Path("static/questions.json"),
        Path("templates/base.html"),
        Path("templates/login.html"),
    }

    assert all((PACKAGED_RESOURCES / path).is_file() for path in expected_resources)
    assert all(not (PROJECT_ROOT / path).exists() for path in expected_resources)
