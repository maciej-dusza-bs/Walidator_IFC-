"""F-02 — wczytanie i walidacja modelu IFC."""

from src.core.check_registry import register_feature
from src.features.f02_ifc_validation.service import run_f02_validation


def register_f02_feature() -> None:
  """Rejestruje funkcjonalność F-02 w rejestrze audytu."""
  register_feature("F-02", run_f02_validation)
