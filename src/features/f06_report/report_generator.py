"""Generowanie raportu kontroli w formacie XLSX."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, compute_overall_status

SUMMARY_SHEET = "Podsumowanie"
F02_SHEET = "F-02 Walidacja IFC"
F03_SHEET = "F-03 Weryfikacja Metadanych"
F04_SHEET = "F-04 Weryfikacja Klas IFC"

F03_TITLE = "F-03 Weryfikacja metadanych pliku i modelu"
F04_TITLE = "F-04 Weryfikacja dopuszczalnych klas IFC"


def build_report_filename(ifc_filename: str | None) -> str:
  """Buduje nazwę pliku raportu zgodnie ze specyfikacją."""
  if not ifc_filename:
    return "Raport_z_kontroli.xlsx"
  stem = Path(ifc_filename).stem
  return f"Raport_z_kontroli_{stem}.xlsx"


def _feature_id_for_check(check_id: str) -> str:
  if check_id.startswith("V-2."):
    return "F-02"
  if check_id.startswith("V-3."):
    return "F-03"
  if check_id.startswith("V-4.") or check_id == "F-04":
    return "F-04"
  return "Inne"


def _checks_to_rows(checks: list[CheckResult]) -> list[dict[str, str]]:
  rows = []
  for check in checks:
    rows.append({
      "ID sprawdzenia": check.check_id,
      "Sprawdzenie": check.name,
      "Status": check.status.value,
      "Wartość / komunikat": check.message,
      "Komentarz użytkownika": check.comment or "",
    })
  return rows


def _write_title_and_table(
  writer: pd.ExcelWriter,
  sheet_name: str,
  title: str,
  rows: list[dict[str, Any]],
  columns: list[str],
) -> None:
  worksheet_frame = pd.DataFrame([[title]], columns=["Tytuł"])
  worksheet_frame.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
  if rows:
    pd.DataFrame(rows, columns=columns).to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)
  else:
    pd.DataFrame([{"Informacja": "Brak wyników do wyświetlenia."}]).to_excel(
      writer,
      sheet_name=sheet_name,
      index=False,
      startrow=2,
    )


def _write_summary_sheet(
  writer: pd.ExcelWriter,
  context: AuditContext,
  generated_at: datetime,
) -> None:
  overall_status = compute_overall_status(context.all_results())
  skipped_features = []
  if context.f04_skipped:
    skipped_features.append("F-04")

  header_rows = [
    {"Pole": "Nazwa kontrolowanego pliku", "Wartość": context.ifc_filename or "Brak danych"},
    {"Pole": "Data i godzina kontroli", "Wartość": generated_at.strftime("%Y-%m-%d %H:%M:%S")},
    {"Pole": "Status całej kontroli", "Wartość": overall_status.value},
    {
      "Pole": "Pominięte funkcjonalności",
      "Wartość": ", ".join(skipped_features) if skipped_features else "Brak",
    },
  ]
  pd.DataFrame(header_rows).to_excel(writer, sheet_name=SUMMARY_SHEET, index=False, startrow=0)

  summary_checks = []
  for check in context.all_results():
    summary_checks.append(
      {
        "Funkcjonalność": _feature_id_for_check(check.check_id),
        "ID sprawdzenia": check.check_id,
        "Sprawdzenie": check.name,
        "Status": check.status.value,
        "Komentarz użytkownika": check.comment or "",
      }
    )

  pd.DataFrame(summary_checks).to_excel(writer, sheet_name=SUMMARY_SHEET, index=False, startrow=6)


def _write_f02_sheet(writer: pd.ExcelWriter, checks: list[CheckResult]) -> None:
  f02_checks = [check for check in checks if check.check_id.startswith("V-2.")]
  _write_title_and_table(
    writer,
    F02_SHEET,
    "F-02 Walidacja IFC",
    _checks_to_rows(f02_checks),
    ["ID sprawdzenia", "Sprawdzenie", "Status", "Wartość / komunikat", "Komentarz użytkownika"],
  )


def _write_f03_sheet(writer: pd.ExcelWriter, checks: list[CheckResult]) -> None:
  f03_checks = [check for check in checks if check.check_id.startswith("V-3.")]
  _write_title_and_table(
    writer,
    F03_SHEET,
    F03_TITLE,
    _checks_to_rows(f03_checks),
    ["ID sprawdzenia", "Sprawdzenie", "Status", "Wartość / komunikat", "Komentarz użytkownika"],
  )


def _write_f04_sheet(writer: pd.ExcelWriter, context: AuditContext) -> None:
  if context.f04_class_rows:
    rows = [
      {
        "Klasa IFC": row.class_name,
        "Liczba wystąpień": row.occurrence_count,
        "Czy klasa dopuszczalna": "Tak" if row.is_allowed else "Nie",
      }
      for row in context.f04_class_rows
    ]
    columns = ["Klasa IFC", "Liczba wystąpień", "Czy klasa dopuszczalna"]
    _write_title_and_table(writer, F04_SHEET, F04_TITLE, rows, columns)
    return

  f04_checks = [
    check for check in context.all_results()
    if check.check_id.startswith("V-4.") or check.check_id == "F-04"
  ]
  _write_title_and_table(
    writer,
    F04_SHEET,
    F04_TITLE,
    _checks_to_rows(f04_checks),
    ["ID sprawdzenia", "Sprawdzenie", "Status", "Wartość / komunikat", "Komentarz użytkownika"],
  )


def generate_report_bytes(
  context: AuditContext,
  generated_at: datetime | None = None,
) -> tuple[bytes, str]:
  """Generuje raport XLSX w pamięci i zwraca bajty oraz nazwę pliku."""
  timestamp = generated_at or datetime.now()
  filename = build_report_filename(context.ifc_filename)
  buffer = BytesIO()

  with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    _write_summary_sheet(writer, context, timestamp)
    _write_f02_sheet(writer, context.all_results())
    _write_f03_sheet(writer, context.f03_results or [
      check for check in context.all_results() if check.check_id.startswith("V-3.")
    ])
    _write_f04_sheet(writer, context)

  buffer.seek(0)
  return buffer.getvalue(), filename
