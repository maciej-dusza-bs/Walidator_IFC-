"""Techniczny odczyt plików IFC."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ifcopenshell

MIN_IFC_FILE_SIZE_BYTES = 10
MAX_IFC_FILE_SIZE_BYTES = 50 * 1024 * 1024
HEADER_READ_LIMIT_BYTES = 16_384


@dataclass
class TempIfcFile:
  """Bezpieczny plik tymczasowy z modelem IFC."""

  path: Path

  def cleanup(self) -> None:
    if self.path.exists():
      self.path.unlink(missing_ok=True)


def read_file_header(file_bytes: bytes, limit: int = HEADER_READ_LIMIT_BYTES) -> str:
  """Odczytuje początek pliku jako tekst nagłówka IFC-SPF."""
  return file_bytes[:limit].decode("utf-8", errors="replace")


def format_file_size(size_bytes: int) -> str:
  """Formatuje rozmiar pliku do czytelnej postaci."""
  if size_bytes < 1024:
    return f"{size_bytes} B"
  size_mb = size_bytes / (1024 * 1024)
  if size_bytes < 1024 * 1024:
    return f"{size_bytes / 1024:.2f} KB"
  return f"{size_mb:.2f} MB"


def write_temp_ifc_file(file_bytes: bytes) -> TempIfcFile:
  """Zapisuje bajty pliku IFC w bezpiecznym pliku tymczasowym."""
  temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ifc")
  try:
    temp_file.write(file_bytes)
    temp_file.flush()
  finally:
    temp_file.close()
  return TempIfcFile(path=Path(temp_file.name))


def open_ifc_model(path: Path) -> Any:
  """Otwiera model IFC za pomocą IfcOpenShell."""
  return ifcopenshell.open(str(path))


def count_ifc_projects(model: Any) -> int:
  """Zwraca liczbę encji IfcProject w modelu."""
  return len(model.by_type("IfcProject"))


def get_model_schema(model: Any) -> str:
  """Zwraca nazwę schematu modelu."""
  return str(model.schema)
