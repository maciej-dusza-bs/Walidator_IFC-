"""Wspólne komponenty interfejsu użytkownika."""

from __future__ import annotations

import streamlit as st

from src.core.models import TOTAL_WORKFLOW_STEPS, CheckResult, CheckStatus, WorkflowStep, WORKFLOW_STEP_LABELS

STATUS_ICONS: dict[CheckStatus, str] = {
  CheckStatus.PASS: "✅",
  CheckStatus.FAIL: "❌",
  CheckStatus.WARNING: "⚠️",
  CheckStatus.SKIPPED: "⏭️",
  CheckStatus.ERROR: "🛑",
}

STATUS_LABELS: dict[CheckStatus, str] = {
  CheckStatus.PASS: "PASS",
  CheckStatus.FAIL: "FAIL",
  CheckStatus.WARNING: "WARNING",
  CheckStatus.SKIPPED: "POMINIĘTO",
  CheckStatus.ERROR: "BŁĄD",
}


def render_progress_header(current_step: WorkflowStep) -> None:
  """Wyświetla numer bieżącego kroku i pasek postępu."""
  step_number = int(current_step)
  st.caption(f"Krok {step_number} z {TOTAL_WORKFLOW_STEPS}")
  st.progress(step_number / TOTAL_WORKFLOW_STEPS)
  st.subheader(WORKFLOW_STEP_LABELS[current_step])


def render_status_badge(status: CheckStatus) -> None:
  """Wyświetla status jako tekst z ikoną."""
  icon = STATUS_ICONS[status]
  label = STATUS_LABELS[status]
  st.markdown(f"{icon} **{label}**")


def render_error_message(title: str, reason: str, action: str) -> None:
  """Wyświetla komunikat błędu zgodny z wymaganiami UX."""
  st.error(
    f"**{title}**\n\n"
    f"**Co się stało:** {reason}\n\n"
    f"**Dlaczego blokuje dalszą pracę:** {reason}\n\n"
    f"**Co zrobić:** {action}"
  )


def render_step_navigation(
  current_step: WorkflowStep,
  can_go_back: bool,
  can_go_forward: bool,
) -> tuple[bool, bool]:
  """Renderuje przyciski nawigacji między krokami."""
  col_back, col_forward = st.columns(2)
  go_back = col_back.button("← Wstecz", disabled=not can_go_back, use_container_width=True)
  go_forward = col_forward.button("Dalej →", disabled=not can_go_forward, use_container_width=True)
  return go_back, go_forward


def render_check_results_table(results: list[CheckResult]) -> None:
  """Wyświetla tabelę wyników sprawdzeń."""
  if not results:
    return

  rows = []
  for result in results:
    icon = STATUS_ICONS[result.status]
    label = STATUS_LABELS[result.status]
    rows.append(
      {
        "ID": result.check_id,
        "Sprawdzenie": result.name,
        "Status": f"{icon} {label}",
        "Komunikat": result.message,
      }
    )
  st.table(rows)


def render_metadata_evaluation_form(
  results: list[CheckResult],
  form_key: str = "f03_evaluation_form",
) -> tuple[bool, dict[str, CheckStatus], dict[str, str]]:
  """Renderuje formularz oceny metadanych i zwraca decyzje użytkownika."""
  evaluation_options = ["Wybierz ocenę", "PASS", "FAIL"]
  evaluations: dict[str, CheckStatus] = {}
  comments: dict[str, str] = {}

  with st.form(form_key):
    for result in results:
      st.markdown(f"**{result.check_id} — {result.name}**")
      st.write(result.message)

      if result.status == CheckStatus.PASS:
        default_index = 1
      elif result.status == CheckStatus.FAIL:
        default_index = 2
      else:
        default_index = 0

      selected = st.radio(
        "Ocena użytkownika",
        options=evaluation_options,
        index=default_index,
        horizontal=True,
        key=f"{form_key}_{result.check_id}_status",
      )
      comment = st.text_input(
        "Komentarz (opcjonalnie)",
        value=result.comment or "",
        key=f"{form_key}_{result.check_id}_comment",
      )

      if selected == "PASS":
        evaluations[result.check_id] = CheckStatus.PASS
      elif selected == "FAIL":
        evaluations[result.check_id] = CheckStatus.FAIL

      comments[result.check_id] = comment
      st.divider()

    submitted = st.form_submit_button("Zatwierdź ocenę metadanych", use_container_width=True)

  return submitted, evaluations, comments


def render_locked_step_message(step: WorkflowStep) -> None:
  """Informuje użytkownika, że krok jest zablokowany."""
  st.warning(
    f"Krok „{WORKFLOW_STEP_LABELS[step]}” jest nieaktywny. "
    "Ukończ poprzedni krok, aby przejść dalej."
  )
