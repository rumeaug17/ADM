"""Tests de la persistance atomique du questionnaire et de son aide en ligne (US4.3)."""

import json
from pathlib import Path

import pytest

from ADM.persistent_paths import resolve_persistent_path
from ADM.questions_io import (
    delete_question_help_text,
    get_question_help_text,
    save_questions,
    set_question_help_text,
)


def test_resolve_persistent_path_seeds_from_template_when_missing(tmp_path: Path) -> None:
    template = tmp_path / "template.json"
    template.write_text('{"template": true}', encoding="utf-8")
    target = tmp_path / "persistent" / "questions.json"

    resolved = resolve_persistent_path(str(target), template)

    assert resolved == target
    assert json.loads(target.read_text(encoding="utf-8")) == {"template": True}


def test_resolve_persistent_path_keeps_existing_file_untouched(tmp_path: Path) -> None:
    template = tmp_path / "template.json"
    template.write_text('{"template": true}', encoding="utf-8")
    target = tmp_path / "questions.json"
    target.write_text('{"custom": true}', encoding="utf-8")

    resolve_persistent_path(str(target), template)

    assert json.loads(target.read_text(encoding="utf-8")) == {"custom": True}


def test_save_questions_writes_normalized_json(tmp_path: Path) -> None:
    path = tmp_path / "questions.json"
    questions = {
        "Architecture": {
            "api": {
                "label": "Utilise-t-on des API standardisées ?",
                "type": "select",
                "weight": 2,
                "options": [{"value": "Oui", "score": 0}],
            }
        }
    }

    save_questions(path, questions)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == questions
    assert not path.with_suffix(".json.tmp").exists()


def test_save_questions_atomic_on_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "questions.json"
    original = json.dumps({"Architecture": {}})
    path.write_text(original, encoding="utf-8")

    def _boom(self: Path, *args: object, **kwargs: object) -> int:
        raise OSError("disque plein simulé")

    monkeypatch.setattr(Path, "write_text", _boom)
    with pytest.raises(ValueError, match="enregistrer"):
        save_questions(path, {"Architecture": {}})
    monkeypatch.undo()
    assert path.read_text(encoding="utf-8") == original


def test_get_question_help_text_rejects_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"

    with pytest.raises(ValueError, match="lire"):
        get_question_help_text(path, "api")


def test_get_question_help_text_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON valide"):
        get_question_help_text(path, "api")


def test_get_question_help_text_rejects_a_non_object_root(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ValueError, match="objet JSON"):
        get_question_help_text(path, "api")


def test_set_question_help_text_atomic_on_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "info_texts.json"
    original = json.dumps({"api": "Aide existante"})
    path.write_text(original, encoding="utf-8")

    def _boom(self: Path, *args: object, **kwargs: object) -> int:
        raise OSError("disque plein simulé")

    monkeypatch.setattr(Path, "write_text", _boom)
    with pytest.raises(ValueError, match="enregistrer"):
        set_question_help_text(path, "api", "Nouvelle aide")
    monkeypatch.undo()
    assert path.read_text(encoding="utf-8") == original


def test_get_question_help_text_returns_empty_string_when_absent(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text("{}", encoding="utf-8")

    assert get_question_help_text(path, "api") == ""


def test_get_question_help_text_joins_array_of_lines(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text(json.dumps({"api": ["Ligne 1", "<br>", "Ligne 2"]}), encoding="utf-8")

    assert get_question_help_text(path, "api") == "Ligne 1<br>Ligne 2"


def test_set_question_help_text_preserves_other_keys(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text(json.dumps({"other": "conservé"}), encoding="utf-8")

    set_question_help_text(path, "api", "Nouvelle aide")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {"other": "conservé", "api": "Nouvelle aide"}


def test_delete_question_help_text_removes_existing_key(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text(json.dumps({"api": "Aide", "other": "conservé"}), encoding="utf-8")

    delete_question_help_text(path, "api")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {"other": "conservé"}


def test_delete_question_help_text_is_a_noop_when_absent(tmp_path: Path) -> None:
    path = tmp_path / "info_texts.json"
    path.write_text(json.dumps({"other": "conservé"}), encoding="utf-8")

    delete_question_help_text(path, "inconnue")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {"other": "conservé"}
