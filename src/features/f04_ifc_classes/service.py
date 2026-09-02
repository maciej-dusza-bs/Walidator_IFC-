"""Orkiestracja funkcjonalności F-04."""

from __future__ import annotations

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f04_ifc_classes.checks import (
  build_class_check_results,
  build_class_verification_rows,
  create_skipped_f04_result,
  has_disallowed_classes,
  normalize_allowed_classes,
)
from src.io_adapters.xlsx_reader import AllowedClassesLoadResult, read_allowed_ifc_classes


def collect_f04_check_ids(results: list[CheckResult]) -> set[str]:
  """Zbiera identyfikatory sprawdzeń F-04 do podmiany w kontekście."""
  check_ids = {result.check_id for result in results}
  check_ids.add("F-04")
  return check_ids


def apply_f04_results(context: AuditContext, results: list[CheckResult]) -> None:
  """Zapisuje wyniki F-04 w kontekście audytu."""
  old_ids = collect_f04_check_ids(context.f04_results)
  context.replace_feature_results(old_ids, results)
  context.f04_results = results


def is_f04_analysis_successful(results: list[CheckResult]) -> bool:
  """Sprawdza, czy analiza klas została wykonana bez pominięcia."""
  if not results:
    return False
  if len(results) == 1 and results[0].check_id == "F-04" and results[0].status == CheckStatus.SKIPPED:
    return False
  return all(result.check_id.startswith("V-4.") for result in results)


def run_class_verification(context: AuditContext) -> list[CheckResult]:
  """Uruchamia sprawdzenie klas IFC względem listy dopuszczalnej."""
  if context.ifc_model is None:
    results = [
      CheckResult(
        check_id="F-04",
        name="Weryfikacja dopuszczalnych klas IFC",
        status=CheckStatus.ERROR,
        message="Brak otwartego modelu IFC. Nie można wykonać sprawdzenia klas.",
      )
    ]
    apply_f04_results(context, results)
    return results

  if not context.f04_allowed_classes:
    results = [
      CheckResult(
        check_id="F-04",
        name="Weryfikacja dopuszczalnych klas IFC",
        status=CheckStatus.ERROR,
        message="Brak wczytanej listy dopuszczalnych klas IFC.",
      )
    ]
    apply_f04_results(context, results)
    return results

  rows = build_class_verification_rows(context.ifc_model, context.f04_allowed_classes)
  results = build_class_check_results(rows)
  context.f04_class_rows = rows
  context.f04_completed = True
  context.f04_skipped = False
  context.f04_has_failures = has_disallowed_classes(rows)
  apply_f04_results(context, results)
  return results


def skip_f04(context: AuditContext, message: str | None = None) -> list[CheckResult]:
  """Oznacza F-04 jako pominiętą i umożliwia przejście dalej."""
  results = [create_skipped_f04_result(message)]
  context.f04_class_rows = []
  context.f04_completed = False
  context.f04_skipped = True
  context.f04_has_failures = False
  apply_f04_results(context, results)
  return results


def load_allowed_classes(
  file_bytes: bytes,
  sheet_name: str,
  column_name: str | None = None,
) -> AllowedClassesLoadResult:
  """Wczytuje listę dopuszczalnych klas z pliku XLSX."""
  result = read_allowed_ifc_classes(file_bytes, sheet_name, column_name)
  if result.error_message:
    return result
  return AllowedClassesLoadResult(
    classes=normalize_allowed_classes(result.classes),
    selected_column=result.selected_column,
  )


def run_f04_ifc_classes(context: AuditContext) -> list[CheckResult]:
  """Runner funkcjonalności F-04 dla silnika audytu."""
  return run_class_verification(context)
