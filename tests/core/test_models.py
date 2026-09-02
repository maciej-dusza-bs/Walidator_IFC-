"""Testy modeli rdzenia aplikacji."""

from src.core.audit_context import AuditContext
from src.core.models import (
  CheckResult,
  CheckStatus,
  FeatureResult,
  WorkflowStep,
  compute_overall_status,
)


def test_check_result_accepts_optional_fields() -> None:
  result = CheckResult(
    check_id="V-2.1",
    name="Plik został przesłany",
    status=CheckStatus.PASS,
    message="Plik jest dostępny.",
    value="model.ifc",
    comment="OK",
  )

  assert result.check_id == "V-2.1"
  assert result.status == CheckStatus.PASS
  assert result.value == "model.ifc"
  assert result.comment == "OK"


def test_feature_result_status_fail_when_any_check_fails() -> None:
  feature = FeatureResult(
    feature_id="F-02",
    name="Walidacja IFC",
    checks=[
      CheckResult("V-2.1", "Upload", CheckStatus.PASS, "OK"),
      CheckResult("V-2.2", "Rozszerzenie", CheckStatus.FAIL, "Błędne rozszerzenie"),
    ],
  )

  assert feature.status == CheckStatus.FAIL


def test_compute_overall_status_counts_only_executed_checks() -> None:
  checks = [
    CheckResult("V-4.1", "Klasa A", CheckStatus.PASS, "OK"),
    CheckResult("F-04", "Pominięto", CheckStatus.SKIPPED, "Pominięto"),
  ]

  assert compute_overall_status(checks) == CheckStatus.PASS


def test_compute_overall_status_fail_on_error_or_fail() -> None:
  checks = [
    CheckResult("V-3.1", "Metadane", CheckStatus.FAIL, "Odrzucone przez użytkownika"),
  ]

  assert compute_overall_status(checks) == CheckStatus.FAIL


def test_audit_context_step_unlocking() -> None:
  context = AuditContext()

  assert context.is_step_unlocked(WorkflowStep.START) is True
  assert context.is_step_unlocked(WorkflowStep.IFC_VALIDATION) is False

  context.step1_acknowledged = True

  assert context.is_step_unlocked(WorkflowStep.IFC_VALIDATION) is True
  assert context.is_step_completed(WorkflowStep.START) is True
