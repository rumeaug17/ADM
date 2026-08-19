import json
from pathlib import Path

from ADM.documentation import clean_html, main


def test_clean_html_converts_supported_tags() -> None:
    assert clean_html("<strong>Titre</strong><br><ul><li>Point</li></ul>") == ("**Titre**\n- Point")


def test_main_uses_the_supplied_project_root(tmp_path: Path) -> None:
    static_directory = tmp_path / "static"
    static_directory.mkdir()
    questions = {
        "Architecture": {
            "api": {
                "label": "API documentée",
                "type": "select",
                "options": [{"value": "Oui", "score": 0}],
            }
        }
    }
    (static_directory / "questions.json").write_text(json.dumps(questions), encoding="utf-8")
    (static_directory / "info_texts.json").write_text(
        json.dumps({"api": "<strong>Aide</strong>"}), encoding="utf-8"
    )

    main(tmp_path)

    generated_documentation = (tmp_path / "documentation.md").read_text(encoding="utf-8")
    assert "### Question : API documentée" in generated_documentation
    assert "> **Aide**" in generated_documentation
