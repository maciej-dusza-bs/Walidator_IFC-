"""Wspólna konfiguracja pytest."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
  """Zwraca ścieżkę do katalogu z plikami testowymi."""
  return FIXTURES_DIR


@pytest.fixture(scope="session")
def generated_ifc_fixtures(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
  """Generuje pliki IFC do testów za pomocą IfcOpenShell."""
  import ifcopenshell

  base_dir = tmp_path_factory.mktemp("ifc_generated")

  valid_model = ifcopenshell.file(schema="IFC2X3")
  valid_model.create_entity("IfcProject", Name="Test Project")
  valid_path = base_dir / "valid_ifc2x3.ifc"
  valid_model.write(str(valid_path))

  multi_model = ifcopenshell.file(schema="IFC2X3")
  multi_model.create_entity("IfcProject", Name="Project A")
  multi_model.create_entity("IfcProject", Name="Project B")
  multi_path = base_dir / "multi_project.ifc"
  multi_model.write(str(multi_path))

  no_project_model = ifcopenshell.file(schema="IFC2X3")
  no_project_path = base_dir / "no_project.ifc"
  no_project_model.write(str(no_project_path))

  ifc4_model = ifcopenshell.file(schema="IFC4")
  ifc4_model.create_entity("IfcProject", Name="IFC4 Project")
  ifc4_path = base_dir / "ifc4_model.ifc"
  ifc4_model.write(str(ifc4_path))

  return {
    "valid": valid_path,
    "multi_project": multi_path,
    "no_project": no_project_path,
    "ifc4": ifc4_path,
    "with_metadata": _create_metadata_model(base_dir),
    "with_products": _create_products_model(base_dir),
  }


def _create_products_model(base_dir: Path) -> Path:
  import ifcopenshell

  model = ifcopenshell.file(schema="IFC2X3")
  model.create_entity("IfcProject", Name="Test Project")
  model.create_entity("IfcWall")
  model.create_entity("IfcDoor")
  products_path = base_dir / "with_products.ifc"
  model.write(str(products_path))
  return products_path


@pytest.fixture(scope="session")
def generated_xlsx_fixtures(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
  """Generuje pliki XLSX do testów F-04."""
  import pandas as pd

  base_dir = tmp_path_factory.mktemp("xlsx_generated")

  valid_path = base_dir / "classes_valid.xlsx"
  pd.DataFrame({"IfcClass": ["IfcWall", "IfcDoor", " IfcWall ", ""]}).to_excel(
    valid_path,
    sheet_name="Klasy",
    index=False,
  )

  multi_sheet_path = base_dir / "classes_multi_sheet.xlsx"
  with pd.ExcelWriter(multi_sheet_path, engine="openpyxl") as writer:
    pd.DataFrame({"Other": ["x"]}).to_excel(writer, sheet_name="Inny", index=False)
    pd.DataFrame({"IfcClass": ["IfcWall"]}).to_excel(writer, sheet_name="Klasy", index=False)

  missing_column_path = base_dir / "classes_missing_column.xlsx"
  pd.DataFrame(
    {
      "Opis": ["ściana"],
      "ClassName": ["IfcWall"],
    }
  ).to_excel(missing_column_path, sheet_name="Klasy", index=False)

  empty_path = base_dir / "classes_empty.xlsx"
  pd.DataFrame({"IfcClass": ["", "   "]}).to_excel(
    empty_path,
    sheet_name="Klasy",
    index=False,
  )

  multi_column_path = base_dir / "classes_multi_column.xlsx"
  pd.DataFrame(
    {
      "Opis": ["ściana", "drzwi"],
      "IfcClass": ["IfcWall", "IfcDoor"],
      "Kod": ["W1", "D1"],
    }
  ).to_excel(multi_column_path, sheet_name="Klasy", index=False)

  offset_header_path = base_dir / "classes_offset_header.xlsx"
  offset_rows = [
    [None, None, None, None],
    [None, None, None, None],
    [None, "MODEL BRANŻY", None, None],
    [None, "Komponent", "IfcType", "IfcClass"],
    [None, "Płyta", "KO_Płyta", "IfcFooting"],
    [None, "Ściana", "KO_Ściana", "IfcWall / IfcWallStandardCase"],
  ]
  pd.DataFrame(offset_rows).to_excel(offset_header_path, sheet_name="Arkusz1", header=False, index=False)

  return {
    "valid": valid_path,
    "multi_sheet": multi_sheet_path,
    "missing_column": missing_column_path,
    "empty": empty_path,
    "multi_column": multi_column_path,
    "offset_header": offset_header_path,
  }


def _create_metadata_model(base_dir: Path) -> Path:
  import ifcopenshell

  model = ifcopenshell.file(schema="IFC2X3")
  model.create_entity("IfcProject", Name="Test Project")
  model.create_entity("IfcBuilding", Name="Building A")
  model.create_entity("IfcSite", Name="Site A")
  metadata_path = base_dir / "with_metadata.ifc"
  model.write(str(metadata_path))
  return metadata_path
