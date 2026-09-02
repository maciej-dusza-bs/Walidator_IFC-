"""Orkiestracja funkcjonalności F-03."""

from __future__ import annotations

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f03_ifc_metadata.checks import F03_CHECK_IDS, extract_metadata

F03_RESULT_IDS = set(F03_CHECK_IDS)
USER_EVALUATION_STATUSES = {CheckStatus.PASS, CheckStatus.FAIL}


def is_f03_complete(results: list[CheckResult]) -> bool:
  """Sprawdza, czy użytkownik ocenił wszystkie pozycje metadanych."""
  if len(results) != len(F03_CHECK_IDS):
    return False
  return all(result.status in USER_EVALUATION_STATUSES for result in results)


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
      merged_results.append(
        CheckResult(
          check_id=extracted.check_id,
          name=extracted.name,
          status=previous.status,
          message=extracted.message,
          value=extracted.value,
          comment=previous.comment,
        )
      )
    else:
      merged_results.append(extracted)

  return merged_results


def apply_user_evaluations(
  current_results: list[CheckResult],
  evaluations: dict[str, CheckStatus],
  comments: dict[str, str],
) -> list[CheckResult]:
  """Aktualizuje wyniki metadanych o oceny użytkownika."""
  updated_results: list[CheckResult] = []
  for result in current_results:
    selected_status = evaluations.get(result.check_id)
    if selected_status not in USER_EVALUATION_STATUSES:
      updated_results.append(result)
      continue

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
  context.f03_completed = is_f03_complete(results)
  return results
