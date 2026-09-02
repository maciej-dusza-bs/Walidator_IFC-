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
