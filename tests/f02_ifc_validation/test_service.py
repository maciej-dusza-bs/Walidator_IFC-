"""Testy service F-02."""

from pathlib import Path

from src.core.audit_context import AuditContext
from src.core.models import CheckStatus
from src.features.f02_ifc_validation.service import (
  apply_v28_acceptance,
  can_proceed_after_f02,
  run_f02_validation,
)
from src.features.f02_ifc_validation import register_f02_feature


def test_run_f02_validation_updates_context(generated_ifc_fixtures: dict[str, Path]) -> None:
  register_f02_feature()
  valid_path = generated_ifc_fixtures["valid"]
  context = AuditContext(
    ifc_filename=valid_path.name,
    ifc_file_bytes=valid_path.read_bytes(),
  )

  results = run_f02_validation(context)

  assert len(results) == 8
  assert context.ifc_model is not None
  assert context.ifc_temp_path is not None
  assert context.f02_completed is True
  assert all(result.status == CheckStatus.PASS for result in results)


def test_apply_v28_acceptance_sets_comment(generated_ifc_fixtures: dict[str, Path]) -> None:
  ifc4_path = generated_ifc_fixtures["ifc4"]
  context = AuditContext(
    ifc_filename=ifc4_path.name,
    ifc_file_bytes=ifc4_path.read_bytes(),
  )
  register_f02_feature()
  results = run_f02_validation(context)

  updated = apply_v28_acceptance(results)
  v28 = next(result for result in updated if result.check_id == "V-2.8")

  assert v28.comment == "zaakceptowano"
  assert can_proceed_after_f02(updated, v28_accepted=True) is True
