"""Testy service F-03."""

from pathlib import Path

import ifcopenshell

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f03_ifc_metadata import register_f03_feature
from src.features.f03_ifc_metadata.service import (
  apply_user_evaluations,
  is_f03_complete,
  run_f03_metadata,
)


def test_is_f03_complete_requires_all_evaluations() -> None:
  results = [
    CheckResult("V-3.1", "Nazwa pliku", CheckStatus.PASS, "model.ifc"),
    CheckResult("V-3.2", "IfcProject.Name", CheckStatus.SKIPPED, "Projekt"),
  ]

  assert is_f03_complete(results) is False


def test_is_f03_complete_when_all_pass_or_fail() -> None:
  results = [
    CheckResult(f"V-3.{index}", f"Pozycja {index}", CheckStatus.PASS, "OK")
    for index in range(1, 7)
  ]

  assert is_f03_complete(results) is True


def test_apply_user_evaluations_updates_status_and_comment() -> None:
  results = [
    CheckResult("V-3.1", "Nazwa pliku", CheckStatus.SKIPPED, "model.ifc"),
    CheckResult("V-3.2", "IfcProject.Name", CheckStatus.SKIPPED, "Projekt"),
  ]

  updated = apply_user_evaluations(
    results,
    evaluations={"V-3.1": CheckStatus.PASS, "V-3.2": CheckStatus.FAIL},
    comments={"V-3.1": "OK", "V-3.2": ""},
  )

  assert updated[0].status == CheckStatus.PASS
  assert updated[0].comment == "OK"
  assert updated[1].status == CheckStatus.FAIL
  assert updated[1].comment is None


def test_run_f03_metadata_updates_context(generated_ifc_fixtures: dict[str, Path]) -> None:
  register_f03_feature()
  metadata_path = generated_ifc_fixtures["with_metadata"]
  file_bytes = metadata_path.read_bytes()
  model = ifcopenshell.open(str(metadata_path))
  context = AuditContext(
    ifc_filename=metadata_path.name,
    ifc_file_bytes=file_bytes,
    ifc_model=model,
    f02_completed=True,
  )

  results = run_f03_metadata(context)

  assert len(results) == 6
  assert len(context.f03_results) == 6
  assert context.f03_completed is False
  assert results[1].message == "Test Project"
