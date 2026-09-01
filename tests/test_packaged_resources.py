"""Vérifie que les ressources installées restent identiques à leurs sources."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGED_RESOURCES = PROJECT_ROOT / "src" / "ADM" / "resources"


def _relative_files(directory: Path) -> set[Path]:
    return {
        path.relative_to(directory)
        for path in directory.rglob("*")
        if path.is_file() and path.name != "version.txt"
    }


def test_packaged_resources_match_runtime_sources() -> None:
    source_directories = (Path("static"), Path("templates"))

    assert (PACKAGED_RESOURCES / "config.json").read_bytes() == (
        PROJECT_ROOT / "config.json"
    ).read_bytes()
    for relative_directory in source_directories:
        source_directory = PROJECT_ROOT / relative_directory
        packaged_directory = PACKAGED_RESOURCES / relative_directory
        assert _relative_files(packaged_directory) == _relative_files(source_directory)
        for relative_file in _relative_files(source_directory):
            assert (packaged_directory / relative_file).read_bytes() == (
                source_directory / relative_file
            ).read_bytes()
