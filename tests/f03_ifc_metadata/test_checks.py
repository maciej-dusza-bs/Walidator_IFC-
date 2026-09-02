"""Testy ekstrakcji metadanych F-03."""

from pathlib import Path

import ifcopenshell

from src.core.models import CheckStatus
from src.features.f03_ifc_metadata.checks import (
  extract_metadata,
  extract_v31_filename,
  extract_v32_project_name,
  extract_v33_building_names,
  extract_v34_site_names,
  extract_v35_file_size_mb,
  extract_v36_entity_count,
)


def test_extract_v31_filename_available() -> None:
  result = extract_v31_filename("model.ifc")

  assert result.message == "model.ifc"
  assert result.status == CheckStatus.SKIPPED


def test_extract_v31_filename_missing() -> None:
  result = extract_v31_filename(None)

  assert result.message == "Brak możliwości pobrania nazwy pliku"


def test_extract_v35_file_size_mb() -> None:
  file_bytes = b"0" * (1024 * 1024)
  result = extract_v35_file_size_mb(file_bytes)

  assert result.message == "1.0000 MB"
  assert result.value == 1024 * 1024


def test_extract_v35_file_size_missing() -> None:
  result = extract_v35_file_size_mb(None)

  assert result.message == "Nie można pobrać rozmiaru pliku"


def test_extract_metadata_with_full_model(generated_ifc_fixtures: dict[str, Path]) -> None:
  metadata_path = generated_ifc_fixtures["with_metadata"]
  file_bytes = metadata_path.read_bytes()
  model = ifcopenshell.open(str(metadata_path))

  results = extract_metadata(metadata_path.name, file_bytes, model)

  assert len(results) == 6
  assert results[0].message == metadata_path.name
  assert results[1].message == "Test Project"
  assert results[2].message == "Building A"
  assert results[3].message == "Site A"
  assert "MB" in results[4].message
  assert int(results[5].message) > 0


def test_extract_v33_without_buildings(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  model = ifcopenshell.open(str(valid_path))
  result = extract_v33_building_names(model)

  assert result.message == "Brak budynku IFC"


def test_extract_v34_without_sites(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  model = ifcopenshell.open(str(valid_path))
  result = extract_v34_site_names(model)

  assert result.message == "Brak IfcSite"


def test_extract_v32_without_project_name(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  model = ifcopenshell.open(str(valid_path))
  projects = model.by_type("IfcProject")
  projects[0].Name = None
  result = extract_v32_project_name(model)

  assert result.message == "Brak wartości IfcProject.Name"


def test_extract_v36_entity_count_missing_model() -> None:
  result = extract_v36_entity_count(None)

  assert result.message == "Nie można pobrać liczby encji"
