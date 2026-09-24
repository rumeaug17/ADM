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


def test_run_demo_forwards_optional_persistent_paths_when_present(tmp_path: Path) -> None:
    """Correctif : ``ADM_CONFIG_PATH``/``ADM_QUESTIONS_PATH``/``ADM_INFO_TEXTS_PATH``
    étaient auparavant absentes de ``.adm-demo.env`` (voir
    ``test_setup_demo_persists_optional_persistent_paths_when_defined`` pour le
    volet écriture), donc jamais restaurées au lancement de la démo : les
    modifications faites depuis /settings ou /settings/questions finissaient
    par réécrire silencieusement le config.json/questions.json/info_texts.json
    du paquet installé plutôt que l'emplacement persistant voulu. Un simple
    ``source`` du fichier généré doit suffire à les réinjecter dans le
    processus lancé."""
    scripts_directory = tmp_path / "scripts"
    scripts_directory.mkdir()
    shutil.copy(PROJECT_ROOT / "scripts" / "run_demo.sh", scripts_directory)
    virtualenv_python = tmp_path / ".venv" / "bin" / "python"
    virtualenv_python.parent.mkdir(parents=True)
    virtualenv_python.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$ADM_CONFIG_PATH" "$ADM_QUESTIONS_PATH" "$ADM_INFO_TEXTS_PATH"\n',
        encoding="utf-8",
    )
    virtualenv_python.chmod(0o755)
    (tmp_path / ".adm-demo.env").write_text(
        "export ADM_DB_BACKEND=json\n"
        "export ADM_DATABASE_URL=/tmp/adm-demo-catalogue-factice.json\n"
        "export ADM_ACCOUNTS_URL=/tmp/adm-demo-comptes-factices.json\n"
        "export ADM_SECRET_KEY=cle-factice-reservee-au-test\n"
        "export ADM_CONFIG_PATH=/tmp/adm-demo-persistant/config.json\n"
        "export ADM_QUESTIONS_PATH=/tmp/adm-demo-persistant/questions.json\n"
        "export ADM_INFO_TEXTS_PATH=/tmp/adm-demo-persistant/info_texts.json\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", str(scripts_directory / "run_demo.sh")],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "ADM_DEMO_VENV": str(tmp_path / ".venv")},
    )

    assert result.stdout.splitlines() == [
        "/tmp/adm-demo-persistant/config.json",
        "/tmp/adm-demo-persistant/questions.json",
        "/tmp/adm-demo-persistant/info_texts.json",
    ]


def test_run_demo_still_works_without_optional_persistent_paths(tmp_path: Path) -> None:
    """Compatibilité ascendante : un ``.adm-demo.env`` généré par une version
    antérieure de ``setup_demo.sh`` (sans les trois variables optionnelles) ne
    doit pas empêcher le lancement de la démo."""
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
        ["bash", str(scripts_directory / "run_demo.sh")],
        check=True,
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "ADM_DEMO_VENV": str(tmp_path / ".venv")},
    )

    assert result.stdout.splitlines() == ["main.py"]


def test_setup_demo_persists_optional_persistent_paths_when_defined() -> None:
    """Correctif : ``setup_demo.sh`` ne reprenait auparavant que 5 variables
    (``ADM_DB_BACKEND``, ``ADM_DATABASE_URL``, ``ADM_SECRET_KEY``,
    ``ADM_ACCOUNTS_URL``, ``ADM_SESSION_COOKIE_SECURE``) dans ``.adm-demo.env`` :
    si l'appelant avait défini ``ADM_CONFIG_PATH``/``ADM_QUESTIONS_PATH``/
    ``ADM_INFO_TEXTS_PATH`` avant de lancer le script (pour éviter d'écrire
    dans le paquet installé, comme en production), cette intention était
    silencieusement perdue dès le prochain ``run_demo.sh`` dans un nouveau
    terminal. Une exécution complète du script shell (avec un interpréteur
    Python factice, comme les deux tests précédents) serait disproportionnée
    ici : on vérifie directement que le script transmet bien ces trois
    variables au script Python embarqué et les ajoute à ``values`` avant
    l'écriture du fichier."""
    script = (PROJECT_ROOT / "scripts" / "setup_demo.sh").read_text(encoding="utf-8")

    assert 'ADM_DEMO_CONFIG_PATH="${ADM_CONFIG_PATH:-}"' in script
    assert 'ADM_DEMO_QUESTIONS_PATH="${ADM_QUESTIONS_PATH:-}"' in script
    assert 'ADM_DEMO_INFO_TEXTS_PATH="${ADM_INFO_TEXTS_PATH:-}"' in script
    assert '("ADM_CONFIG_PATH", "ADM_DEMO_CONFIG_PATH")' in script
    assert '("ADM_QUESTIONS_PATH", "ADM_DEMO_QUESTIONS_PATH")' in script
    assert '("ADM_INFO_TEXTS_PATH", "ADM_DEMO_INFO_TEXTS_PATH")' in script


def test_windows_setup_persists_optional_persistent_paths_when_defined() -> None:
    """Même correctif que ``test_setup_demo_persists_optional_persistent_paths_when_defined``,
    pour le pendant PowerShell (``setup_demo.ps1``/``run_demo.ps1``)."""
    setup_script = (PROJECT_ROOT / "scripts" / "setup_demo.ps1").read_text(encoding="utf-8")
    run_script = (PROJECT_ROOT / "scripts" / "run_demo.ps1").read_text(encoding="utf-8")

    assert "ADM_CONFIG_PATH           = $env:ADM_CONFIG_PATH" in setup_script
    assert "ADM_QUESTIONS_PATH        = $env:ADM_QUESTIONS_PATH" in setup_script
    assert "ADM_INFO_TEXTS_PATH       = $env:ADM_INFO_TEXTS_PATH" in setup_script

    assert "$optionalVariables = @(" in run_script
    assert '"ADM_CONFIG_PATH",' in run_script
    assert '"ADM_QUESTIONS_PATH",' in run_script
    assert '"ADM_INFO_TEXTS_PATH"' in run_script
    # Contrairement aux variables obligatoires, une valeur absente ne doit
    # jamais lever d'exception (compatibilité avec un .adm-demo.json antérieur
    # à ce correctif).
    assert (
        'throw "La variable $variableName est absente'
        not in run_script.split("$optionalVariables = @(")[1]
    )


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
