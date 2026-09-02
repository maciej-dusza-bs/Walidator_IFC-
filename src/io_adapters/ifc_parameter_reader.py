"""Odczyt parametrów encji IFC do eksportu."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

EXPORT_COLUMNS = ["Name", "GlobalID", "ObjectType", "IfcClass"]


def is_exportable_ifc_element(entity: Any) -> bool:
  """Sprawdza, czy encja jest IfcElement, ale nie dziedziczy po IfcFeatureElement."""
  return entity.is_a("IfcElement") and not entity.is_a("IfcFeatureElement")


def _format_parameter_value(value: Any) -> str:
  if value is None:
    return ""
  if isinstance(value, bool):
    return "Tak" if value else "Nie"
  return str(value)


def list_model_ifc_classes(model: Any) -> list[str]:
  """Zwraca posortowaną listę klas IfcElement bez IfcFeatureElement występujących w modelu."""
  return sorted({entity.is_a() for entity in model if is_exportable_ifc_element(entity)})


def collect_entity_export_row(entity: Any) -> dict[str, str]:
  """Zbiera wiersz eksportu z podstawowymi parametrami encji."""
  return {
    "Name": _format_parameter_value(getattr(entity, "Name", None)),
    "GlobalID": _format_parameter_value(getattr(entity, "GlobalId", None)),
    "ObjectType": _format_parameter_value(getattr(entity, "ObjectType", None)),
    "IfcClass": entity.is_a(),
  }


def extract_entity_parameter_table(
  model: Any,
  selected_classes: list[str],
  progress_callback: Callable[[int, int], None] | None = None,
) -> tuple[list[str], list[dict[str, str]]]:
  """Buduje tabelę encji wybranych klas IFC."""
  selected_class_set = set(selected_classes)
  entities = list(model)
  total_entities = len(entities)
  rows: list[dict[str, str]] = []

  for index, entity in enumerate(entities, start=1):
    if progress_callback is not None:
      progress_callback(index, total_entities)
    if not is_exportable_ifc_element(entity):
      continue
    if entity.is_a() not in selected_class_set:
      continue
    rows.append(collect_entity_export_row(entity))

  return EXPORT_COLUMNS, rows
