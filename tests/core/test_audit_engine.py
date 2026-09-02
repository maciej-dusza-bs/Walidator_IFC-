"""Testy rdzenia: rejestr i silnik audytu."""

from src.core.audit_context import AuditContext
from src.core.audit_engine import get_audit_summary, run_feature
from src.core.check_registry import list_registered_features, register_feature
from src.core.models import CheckResult, CheckStatus


def test_run_feature_returns_error_when_not_registered() -> None:
  context = AuditContext()

  result = run_feature(context, "F-99", "Nieistniejąca funkcjonalność")

  assert result.status == CheckStatus.ERROR
  assert len(context.all_results()) == 1
  assert context.all_results()[0].check_id == "F-99-UNREGISTERED"


def test_register_and_run_feature() -> None:
  def _runner(context: AuditContext) -> list[CheckResult]:
    return [
      CheckResult(
        check_id="TEST-1",
        name="Test",
        status=CheckStatus.PASS,
        message="OK",
      )
    ]

  register_feature("F-TEST", _runner)
  context = AuditContext()

  result = run_feature(context, "F-TEST", "Testowa funkcjonalność")

  assert result.status == CheckStatus.PASS
  assert "F-TEST" in list_registered_features()
  assert get_audit_summary(context) == CheckStatus.PASS
