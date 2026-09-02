"""Testy odczytu parametrów IFC."""

from pathlib import Path

import ifcopenshell

from src.io_adapters.ifc_parameter_reader import (
  EXPORT_COLUMNS,
  collect_entity_export_row,
  extract_entity_parameter_table,
  is_exportable_ifc_element,
  list_model_ifc_classes,
)


def test_list_model_ifc_classes_returns_sorted_unique_values(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))

  classes = list_model_ifc_classes(model)

  assert classes == sorted(classes)
  assert "IfcWall" in classes
  assert "IfcDoor" in classes
  assert "IfcProject" not in classes


def test_list_model_ifc_classes_excludes_ifc_feature_elements() -> None:
  model = ifcopenshell.file(schema="IFC2X3")
  model.create_entity("IfcWall")
  model.create_entity("IfcOpeningElement")
  model.create_entity("IfcProjectionElement")

  classes = list_model_ifc_classes(model)

  assert "IfcWall" in classes
  assert "IfcOpeningElement" not in classes
  assert "IfcProjectionElement" not in classes


def test_is_exportable_ifc_element() -> None:
  model = ifcopenshell.file(schema="IFC2X3")
  wall = model.create_entity("IfcWall")
  opening = model.create_entity("IfcOpeningElement")
  project = model.create_entity("IfcProject")

  assert is_exportable_ifc_element(wall) is True
  assert is_exportable_ifc_element(opening) is False
  assert is_exportable_ifc_element(project) is False


def test_collect_entity_export_row_reads_core_attributes() -> None:
  model = ifcopenshell.file(schema="IFC2X3")
  wall = model.create_entity(
    "IfcWall",
    Name="Test Wall",
    GlobalId="0abc1234567890abcdefghij",
    ObjectType="KO_Wall",
  )

  row = collect_entity_export_row(wall)

  assert row == {
    "Name": "Test Wall",
    "GlobalID": "0abc1234567890abcdefghij",
    "ObjectType": "KO_Wall",
    "IfcClass": "IfcWall",
  }


def test_extract_entity_parameter_table_filters_selected_classes(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))

  columns, rows = extract_entity_parameter_table(model, ["IfcWall"])

  assert columns == EXPORT_COLUMNS
  assert rows
  assert all(row["IfcClass"] == "IfcWall" for row in rows)
  assert not any(row["IfcClass"] == "IfcDoor" for row in rows)


def test_extract_entity_parameter_table_excludes_ifc_feature_elements() -> None:
  model = ifcopenshell.file(schema="IFC2X3")
  model.create_entity("IfcWall", Name="Wall")
  model.create_entity("IfcOpeningElement", Name="Opening")

  _, rows = extract_entity_parameter_table(model, ["IfcWall", "IfcOpeningElement"])

  assert len(rows) == 1
  assert rows[0]["IfcClass"] == "IfcWall"


def test_extract_entity_parameter_table_reports_progress(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  progress_updates: list[tuple[int, int]] = []

  extract_entity_parameter_table(
    model,
    list_model_ifc_classes(model),
    progress_callback=lambda current, total: progress_updates.append((current, total)),
  )

  assert progress_updates
  assert progress_updates[-1] == (len(list(model)), len(list(model)))
