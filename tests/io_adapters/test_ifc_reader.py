"""Testy adaptera odczytu IFC."""

from pathlib import Path

from src.io_adapters.ifc_reader import (
  count_ifc_projects,
  format_file_size,
  get_model_schema,
  open_ifc_model,
  read_file_header,
  write_temp_ifc_file,
)


def test_read_file_header_extracts_text(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  header = read_file_header(valid_path.read_bytes())

  assert "ISO-10303-21" in header
  assert "FILE_SCHEMA" in header


def test_write_temp_ifc_file_creates_ifc_suffix(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  file_bytes = valid_path.read_bytes()
  temp_file = write_temp_ifc_file(file_bytes)

  try:
    assert temp_file.path.exists()
    assert temp_file.path.suffix == ".ifc"
    model = open_ifc_model(temp_file.path)
    assert count_ifc_projects(model) == 1
    assert get_model_schema(model) == "IFC2X3"
  finally:
    temp_file.cleanup()
    assert not temp_file.path.exists()


def test_format_file_size() -> None:
  assert format_file_size(512) == "512 B"
  assert format_file_size(2048) == "2.00 KB"
  assert format_file_size(2 * 1024 * 1024) == "2.00 MB"


def test_format_file_size_mb() -> None:
  from src.io_adapters.ifc_reader import format_file_size_mb

  assert format_file_size_mb(1024 * 1024) == "1.0000 MB"


def test_get_entity_names_and_project_name(generated_ifc_fixtures: dict[str, Path]) -> None:
  import ifcopenshell

  from src.io_adapters.ifc_reader import count_model_entities, get_entity_names, get_ifc_project_name

  metadata_path = generated_ifc_fixtures["with_metadata"]
  model = ifcopenshell.open(str(metadata_path))

  assert get_ifc_project_name(model) == "Test Project"
  assert get_entity_names(model, "IfcBuilding") == ["Building A"]
  assert get_entity_names(model, "IfcSite") == ["Site A"]
  assert count_model_entities(model) > 0
