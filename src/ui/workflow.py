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
from src.features.f03_ifc_metadata.checks import F03_CHECK_IDS
from src.features.f03_ifc_metadata.service import apply_user_evaluations, is_f03_complete
from src.features.f04_ifc_classes.service import (
  collect_f04_check_ids,
  load_allowed_classes,
  run_class_verification,
  skip_f04,
)
from src.io_adapters.xlsx_reader import (
  IFC_CLASS_COLUMN,
  XLSX_FORMAT_HINT,
  list_sheet_columns,
  list_xlsx_sheet_names,
)
from src.ui.components import (
  render_check_results_table,
  render_class_verification_table,
  render_locked_step_message,
  render_metadata_evaluation_table,
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


F03_RESULT_IDS = set(F03_CHECK_IDS)


def _reset_f03_state(context: AuditContext) -> None:
  context.f03_results = []
  context.f03_completed = False
  context.replace_feature_results(F03_RESULT_IDS, [])


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
    _reset_f03_state(context)
    _reset_f04_state(context)
    _save_context(context)
    st.rerun()

  if validate_clicked:
    _reset_f03_state(context)
    _reset_f04_state(context)
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


def _render_metadata_step(context: AuditContext) -> None:
  if context.ifc_model is None:
    st.error(
      "Brak otwartego modelu IFC. Wróć do kroku F-02 i poprawnie zwaliduj plik, "
      "aby kontynuować weryfikację metadanych."
    )
    return

  if not context.f03_results:
    context.f03_results = run_feature(context, "F-03", "Weryfikacja metadanych").checks
    _save_context(context)

  st.markdown(
    "Zweryfikuj metadane pliku i modelu. Dla pozycji V-3.1–V-3.5 wybierz **PASS** lub **FAIL** "
    "(domyślnie PASS). Pozycja V-3.6 jest wyłącznie informacyjna."
  )

  submitted, evaluations, comments = render_metadata_evaluation_table(context.f03_results)

  if submitted:
    if len(evaluations) != len([result for result in context.f03_results if result.check_id != "V-3.6"]):
      st.error(
        "Nie można przejść dalej, ponieważ nie wszystkie wymagane pozycje mają przypisaną ocenę. "
        "Uzupełnij oceny dla pozycji V-3.1–V-3.5."
      )
      return

    updated_results = apply_user_evaluations(context.f03_results, evaluations, comments)
    context.f03_results = updated_results
    context.replace_feature_results(F03_RESULT_IDS, updated_results)
    context.f03_completed = is_f03_complete(updated_results)
    _save_context(context)
    st.rerun()

  if context.f03_completed:
    st.success("Ocena metadanych została zapisana. Możesz przejść do weryfikacji klas IFC (F-04).")


def _reset_f04_state(context: AuditContext) -> None:
  old_ids = collect_f04_check_ids(context.f04_results)
  context.f04_xlsx_filename = None
  context.f04_xlsx_bytes = None
  context.f04_sheet_names = []
  context.f04_selected_sheet = None
  context.f04_sheet_columns = []
  context.f04_selected_column = None
  context.f04_allowed_classes = []
  context.f04_results = []
  context.f04_class_rows = []
  context.f04_completed = False
  context.f04_skipped = False
  context.f04_has_failures = False
  context.f04_xlsx_error = None
  context.f04_xlsx_format_hint = None
  context.f04_load_success = None
  context.replace_feature_results(old_ids, [])


def _refresh_f04_sheet_columns(context: AuditContext) -> None:
  if context.f04_xlsx_bytes is None or context.f04_selected_sheet is None:
    context.f04_sheet_columns = []
    return

  columns_info = list_sheet_columns(context.f04_xlsx_bytes, context.f04_selected_sheet)
  if columns_info.error_message:
    context.f04_sheet_columns = []
    context.f04_xlsx_error = columns_info.error_message
    context.f04_xlsx_format_hint = columns_info.format_hint
    context.f04_load_success = None
    return

  context.f04_sheet_columns = columns_info.columns
  if len(columns_info.columns) == 1:
    context.f04_selected_column = columns_info.columns[0]
  elif context.f04_selected_column not in columns_info.columns:
    if IFC_CLASS_COLUMN in columns_info.columns:
      context.f04_selected_column = IFC_CLASS_COLUMN
    else:
      context.f04_selected_column = None


def _handle_f04_file_upload(context: AuditContext, uploaded_xlsx) -> None:
  if uploaded_xlsx is None:
    return

  new_bytes = uploaded_xlsx.getvalue()
  new_name = uploaded_xlsx.name
  file_changed = new_name != context.f04_xlsx_filename or new_bytes != context.f04_xlsx_bytes

  if file_changed:
    context.f04_xlsx_filename = new_name
    context.f04_xlsx_bytes = new_bytes
    context.f04_allowed_classes = []
    context.f04_results = []
    context.f04_class_rows = []
    context.f04_completed = False
    context.f04_skipped = False
    context.f04_xlsx_error = None
    context.f04_xlsx_format_hint = None
    context.f04_load_success = None
    context.f04_selected_sheet = None
    context.f04_selected_column = None
    context.f04_sheet_columns = []

  sheet_info = list_xlsx_sheet_names(context.f04_xlsx_bytes)
  if sheet_info.error_message:
    context.f04_sheet_names = []
    context.f04_selected_sheet = None
    context.f04_sheet_columns = []
    context.f04_xlsx_error = sheet_info.error_message
    context.f04_xlsx_format_hint = sheet_info.format_hint
    context.f04_load_success = None
    return

  context.f04_sheet_names = sheet_info.sheet_names
  if context.f04_selected_sheet not in context.f04_sheet_names:
    context.f04_selected_sheet = context.f04_sheet_names[0]
  _refresh_f04_sheet_columns(context)


def _render_ifc_classes_step(context: AuditContext) -> None:
  if context.ifc_model is None:
    st.error(
      "Brak otwartego modelu IFC. Wróć do kroku F-02 i poprawnie zwaliduj plik, "
      "aby kontynuować weryfikację klas."
    )
    return

  with st.expander("Jak powinien wyglądać plik XLSX?", expanded=False):
    st.markdown(XLSX_FORMAT_HINT)

  st.markdown(
    "Prześlij plik XLSX z listą dopuszczalnych klas IFC. "
    "Jeśli arkusz ma wiele kolumn, wskaż kolumnę z nazwami klas."
  )
  uploaded_xlsx = st.file_uploader(
    "Plik XLSX z listą klas",
    type=["xlsx"],
    key="ifc_classes_xlsx_uploader",
  )
  _handle_f04_file_upload(context, uploaded_xlsx)

  if context.f04_xlsx_filename:
    st.caption(f"Wczytany plik: `{context.f04_xlsx_filename}`")

  if context.f04_xlsx_error:
    st.error(context.f04_xlsx_error)
    if context.f04_xlsx_format_hint:
      st.info(context.f04_xlsx_format_hint)

  if context.f04_load_success:
    st.success(context.f04_load_success)

  selected_sheet = context.f04_selected_sheet
  if context.f04_sheet_names:
    previous_sheet = context.f04_selected_sheet
    selected_sheet = st.selectbox(
      "Wybierz arkusz",
      options=context.f04_sheet_names,
      index=context.f04_sheet_names.index(context.f04_selected_sheet)
      if context.f04_selected_sheet in context.f04_sheet_names
      else 0,
      key="f04_sheet_select",
    )
    if selected_sheet != previous_sheet:
      context.f04_selected_sheet = selected_sheet
      context.f04_allowed_classes = []
      context.f04_load_success = None
      context.f04_xlsx_error = None
      context.f04_xlsx_format_hint = None
      _refresh_f04_sheet_columns(context)
    else:
      context.f04_selected_sheet = selected_sheet

  selected_column = context.f04_selected_column
  if len(context.f04_sheet_columns) > 1:
    column_options = ["— wybierz kolumnę —", *context.f04_sheet_columns]
    default_index = 0
    if context.f04_selected_column in context.f04_sheet_columns:
      default_index = column_options.index(context.f04_selected_column)

    selected_column_label = st.selectbox(
      "Wybierz kolumnę z listą klas IFC",
      options=column_options,
      index=default_index,
      key="f04_column_select",
    )
    selected_column = (
      None if selected_column_label == "— wybierz kolumnę —" else selected_column_label
    )
    context.f04_selected_column = selected_column
  elif len(context.f04_sheet_columns) == 1:
    selected_column = context.f04_sheet_columns[0]
    context.f04_selected_column = selected_column
    st.caption(f"Używana kolumna: `{selected_column}`")

  _save_context(context)

  needs_column_selection = len(context.f04_sheet_columns) > 1
  can_load_classes = (
    context.f04_xlsx_bytes is not None
    and selected_sheet is not None
    and (not needs_column_selection or selected_column is not None)
  )

  col_load, col_analyze = st.columns(2)
  load_clicked = col_load.button(
    "Wczytaj listę klas",
    type="primary",
    use_container_width=True,
    disabled=not can_load_classes,
  )
  analyze_clicked = col_analyze.button(
    "Uruchom sprawdzenie klas",
    use_container_width=True,
    disabled=not context.f04_allowed_classes,
  )

  if load_clicked and can_load_classes:
    load_result = load_allowed_classes(
      context.f04_xlsx_bytes,
      selected_sheet,
      selected_column,
    )
    if load_result.error_message:
      context.f04_allowed_classes = []
      context.f04_xlsx_error = load_result.error_message
      context.f04_xlsx_format_hint = load_result.format_hint
      context.f04_load_success = None
    else:
      context.f04_allowed_classes = load_result.classes
      context.f04_selected_column = load_result.selected_column
      context.f04_xlsx_error = None
      context.f04_xlsx_format_hint = None
      context.f04_completed = False
      context.f04_skipped = False
      context.f04_results = []
      context.f04_class_rows = []
      context.f04_load_success = (
        f"Wczytano {len(load_result.classes)} dopuszczalnych klas IFC z arkusza "
        f"`{selected_sheet}`, kolumna `{load_result.selected_column}`."
      )
    _save_context(context)
    st.rerun()

  if analyze_clicked:
    run_class_verification(context)
    context.f04_load_success = None
    _save_context(context)
    st.rerun()

  if context.f04_allowed_classes and not context.f04_load_success:
    st.info(
      f"Lista {len(context.f04_allowed_classes)} klas jest gotowa do sprawdzenia. "
      "Kliknij „Uruchom sprawdzenie klas”."
    )

  if context.f04_class_rows:
    st.markdown("### Tabela wynikowa klas IFC")
    render_class_verification_table(context.f04_class_rows)
    render_check_results_table(context.f04_results)

    if context.f04_has_failures:
      st.error(
        "W modelu występuje co najmniej jedna niedopuszczalna klasa IFC. "
        "Funkcjonalność F-04 ma status FAIL."
      )
    elif context.f04_completed:
      st.success("Sprawdzenie klas zakończone. Wszystkie występujące klasy są dopuszczalne.")

  st.divider()
  st.markdown("**Jeśli nie możesz wczytać pliku XLSX:**")
  action_col_skip, action_col_end = st.columns(2)

  if action_col_skip.button("Pomiń F-04 i przejdź dalej", use_container_width=True):
    skip_f04(context)
    _save_context(context)
    st.rerun()

  if action_col_end.button("Zakończ kontrolę i przejdź do raportu", use_container_width=True):
    skip_f04(
      context,
      message="Funkcjonalność F-04 została pominięta. Kontrola przechodzi do raportu częściowego.",
    )
    context.current_step = WorkflowStep.REPORT
    _save_context(context)
    st.rerun()

  if context.f04_skipped and not context.f04_class_rows:
    st.info(context.f04_results[0].message if context.f04_results else "F-04 została pominięta.")


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
    _render_metadata_step(context)
  elif step == WorkflowStep.IFC_CLASSES:
    _render_ifc_classes_step(context)
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
