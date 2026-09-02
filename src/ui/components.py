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


def render_metadata_evaluation_table(
  results: list[CheckResult],
  form_key: str = "f03_evaluation_form",
) -> tuple[bool, dict[str, CheckStatus], dict[str, str]]:
  """Renderuje tabelę metadanych z oceną PASS/FAIL i komentarzem w jednym widoku."""
  from src.features.f03_ifc_metadata.checks import F03_INFORMATIONAL_CHECK_IDS

  evaluations: dict[str, CheckStatus] = {}
  comments: dict[str, str] = {}

  with st.form(form_key):
    header_cols = st.columns([0.7, 1.6, 2.2, 1.0, 1.7])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Dane**")
    header_cols[2].markdown("**Wartość**")
    header_cols[3].markdown("**Ocena**")
    header_cols[4].markdown("**Komentarz**")

    for result in results:
      row_cols = st.columns([0.7, 1.6, 2.2, 1.0, 1.7])
      row_cols[0].write(result.check_id)
      row_cols[1].write(result.name)
      row_cols[2].write(result.message)

      if result.check_id in F03_INFORMATIONAL_CHECK_IDS:
        row_cols[3].write("Informacja")
        row_cols[4].write("—")
        continue

      current_status = result.status if result.status in (CheckStatus.PASS, CheckStatus.FAIL) else CheckStatus.PASS
      selected = row_cols[3].selectbox(
        "Ocena",
        options=["PASS", "FAIL"],
        index=0 if current_status == CheckStatus.PASS else 1,
        label_visibility="collapsed",
        key=f"{form_key}_{result.check_id}_status",
      )
      comment = row_cols[4].text_input(
        "Komentarz",
        value=result.comment or "",
        label_visibility="collapsed",
        key=f"{form_key}_{result.check_id}_comment",
      )

      evaluations[result.check_id] = CheckStatus.PASS if selected == "PASS" else CheckStatus.FAIL
      comments[result.check_id] = comment

    submitted = st.form_submit_button("Zatwierdź ocenę metadanych", use_container_width=True)

  return submitted, evaluations, comments


def render_metadata_evaluation_form(
  results: list[CheckResult],
  form_key: str = "f03_evaluation_form",
) -> tuple[bool, dict[str, CheckStatus], dict[str, str]]:
  """Kompatybilność wsteczna — przekierowuje do tabeli metadanych."""
  return render_metadata_evaluation_table(results, form_key)


def render_class_verification_table(rows: list[object]) -> None:
  """Wyświetla tabelę wynikową F-04."""
  if not rows:
    return

  table_rows = []
  for row in rows:
    allowed_label = "Tak" if row.is_allowed else "Nie"
    table_rows.append(
      {
        "Klasa IFC": row.class_name,
        "Liczba wystąpień": row.occurrence_count,
        "Czy klasa dopuszczalna": allowed_label,
      }
    )
  st.table(table_rows)


def render_locked_step_message(step: WorkflowStep) -> None:
  """Informuje użytkownika, że krok jest zablokowany."""
  st.warning(
    f"Krok „{WORKFLOW_STEP_LABELS[step]}” jest nieaktywny. "
    "Ukończ poprzedni krok, aby przejść dalej."
  )
