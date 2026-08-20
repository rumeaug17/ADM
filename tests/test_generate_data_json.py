"""Tests de compatibilité des données de démonstration avec le backend JSON."""

import json
import subprocess
import sys
from pathlib import Path

from ADM.database import Application


def test_generated_applications_can_be_loaded_by_json_backend(tmp_path: Path) -> None:
    """Le catalogue produit doit respecter les types attendus par la persistance."""
    project_root = Path(__file__).resolve().parents[1]
    static_directory = tmp_path / "static"
    static_directory.mkdir()
    (static_directory / "questions.json").write_text(
        (project_root / "static" / "questions.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    subprocess.run(
        [sys.executable, str(project_root / "scripts" / "generate_data_json.py")],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    records = json.loads((tmp_path / "applications.json").read_text(encoding="utf-8"))
    applications = [Application.from_dict(record) for record in records]

    assert len(applications) == 20
    assert all(isinstance(application.criticite, int) for application in applications)
