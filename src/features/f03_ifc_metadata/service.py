"""Orkiestracja funkcjonalności F-03."""

from __future__ import annotations

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f03_ifc_metadata.checks import (
  F03_CHECK_IDS,
  F03_EVALUABLE_CHECK_IDS,
  F03_INFORMATIONAL_CHECK_IDS,
  extract_metadata,
)

F03_RESULT_IDS = set(F03_CHECK_IDS)
USER_EVALUATION_STATUSES = {CheckStatus.PASS, CheckStatus.FAIL}


def is_f03_complete(results: list[CheckResult]) -> bool:
  """Sprawdza, czy użytkownik ocenił wszystkie wymagane pozycje metadanych."""
  results_by_id = {result.check_id: result for result in results}
  for check_id in F03_EVALUABLE_CHECK_IDS:
    result = results_by_id.get(check_id)
    if result is None or result.status not in USER_EVALUATION_STATUSES:
      return False
  return True


def _default_metadata_status(check_id: str) -> CheckStatus:
  if check_id in F03_INFORMATIONAL_CHECK_IDS:
    return CheckStatus.PASS
  return CheckStatus.PASS


def merge_user_evaluations(
  extracted_results: list[CheckResult],
  previous_results: list[CheckResult],
) -> list[CheckResult]:
  """Zachowuje oceny użytkownika przy ponownej ekstrakcji metadanych."""
  previous_by_id = {result.check_id: result for result in previous_results}
  merged_results: list[CheckResult] = []

  for extracted in extracted_results:
    previous = previous_by_id.get(extracted.check_id)
    if previous and previous.status in USER_EVALUATION_STATUSES:
      status = previous.status
      comment = previous.comment
    else:
      status = _default_metadata_status(extracted.check_id)
      comment = None

    merged_results.append(
      CheckResult(
        check_id=extracted.check_id,
        name=extracted.name,
        status=status,
        message=extracted.message,
        value=extracted.value,
        comment=comment,
      )
    )

  return merged_results


def apply_user_evaluations(
  current_results: list[CheckResult],
  evaluations: dict[str, CheckStatus],
  comments: dict[str, str],
) -> list[CheckResult]:
  """Aktualizuje wyniki metadanych o oceny użytkownika."""
  updated_results: list[CheckResult] = []
  for result in current_results:
    if result.check_id in F03_INFORMATIONAL_CHECK_IDS:
      updated_results.append(
        CheckResult(
          check_id=result.check_id,
          name=result.name,
          status=CheckStatus.PASS,
          message=result.message,
          value=result.value,
          comment=None,
        )
      )
      continue

    selected_status = evaluations.get(result.check_id, CheckStatus.PASS)
    if selected_status not in USER_EVALUATION_STATUSES:
      selected_status = CheckStatus.PASS

    comment = comments.get(result.check_id, "").strip() or None
    updated_results.append(
      CheckResult(
        check_id=result.check_id,
        name=result.name,
        status=selected_status,
        message=result.message,
        value=result.value,
        comment=comment,
      )
    )
  return updated_results


def run_f03_metadata(context: AuditContext) -> list[CheckResult]:
  """Ekstrahuje metadane i aktualizuje kontekst audytu."""
  extracted = extract_metadata(
    filename=context.ifc_filename,
    file_bytes=context.ifc_file_bytes,
    model=context.ifc_model,
  )
  results = merge_user_evaluations(extracted, context.f03_results)
  context.replace_feature_results(F03_RESULT_IDS, results)
  context.f03_results = results
  return results
