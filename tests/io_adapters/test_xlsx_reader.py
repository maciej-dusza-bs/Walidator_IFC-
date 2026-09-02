"""Testy adaptera odczytu XLSX."""

from pathlib import Path

from src.io_adapters.xlsx_reader import (
  list_sheet_columns,
  list_xlsx_sheet_names,
  read_allowed_ifc_classes,
)


def test_list_xlsx_sheet_names(generated_xlsx_fixtures: dict[str, Path]) -> None:
  multi_sheet_path = generated_xlsx_fixtures["multi_sheet"]
  sheet_info = list_xlsx_sheet_names(multi_sheet_path.read_bytes())

  assert sheet_info.error_message is None
  assert sheet_info.sheet_names == ["Inny", "Klasy"]


def test_list_sheet_columns(generated_xlsx_fixtures: dict[str, Path]) -> None:
  multi_column_path = generated_xlsx_fixtures["multi_column"]
  columns_info = list_sheet_columns(multi_column_path.read_bytes(), "Klasy")

  assert columns_info.error_message is None
  assert columns_info.columns == ["Opis", "IfcClass", "Kod"]


def test_read_allowed_ifc_classes_removes_duplicates_and_whitespace(
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  valid_path = generated_xlsx_fixtures["valid"]
  result = read_allowed_ifc_classes(valid_path.read_bytes(), "Klasy")

  assert result.error_message is None
  assert result.classes == ["IfcDoor", "IfcWall"]
  assert result.selected_column == "IfcClass"


def test_read_allowed_ifc_classes_requires_column_for_multi_column_sheet(
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  multi_column_path = generated_xlsx_fixtures["multi_column"]
  result = read_allowed_ifc_classes(multi_column_path.read_bytes(), "Klasy")

  assert result.classes == []
  assert result.error_message is not None
  assert result.format_hint is not None


def test_read_allowed_ifc_classes_with_selected_column(
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  multi_column_path = generated_xlsx_fixtures["multi_column"]
  result = read_allowed_ifc_classes(multi_column_path.read_bytes(), "Klasy", "IfcClass")

  assert result.error_message is None
  assert result.classes == ["IfcDoor", "IfcWall"]


def test_read_allowed_ifc_classes_empty_column(generated_xlsx_fixtures: dict[str, Path]) -> None:
  empty_path = generated_xlsx_fixtures["empty"]
  result = read_allowed_ifc_classes(empty_path.read_bytes(), "Klasy", "IfcClass")

  assert result.classes == []
  assert result.error_message is not None
  assert result.format_hint is not None


def test_read_allowed_ifc_classes_invalid_column(
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  missing_column_path = generated_xlsx_fixtures["missing_column"]
  result = read_allowed_ifc_classes(missing_column_path.read_bytes(), "Klasy", "BrakujacaKolumna")

  assert result.classes == []
  assert "BrakujacaKolumna" in result.error_message


def test_list_sheet_columns_detects_offset_header(generated_xlsx_fixtures: dict[str, Path]) -> None:
  offset_header_path = generated_xlsx_fixtures["offset_header"]
  columns_info = list_sheet_columns(offset_header_path.read_bytes(), "Arkusz1")

  assert columns_info.error_message is None
  assert columns_info.columns == ["Komponent", "IfcType", "IfcClass"]


def test_read_allowed_ifc_classes_splits_combined_values(
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  offset_header_path = generated_xlsx_fixtures["offset_header"]
  result = read_allowed_ifc_classes(offset_header_path.read_bytes(), "Arkusz1", "IfcClass")

  assert result.error_message is None
  assert result.classes == ["IfcFooting", "IfcWall", "IfcWallStandardCase"]

