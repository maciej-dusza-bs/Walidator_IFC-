"""F-03 — weryfikacja metadanych pliku i modelu."""

from src.core.check_registry import register_feature
from src.features.f03_ifc_metadata.service import run_f03_metadata


def register_f03_feature() -> None:
  """Rejestruje funkcjonalność F-03 w rejestrze audytu."""
  register_feature("F-03", run_f03_metadata)
