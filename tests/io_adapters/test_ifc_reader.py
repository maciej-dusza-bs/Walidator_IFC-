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
