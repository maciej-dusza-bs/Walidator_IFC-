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


def test_is_f03_complete_requires_evaluable_items_only() -> None:
  results = [
    CheckResult("V-3.1", "Nazwa pliku", CheckStatus.PASS, "model.ifc"),
    CheckResult("V-3.2", "IfcProject.Name", CheckStatus.SKIPPED, "Projekt"),
    CheckResult("V-3.6", "Łączna liczba encji", CheckStatus.PASS, "100"),
  ]

  assert is_f03_complete(results) is False


def test_is_f03_complete_when_evaluable_items_have_pass_or_fail() -> None:
  results = [
    CheckResult(f"V-3.{index}", f"Pozycja {index}", CheckStatus.PASS, "OK")
    for index in range(1, 6)
  ]
  results.append(CheckResult("V-3.6", "Łączna liczba encji", CheckStatus.PASS, "100"))

  assert is_f03_complete(results) is True


def test_merge_user_evaluations_defaults_to_pass() -> None:
  from src.features.f03_ifc_metadata.service import merge_user_evaluations

  extracted = [
    CheckResult("V-3.1", "Nazwa pliku", CheckStatus.SKIPPED, "model.ifc"),
    CheckResult("V-3.6", "Łączna liczba encji", CheckStatus.SKIPPED, "10"),
  ]

  merged = merge_user_evaluations(extracted, [])

  assert merged[0].status == CheckStatus.PASS
  assert merged[1].status == CheckStatus.PASS


def test_is_f03_complete_when_all_pass_or_fail() -> None:
  results = [
    CheckResult(f"V-3.{index}", f"Pozycja {index}", CheckStatus.PASS, "OK")
    for index in range(1, 6)
  ]
  results.append(CheckResult("V-3.6", "Łączna liczba encji", CheckStatus.PASS, "100"))

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
