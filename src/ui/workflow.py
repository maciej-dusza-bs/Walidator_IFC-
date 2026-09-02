"""Nawigacja kroków i składanie interfejsu aplikacji."""

from __future__ import annotations

import streamlit as st

from src.core.audit_context import AuditContext
from src.core.audit_engine import run_feature
from src.core.models import CheckStatus, WorkflowStep
from src.features.f02_ifc_validation.service import (
  apply_v28_acceptance,
  can_proceed_after_f02,
)
from src.ui.components import (
  render_check_results_table,
  render_locked_step_message,
  render_progress_header,
  render_step_navigation,
)

SESSION_CONTEXT_KEY = "audit_context"


def _init_session_state() -> AuditContext:
  if SESSION_CONTEXT_KEY not in st.session_state:
    st.session_state[SESSION_CONTEXT_KEY] = AuditContext()
  return st.session_state[SESSION_CONTEXT_KEY]


def _save_context(context: AuditContext) -> None:
  st.session_state[SESSION_CONTEXT_KEY] = context


def _set_current_step(context: AuditContext, step: WorkflowStep) -> None:
  context.current_step = step
  _save_context(context)


def _render_start_step(context: AuditContext) -> None:
  st.markdown(
    """
    ### Witaj w Walidatorze IFC

    Aplikacja przeprowadzi Cię przez kontrolę pojedynczego modelu IFC (IFC2X3).

    **Przebieg kontroli:**
    1. **F-01** — instrukcja i rozpoczęcie pracy
    2. **F-02** — wczytanie i walidacja pliku IFC
    3. **F-03** — weryfikacja metadanych pliku i modelu
    4. **F-04** — weryfikacja dopuszczalnych klas IFC
    5. **F-05** — generowanie raportu kontroli

  **Zanim zaczniesz, przygotuj:**
  - plik IFC (od 10 B do 50 MB),
  - opcjonalnie plik XLSX z listą dopuszczalnych klas IFC (kolumna `IfcClass`).
    """
  )

  if not context.step1_acknowledged:
    if st.button("Rozpocznij kontrolę", type="primary", use_container_width=True):
      context.step1_acknowledged = True
      context.current_step = WorkflowStep.IFC_VALIDATION
      _save_context(context)
      st.rerun()
  else:
    st.success("Instrukcja została potwierdzona. Możesz przejść do walidacji pliku IFC.")


def _render_ifc_validation_step(context: AuditContext) -> None:
  st.markdown("Prześlij jeden plik IFC przeznaczony do kontroli.")
  uploaded_file = st.file_uploader(
    "Plik IFC",
    type=["ifc"],
    key="ifc_file_uploader",
    help="Dozwolony rozmiar: od 10 B do 50 MB.",
  )

  if uploaded_file is not None:
    context.ifc_filename = uploaded_file.name
    context.ifc_file_bytes = uploaded_file.getvalue()
    context.v28_accepted = False
    _save_context(context)

  col_validate, col_reset = st.columns(2)
  validate_clicked = col_validate.button(
    "Waliduj plik IFC",
    type="primary",
    use_container_width=True,
    disabled=context.ifc_file_bytes is None,
  )
  reset_clicked = col_reset.button("Wyczyść wyniki", use_container_width=True)

  if reset_clicked:
    context.f02_results = []
    context.f02_completed = False
    context.v28_accepted = False
    context.ifc_filename = None
    context.ifc_file_bytes = None
    context.ifc_model = None
    context.ifc_temp_path = None
    context.replace_feature_results({f"V-2.{index}" for index in range(1, 9)}, [])
    _save_context(context)
    st.rerun()

  if validate_clicked:
    results = run_feature(context, "F-02", "Walidacja IFC").checks
    context.f02_results = results
    context.f02_completed = can_proceed_after_f02(results, context.v28_accepted)
    _save_context(context)
    st.rerun()

  if context.f02_results:
    st.markdown("### Podsumowanie walidacji")
    render_check_results_table(context.f02_results)

    blocking_failed = any(
      result.status == CheckStatus.FAIL and result.check_id in {f"V-2.{index}" for index in range(1, 8)}
      for result in context.f02_results
    )
    if blocking_failed:
      st.error(
        "Walidacja nie powiodła się. Co najmniej jedno sprawdzenie V-2.1–V-2.7 zakończyło się statusem FAIL. "
        "Popraw plik lub wybierz inny model, a następnie uruchom walidację ponownie."
      )

    v28_result = next((result for result in context.f02_results if result.check_id == "V-2.8"), None)
    if v28_result and v28_result.status == CheckStatus.WARNING and not context.v28_accepted:
      st.warning(v28_result.message)
      if st.button("Akceptuję ostrzeżenie i chcę kontynuować", use_container_width=True):
        context.v28_accepted = True
        context.f02_results = apply_v28_acceptance(context.f02_results)
        context.replace_feature_results({f"V-2.{index}" for index in range(1, 9)}, context.f02_results)
        context.f02_completed = can_proceed_after_f02(context.f02_results, context.v28_accepted)
        _save_context(context)
        st.rerun()

    if context.f02_completed:
      st.success("Walidacja zakończona pomyślnie. Możesz przejść do weryfikacji metadanych (F-03).")


def _render_placeholder_step(feature_label: str) -> None:
  st.info(
    f"Funkcjonalność **{feature_label}** zostanie zaimplementowana w kolejnym etapie. "
    "Na tym etapie dostępna jest wyłącznie struktura workflow."
  )


def _render_step_content(context: AuditContext) -> None:
  step = context.current_step

  if step == WorkflowStep.START:
    _render_start_step(context)
    return

  if not context.is_step_unlocked(step):
    render_locked_step_message(step)
    return

  if step == WorkflowStep.IFC_VALIDATION:
    _render_ifc_validation_step(context)
  elif step == WorkflowStep.METADATA:
    _render_placeholder_step("F-03 — Metadane")
  elif step == WorkflowStep.IFC_CLASSES:
    _render_placeholder_step("F-04 — Klasy IFC")
  elif step == WorkflowStep.REPORT:
    _render_placeholder_step("F-05 — Raport")


def render_app() -> None:
  """Renderuje główny widok aplikacji."""
  st.set_page_config(page_title="Walidator IFC", layout="wide")
  context = _init_session_state()

  st.title("Walidator IFC")
  render_progress_header(context.current_step)
  _render_step_content(context)

  st.divider()
  can_go_back = int(context.current_step) > int(WorkflowStep.START)
  can_go_forward = (
    context.is_step_completed(context.current_step)
    and int(context.current_step) < int(WorkflowStep.REPORT)
  )
  go_back, go_forward = render_step_navigation(
    current_step=context.current_step,
    can_go_back=can_go_back,
    can_go_forward=can_go_forward,
  )

  if go_back:
    previous_step = WorkflowStep(int(context.current_step) - 1)
    _set_current_step(context, previous_step)
    st.rerun()

  if go_forward:
    next_step = WorkflowStep(int(context.current_step) + 1)
    if context.is_step_unlocked(next_step):
      _set_current_step(context, next_step)
      st.rerun()
