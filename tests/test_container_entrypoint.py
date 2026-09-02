"""Tests légers de docker-entrypoint.sh, le point d'entrée de l'image conteneurisée
(Tâche 0.3 du backlog, voir Dockerfile et docs/CONTAINER.md)."""

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = PROJECT_ROOT / "docker-entrypoint.sh"


def _write_stub(path: Path) -> None:
    """Écrit un exécutable factice affichant les arguments reçus, un par ligne."""
    path.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n", encoding="utf-8")
    path.chmod(0o755)


def _run_entrypoint(tmp_path: Path, arguments: list[str], env_overrides: dict[str, str]) -> str:
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    _write_stub(bin_directory / "gunicorn")
    _write_stub(bin_directory / "alembic")
    result = subprocess.run(
        ["bash", str(ENTRYPOINT), *arguments],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PATH": f"{bin_directory}:{os.environ['PATH']}", **env_overrides},
    )
    return result.stdout


def test_entrypoint_has_valid_syntax() -> None:
    subprocess.run(["bash", "-n", str(ENTRYPOINT)], check=True)


def test_entrypoint_defaults_to_web_command(tmp_path: Path) -> None:
    stdout = _run_entrypoint(tmp_path, [], {})

    assert "--bind" in stdout
    assert "0.0.0.0:8000" in stdout
    assert "ADM.app:create_app()" in stdout


def test_entrypoint_web_command_honors_port_and_workers_overrides(tmp_path: Path) -> None:
    stdout = _run_entrypoint(
        tmp_path, ["web"], {"ADM_HTTP_PORT": "9000", "ADM_GUNICORN_WORKERS": "4"}
    )

    assert "0.0.0.0:9000" in stdout
    assert "4" in stdout.splitlines()


def test_entrypoint_migrate_command_invokes_alembic_upgrade_head(tmp_path: Path) -> None:
    stdout = _run_entrypoint(tmp_path, ["migrate"], {})

    assert stdout.splitlines() == ["upgrade", "head"]


def test_entrypoint_passes_through_unknown_command(tmp_path: Path) -> None:
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    _write_stub(bin_directory / "gunicorn")
    _write_stub(bin_directory / "alembic")
    _write_stub(bin_directory / "some-other-tool")

    result = subprocess.run(
        ["bash", str(ENTRYPOINT), "some-other-tool", "--flag"],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PATH": f"{bin_directory}:{os.environ['PATH']}"},
    )

    assert result.stdout.splitlines() == ["--flag"]
