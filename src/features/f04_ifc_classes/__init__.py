"""F-04 — weryfikacja dopuszczalnych klas IFC."""

from src.core.check_registry import register_feature
from src.features.f04_ifc_classes.service import run_f04_ifc_classes


def register_f04_feature() -> None:
  """Rejestruje funkcjonalność F-04 w rejestrze audytu."""
  register_feature("F-04", run_f04_ifc_classes)
