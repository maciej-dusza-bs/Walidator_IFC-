"""Eksport parametrów encji IFC do pliku XLSX."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd

from src.io_adapters.ifc_parameter_reader import extract_entity_parameter_table

EXPORT_SHEET_NAME = "Parametry IFC"


def build_parameter_export_filename(ifc_filename: str | None) -> str:
  """Buduje nazwę pliku eksportu parametrów."""
  if not ifc_filename:
    return "Eksport_parametrow.xlsx"
  stem = Path(ifc_filename).stem
  return f"Eksport_parametrow_{stem}.xlsx"


def export_parameters_xlsx(
  model: Any,
  ifc_filename: str | None = None,
  selected_classes: list[str] | None = None,
  progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[bytes, str]:
  """Eksportuje parametry wybranych klas IFC do pliku XLSX w pamięci."""
  if not selected_classes:
    raise ValueError("Wybierz co najmniej jedną klasę IFC do eksportu.")

  columns, rows = extract_entity_parameter_table(
    model,
    selected_classes,
    progress_callback=progress_callback,
  )
  dataframe = pd.DataFrame(rows, columns=columns)
  buffer = BytesIO()
  with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    dataframe.to_excel(writer, sheet_name=EXPORT_SHEET_NAME, index=False)
  buffer.seek(0)
  return buffer.getvalue(), build_parameter_export_filename(ifc_filename)
