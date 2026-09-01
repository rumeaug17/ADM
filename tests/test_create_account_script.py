"""Tests du point d'entrée autonome de création de compte."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

from pytest import MonkeyPatch


def test_create_account_script_loads_checkout_package_without_installation(
    monkeypatch: MonkeyPatch,
) -> None:
    """Le script doit fonctionner même si ``src`` n'est pas dans ``sys.path``."""
    project_root = Path(__file__).resolve().parents[1]
    command_called = False

    def fake_command() -> None:
        nonlocal command_called
        command_called = True

    adm_module = ModuleType("ADM")
    cli_module = ModuleType("ADM.cli")
    cli_module.create_account_command = fake_command
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setitem(sys.modules, "ADM", adm_module)
    monkeypatch.setitem(sys.modules, "ADM.cli", cli_module)

    script_path = project_root / "scripts" / "create_account.py"
    spec = spec_from_file_location("create_account_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    script_module = module_from_spec(spec)
    spec.loader.exec_module(script_module)
    script_module.main()

    assert command_called
    assert Path(sys.path[0]) == project_root / "src"
