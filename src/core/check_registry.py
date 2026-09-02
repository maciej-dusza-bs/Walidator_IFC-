"""Rejestr funkcjonalności audytu i ich runnerów."""

from __future__ import annotations

from collections.abc import Callable

from src.core.audit_context import AuditContext
from src.core.models import CheckResult

FeatureRunner = Callable[[AuditContext], list[CheckResult]]

_REGISTRY: dict[str, FeatureRunner] = {}


def register_feature(feature_id: str, runner: FeatureRunner) -> None:
  """Rejestruje runner funkcjonalności pod podanym identyfikatorem."""
  _REGISTRY[feature_id] = runner


def get_feature_runner(feature_id: str) -> FeatureRunner | None:
  """Zwraca runner funkcjonalności lub None, jeśli nie jest zarejestrowany."""
  return _REGISTRY.get(feature_id)


def list_registered_features() -> list[str]:
  """Zwraca posortowaną listę zarejestrowanych identyfikatorów funkcjonalności."""
  return sorted(_REGISTRY.keys())
