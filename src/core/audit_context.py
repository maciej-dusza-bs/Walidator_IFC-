"""Kontekst audytu przekazywany między funkcjonalnościami."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.models import CheckResult, WorkflowStep


@dataclass
class AuditContext:
  """Stan bieżącej kontroli modelu IFC."""

  ifc_filename: str | None = None
  ifc_file_bytes: bytes | None = None
  ifc_temp_path: str | None = None
  ifc_model: Any | None = None
  check_results: list[CheckResult] = field(default_factory=list)
  current_step: WorkflowStep = WorkflowStep.START
  step1_acknowledged: bool = False
  f02_results: list[CheckResult] = field(default_factory=list)
  v28_accepted: bool = False
  f02_completed: bool = False
  f03_completed: bool = False
  f04_completed: bool = False
  f04_skipped: bool = False

  def all_results(self) -> list[CheckResult]:
    return list(self.check_results)

  def add_results(self, results: list[CheckResult]) -> None:
    self.check_results.extend(results)

  def replace_feature_results(self, check_ids: set[str], results: list[CheckResult]) -> None:
    self.check_results = [result for result in self.check_results if result.check_id not in check_ids]
    self.check_results.extend(results)

  def is_step_unlocked(self, step: WorkflowStep) -> bool:
    if step == WorkflowStep.START:
      return True
    if step == WorkflowStep.IFC_VALIDATION:
      return self.step1_acknowledged
    if step == WorkflowStep.METADATA:
      return self.f02_completed
    if step == WorkflowStep.IFC_CLASSES:
      return self.f03_completed
    if step == WorkflowStep.REPORT:
      return self.f04_completed or self.f04_skipped
    return False

  def is_step_completed(self, step: WorkflowStep) -> bool:
    if step == WorkflowStep.START:
      return self.step1_acknowledged
    if step == WorkflowStep.IFC_VALIDATION:
      return self.f02_completed
    if step == WorkflowStep.METADATA:
      return self.f03_completed
    if step == WorkflowStep.IFC_CLASSES:
      return self.f04_completed or self.f04_skipped
    if step == WorkflowStep.REPORT:
      return False
    return False
