"""Punkt wejścia aplikacji Walidator IFC MVP."""

from src.features.f02_ifc_validation import register_f02_feature
from src.ui.workflow import render_app


def main() -> None:
  register_f02_feature()
  render_app()


if __name__ == "__main__":
  main()
