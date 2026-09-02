"""Wspólna konfiguracja pytest."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Zwraca ścieżkę do katalogu z plikami testowymi."""
    return FIXTURES_DIR
