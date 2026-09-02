"""Modele danych wspólne dla całej aplikacji."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
  """Dozwolone statusy wyniku sprawdzenia."""

  PASS = "PASS"
  FAIL = "FAIL"
  WARNING = "WARNING"
  SKIPPED = "SKIPPED"
  ERROR = "ERROR"


class WorkflowStep(int, Enum):
  """Kroki workflow aplikacji."""

  START = 1
  IFC_VALIDATION = 2
  METADATA = 3
  IFC_CLASSES = 4
  REPORT = 5


WORKFLOW_STEP_LABELS: dict[WorkflowStep, str] = {
  WorkflowStep.START: "F-01 Uruchomienie",
  WorkflowStep.IFC_VALIDATION: "F-02 Walidacja IFC",
  WorkflowStep.METADATA: "F-03 Metadane",
  WorkflowStep.IFC_CLASSES: "F-04 Klasy IFC",
  WorkflowStep.REPORT: "F-05 Raport",
}

TOTAL_WORKFLOW_STEPS = len(WorkflowStep)


@dataclass
class CheckResult:
  """Ujednolicony wynik pojedynczego sprawdzenia."""

  check_id: str
  name: str
  status: CheckStatus
  message: str
  value: Any | None = None
  comment: str | None = None


@dataclass
class FeatureResult:
  """Zbiorczy wynik funkcjonalności audytu."""

  feature_id: str
  name: str
  checks: list[CheckResult] = field(default_factory=list)

  @property
  def status(self) -> CheckStatus:
    if not self.checks:
      return CheckStatus.SKIPPED
    if any(check.status == CheckStatus.ERROR for check in self.checks):
      return CheckStatus.ERROR
    if any(check.status == CheckStatus.FAIL for check in self.checks):
      return CheckStatus.FAIL
    if any(check.status == CheckStatus.WARNING for check in self.checks):
      return CheckStatus.WARNING
    if all(check.status == CheckStatus.SKIPPED for check in self.checks):
      return CheckStatus.SKIPPED
    return CheckStatus.PASS


def compute_overall_status(checks: list[CheckResult]) -> CheckStatus:
  """Oblicza status całej kontroli na podstawie wykonanych sprawdzeń."""
  executed = [check for check in checks if check.status != CheckStatus.SKIPPED]
  if not executed:
    return CheckStatus.SKIPPED
  if any(check.status in (CheckStatus.FAIL, CheckStatus.ERROR) for check in executed):
    return CheckStatus.FAIL
  return CheckStatus.PASS
