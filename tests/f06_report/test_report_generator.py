"""Testy generatora raportu F-06."""

from datetime import datetime
from io import BytesIO

import pandas as pd

from src.core.audit_context import AuditContext
from src.core.models import CheckResult, CheckStatus
from src.features.f04_ifc_classes.checks import ClassVerificationRow
from src.features.f06_report.report_generator import (
  F02_SHEET,
  F03_SHEET,
  F04_SHEET,
  SUMMARY_SHEET,
  build_report_filename,
  generate_report_bytes,
)


def _sample_context() -> AuditContext:
  context = AuditContext(
    ifc_filename="model_test.ifc",
    f04_skipped=False,
  )
  context.check_results = [
    CheckResult("V-2.1", "Plik został przesłany", CheckStatus.PASS, "OK"),
    CheckResult("V-2.8", "Schemat IFC2X3", CheckStatus.WARNING, "Inny schemat", comment="zaakceptowano"),
    CheckResult("V-3.1", "Nazwa pliku", CheckStatus.PASS, "model_test.ifc", comment="OK"),
    CheckResult("V-3.6", "Łączna liczba encji", CheckStatus.PASS, "120"),
    CheckResult("V-4.1", "Klasa IFC: IfcWall", CheckStatus.PASS, "Klasa dopuszczalna"),
    CheckResult("V-4.2", "Klasa IFC: IfcDoor", CheckStatus.FAIL, "Klasa niedopuszczalna"),
  ]
  context.f02_results = [check for check in context.check_results if check.check_id.startswith("V-2.")]
  context.f03_results = [check for check in context.check_results if check.check_id.startswith("V-3.")]
  context.f04_results = [check for check in context.check_results if check.check_id.startswith("V-4.")]
  context.f04_class_rows = [
    ClassVerificationRow(class_name="IfcWall", occurrence_count=3, is_allowed=True),
    ClassVerificationRow(class_name="IfcDoor", occurrence_count=1, is_allowed=False),
  ]
  context.f04_completed = True
  return context


def test_build_report_filename() -> None:
  assert build_report_filename("model_test.ifc") == "Raport_z_kontroli_model_test.xlsx"


def test_generate_report_contains_required_sheets() -> None:
  context = _sample_context()
  report_bytes, filename = generate_report_bytes(
    context,
    generated_at=datetime(2026, 3, 2, 12, 0, 0),
  )

  assert filename == "Raport_z_kontroli_model_test.xlsx"
  workbook = pd.ExcelFile(BytesIO(report_bytes))
  assert SUMMARY_SHEET in workbook.sheet_names
  assert F02_SHEET in workbook.sheet_names
  assert F03_SHEET in workbook.sheet_names
  assert F04_SHEET in workbook.sheet_names


def test_generate_report_summary_contains_overall_fail_status() -> None:
  context = _sample_context()
  report_bytes, _ = generate_report_bytes(context, generated_at=datetime(2026, 3, 2, 12, 0, 0))
  summary = pd.read_excel(BytesIO(report_bytes), sheet_name=SUMMARY_SHEET)
  checks_table = pd.read_excel(BytesIO(report_bytes), sheet_name=SUMMARY_SHEET, header=6)

  assert summary.iloc[0]["Wartość"] == "model_test.ifc"
  assert summary.iloc[2]["Wartość"] == "FAIL"
  assert "V-4.2" in checks_table["ID sprawdzenia"].astype(str).values


def test_generate_report_f04_sheet_contains_class_table() -> None:
  context = _sample_context()
  report_bytes, _ = generate_report_bytes(context)
  f04_sheet = pd.read_excel(BytesIO(report_bytes), sheet_name=F04_SHEET, header=2)

  assert "IfcWall" in f04_sheet["Klasa IFC"].astype(str).values
  assert 3 in f04_sheet["Liczba wystąpień"].values


def test_generate_report_marks_skipped_f04() -> None:
  context = _sample_context()
  context.f04_skipped = True
  context.f04_completed = False
  context.f04_class_rows = []
  context.check_results.append(
    CheckResult(
      check_id="F-04",
      name="Weryfikacja dopuszczalnych klas IFC",
      status=CheckStatus.SKIPPED,
      message="Pominięto",
    )
  )

  report_bytes, _ = generate_report_bytes(context)
  summary = pd.read_excel(BytesIO(report_bytes), sheet_name=SUMMARY_SHEET)

  assert summary.iloc[3]["Wartość"] == "F-04"
