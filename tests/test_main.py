"""Tests du point d'entrée de l'application."""

from unittest.mock import Mock

from pytest import MonkeyPatch

from ADM import cli


def test_parse_debug_option_is_disabled_by_default() -> None:
    assert cli.parse_debug_option([]) is False


def test_parse_debug_option_enables_debug() -> None:
    assert cli.parse_debug_option(["--debug"]) is True


def test_run_server_passes_debug_mode_to_flask(monkeypatch: MonkeyPatch) -> None:
    application = Mock()
    monkeypatch.setattr(cli, "create_app", Mock(return_value=application))

    cli.run_server(debug=True)

    application.run.assert_called_once_with(debug=True)
