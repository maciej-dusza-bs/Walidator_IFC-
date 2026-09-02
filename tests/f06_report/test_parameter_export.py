"""Testy eksportu parametrów IFC."""

from io import BytesIO
from pathlib import Path

import ifcopenshell
import pandas as pd

from src.features.f06_report.parameter_export import (
  EXPORT_SHEET_NAME,
  build_parameter_export_filename,
  export_parameters_xlsx,
)
from src.io_adapters.ifc_parameter_reader import (
  EXPORT_COLUMNS,
  is_exportable_ifc_element,
  list_model_ifc_classes,
)


def test_build_parameter_export_filename() -> None:
  assert build_parameter_export_filename("model_test.ifc") == "Eksport_parametrow_model_test.xlsx"


def test_export_parameters_xlsx_creates_workbook(generated_ifc_fixtures: dict[str, Path]) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  selected_classes = list_model_ifc_classes(model)

  export_bytes, filename = export_parameters_xlsx(model, products_path.name, selected_classes)
  workbook = pd.ExcelFile(BytesIO(export_bytes))

  assert filename == "Eksport_parametrow_with_products.xlsx"
  assert EXPORT_SHEET_NAME in workbook.sheet_names

  dataframe = pd.read_excel(BytesIO(export_bytes), sheet_name=EXPORT_SHEET_NAME)
  assert list(dataframe.columns) == EXPORT_COLUMNS
  exportable_count = sum(1 for entity in model if is_exportable_ifc_element(entity))
  assert len(dataframe) == exportable_count


def test_export_parameters_xlsx_requires_selected_classes(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))

  try:
    export_parameters_xlsx(model, products_path.name, [])
  except ValueError as error:
    assert "klasę IFC" in str(error)
  else:
    raise AssertionError("Oczekiwano ValueError przy pustej liście klas")
