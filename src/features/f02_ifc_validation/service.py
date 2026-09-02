"""Orkiestracja sprawdzeń F-02."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f02_ifc_validation.checks import (
  BLOCKING_CHECK_IDS,
  check_v21_file_uploaded,
  check_v22_extension,
  check_v23_file_size,
  check_v24_iso_header,
  check_v25_file_schema,
  check_v26_open_with_ifcopenshell,
  check_v27_single_ifc_project,
  check_v28_schema_ifc2x3,
)
from src.io_adapters.ifc_reader import TempIfcFile

F02_CHECK_IDS = {f"V-2.{index}" for index in range(1, 9)}
V28_ACCEPTANCE_COMMENT = "zaakceptowano"


def validate_ifc_file(
  filename: str | None,
  file_bytes: bytes | None,
) -> tuple[list[CheckResult], Path | None, Any | None]:
  """Uruchamia sprawdzenia V-2.1–V-2.8 i zwraca wyniki oraz otwarty model."""
  results: list[CheckResult] = []
  temp_path: Path | None = None
  model: Any | None = None

  result = check_v21_file_uploaded(filename, file_bytes)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result = check_v22_extension(filename)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result = check_v23_file_size(file_bytes)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result, header_text = check_v24_iso_header(file_bytes)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result = check_v25_file_schema(header_text)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result, temp_path, model = check_v26_open_with_ifcopenshell(file_bytes)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    return results, None, None

  result = check_v27_single_ifc_project(model)
  results.append(result)
  if result.status == CheckStatus.FAIL:
    if temp_path is not None:
      TempIfcFile(path=temp_path).cleanup()
    return results, None, None

  result = check_v28_schema_ifc2x3(model)
  results.append(result)

  return results, temp_path, model


def can_proceed_after_f02(results: list[CheckResult], v28_accepted: bool) -> bool:
  """Sprawdza, czy po F-02 można przejść do F-03."""
  by_id = {result.check_id: result for result in results}

  if not all(check_id in by_id for check_id in BLOCKING_CHECK_IDS):
    return False
  if any(by_id[check_id].status != CheckStatus.PASS for check_id in BLOCKING_CHECK_IDS):
    return False

  v28 = by_id.get("V-2.8")
  if v28 is None:
    return False
  if v28.status == CheckStatus.WARNING:
    return v28_accepted
  return v28.status == CheckStatus.PASS


def apply_v28_acceptance(results: list[CheckResult]) -> list[CheckResult]:
  """Ustawia komentarz akceptacji dla ostrzeżenia V-2.8."""
  updated_results: list[CheckResult] = []
  for result in results:
    if result.check_id == "V-2.8" and result.status == CheckStatus.WARNING:
      updated_results.append(
        CheckResult(
          check_id=result.check_id,
          name=result.name,
          status=result.status,
          message=result.message,
          value=result.value,
          comment=V28_ACCEPTANCE_COMMENT,
        )
      )
    else:
      updated_results.append(result)
  return updated_results


def run_f02_validation(context: AuditContext) -> list[CheckResult]:
  """Uruchamia walidację IFC na podstawie danych z kontekstu audytu."""
  if context.ifc_temp_path is not None:
    TempIfcFile(path=Path(context.ifc_temp_path)).cleanup()
    context.ifc_temp_path = None
    context.ifc_model = None

  results, temp_path, model = validate_ifc_file(context.ifc_filename, context.ifc_file_bytes)
  context.replace_feature_results(F02_CHECK_IDS, results)
  context.f02_results = results

  if temp_path is not None:
    context.ifc_temp_path = str(temp_path)
  context.ifc_model = model
  context.f02_completed = can_proceed_after_f02(results, context.v28_accepted)
  return results
