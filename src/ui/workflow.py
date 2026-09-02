"""Nawigacja kroków i składanie interfejsu aplikacji."""

from __future__ import annotations

import streamlit as st

from src.core.audit_context import AuditContext
from src.core.models import WorkflowStep
from src.ui.components import (
  render_locked_step_message,
  render_progress_header,
  render_step_navigation,
)

SESSION_CONTEXT_KEY = "audit_context"


def _init_session_state() -> AuditContext:
  if SESSION_CONTEXT_KEY not in st.session_state:
    st.session_state[SESSION_CONTEXT_KEY] = AuditContext()
  return st.session_state[SESSION_CONTEXT_KEY]


def _set_current_step(context: AuditContext, step: WorkflowStep) -> None:
  context.current_step = step
  st.session_state[SESSION_CONTEXT_KEY] = context


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
      st.session_state[SESSION_CONTEXT_KEY] = context
      st.rerun()
  else:
    st.success("Instrukcja została potwierdzona. Możesz przejść do walidacji pliku IFC.")


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
    _render_placeholder_step("F-02 — Walidacja IFC")
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
