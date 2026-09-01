"""Tests légers des scripts shell de préparation et de lancement de la démo."""

import os
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_shell_demo_scripts_have_valid_syntax() -> None:
    subprocess.run(
        ["bash", "-n", "scripts/setup_demo.sh", "scripts/run_demo.sh"],
        cwd=PROJECT_ROOT,
        check=True,
    )


def test_run_demo_forwards_debug_mode_to_virtualenv_python(tmp_path: Path) -> None:
    scripts_directory = tmp_path / "scripts"
    scripts_directory.mkdir()
    shutil.copy(PROJECT_ROOT / "scripts" / "run_demo.sh", scripts_directory)
    virtualenv_python = tmp_path / ".venv" / "bin" / "python"
    virtualenv_python.parent.mkdir(parents=True)
    virtualenv_python.write_text(
        "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n",
        encoding="utf-8",
    )
    virtualenv_python.chmod(0o755)
    (tmp_path / ".adm-demo.env").write_text(
        "export ADM_DB_BACKEND=json\n"
        "export ADM_DATABASE_URL=/tmp/adm-demo-catalogue-factice.json\n"
        "export ADM_ACCOUNTS_URL=/tmp/adm-demo-comptes-factices.json\n"
        "export ADM_SECRET_KEY=cle-factice-reservee-au-test\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_directory / "run_demo.sh"), "--debug-mode", "on"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "ADM_DEMO_VENV": str(tmp_path / ".venv")},
    )

    assert result.stdout.splitlines() == ["main.py", "--debug"]


def test_setup_demo_runs_complete_command_sequence_with_selected_python(tmp_path: Path) -> None:
    scripts_directory = tmp_path / "scripts"
    static_directory = tmp_path / "src" / "ADM" / "resources" / "static"
    scripts_directory.mkdir()
    static_directory.mkdir(parents=True)
    legacy_version = tmp_path / "static" / "version.txt"
    legacy_version.parent.mkdir()
    legacy_version.write_text("ancienne-version\n", encoding="utf-8")
    shutil.copy(PROJECT_ROOT / "scripts" / "setup_demo.sh", scripts_directory)
    fake_python = tmp_path / "python-factice"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "set -eu\n"
        "if [[ ${1:-} == -m && ${2:-} == venv ]]; then\n"
        '  mkdir -p "$3/bin"\n'
        '  cp "$0" "$3/bin/python"\n'
        "fi\n",
        encoding="utf-8",
    )
    fake_python.chmod(0o755)

    result = subprocess.run(
        ["bash", str(scripts_directory / "setup_demo.sh")],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHON_BIN": str(fake_python)},
    )

    assert "Installation terminée" in result.stdout
    assert (tmp_path / ".venv" / "bin" / "python").is_file()
    assert (static_directory / "version.txt").read_text(encoding="utf-8") == "v0.1.0\n"
    assert not legacy_version.exists()


def test_windows_setup_uses_acl_command_without_security_privilege() -> None:
    script = (PROJECT_ROOT / "scripts" / "setup_demo.ps1").read_text(encoding="utf-8")

    assert "Protect-DemoConfigFile -Path $ConfigFile" in script
    assert 'Invoke-CheckedCommand -Command "icacls.exe"' in script
    assert 'Remove-Item -Force (Join-Path $ProjectRoot "static\\version.txt")' in script
    assert "Set-Acl" not in script
