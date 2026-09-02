"""Testy interfejsu aplikacji Streamlit."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_app_starts_with_polish_instruction() -> None:
  app_test = AppTest.from_file(PROJECT_ROOT / "app.py")
  app_test.run(timeout=10)

  assert not app_test.exception
  assert app_test.title[0].value == "Walidator IFC"
  assert any("Witaj w Walidatorze IFC" in markdown.value for markdown in app_test.markdown)
  assert any("Rozpocznij kontrolę" in button.label for button in app_test.button)


def test_app_shows_progress_for_step_one() -> None:
  app_test = AppTest.from_file(PROJECT_ROOT / "app.py")
  app_test.run(timeout=10)

  assert any("Krok 1 z 5" in caption.value for caption in app_test.caption)
