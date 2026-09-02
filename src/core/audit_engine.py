"""Silnik uruchamiający funkcjonalności audytu i agregujący wyniki."""

from __future__ import annotations

from src.core.audit_context import AuditContext
from src.core.check_registry import get_feature_runner
from src.core.models import CheckResult, CheckStatus, FeatureResult, compute_overall_status


def run_feature(context: AuditContext, feature_id: str, feature_name: str) -> FeatureResult:
  """Uruchamia funkcjonalność i zapisuje jej wyniki w kontekście audytu."""
  runner = get_feature_runner(feature_id)
  if runner is None:
    result = CheckResult(
      check_id=f"{feature_id}-UNREGISTERED",
      name=f"Brak implementacji funkcjonalności {feature_id}",
      status=CheckStatus.ERROR,
      message=(
        f"Funkcjonalność {feature_id} nie została jeszcze zarejestrowana. "
        "Kontynuacja audytu dla tego kroku nie jest możliwa."
      ),
    )
    context.add_results([result])
    return FeatureResult(feature_id=feature_id, name=feature_name, checks=[result])

  checks = runner(context)
  context.add_results(checks)
  return FeatureResult(feature_id=feature_id, name=feature_name, checks=checks)


def get_audit_summary(context: AuditContext) -> CheckStatus:
  """Zwraca status całej kontroli na podstawie zebranych wyników."""
  return compute_overall_status(context.all_results())
