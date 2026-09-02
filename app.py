"""Punkt wejścia aplikacji Walidator IFC MVP."""

from src.features.f02_ifc_validation import register_f02_feature
from src.features.f03_ifc_metadata import register_f03_feature
from src.features.f04_ifc_classes import register_f04_feature
from src.ui.workflow import render_app


def main() -> None:
  register_f02_feature()
  register_f03_feature()
  register_f04_feature()
  render_app()


if __name__ == "__main__":
  main()
