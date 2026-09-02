"""Sprawdzenia ekstrakcji metadanych (V-3.1–V-3.6)."""

from __future__ import annotations

from typing import Any

from src.core.models import CheckResult, CheckStatus
from src.io_adapters.ifc_reader import (
  count_model_entities,
  format_file_size_mb,
  get_entity_names,
  get_ifc_project_name,
)

F03_CHECK_IDS = tuple(f"V-3.{index}" for index in range(1, 7))
F03_EVALUABLE_CHECK_IDS = frozenset(f"V-3.{index}" for index in range(1, 6))
F03_INFORMATIONAL_CHECK_IDS = frozenset({"V-3.6"})
PENDING_USER_REVIEW = CheckStatus.SKIPPED


def extract_v31_filename(filename: str | None) -> CheckResult:
  if filename:
    return CheckResult(
      check_id="V-3.1",
      name="Nazwa pliku",
      status=PENDING_USER_REVIEW,
      message=filename,
      value=filename,
    )
  return CheckResult(
    check_id="V-3.1",
    name="Nazwa pliku",
    status=PENDING_USER_REVIEW,
    message="Brak możliwości pobrania nazwy pliku",
  )


def extract_v32_project_name(model: Any | None) -> CheckResult:
  project_name = get_ifc_project_name(model)
  if project_name is not None:
    return CheckResult(
      check_id="V-3.2",
      name="IfcProject.Name",
      status=PENDING_USER_REVIEW,
      message=project_name,
      value=project_name,
    )
  return CheckResult(
    check_id="V-3.2",
    name="IfcProject.Name",
    status=PENDING_USER_REVIEW,
    message="Brak wartości IfcProject.Name",
  )


def extract_v33_building_names(model: Any | None) -> CheckResult:
  if model is None:
    return CheckResult(
      check_id="V-3.3",
      name="Lista wartości IfcBuilding.Name",
      status=PENDING_USER_REVIEW,
      message="Brak budynku IFC",
      value=[],
    )

  names = get_entity_names(model, "IfcBuilding")
  return CheckResult(
    check_id="V-3.3",
    name="Lista wartości IfcBuilding.Name",
    status=PENDING_USER_REVIEW,
    message=", ".join(names) if names else "Brak budynku IFC",
    value=names,
  )


def extract_v34_site_names(model: Any | None) -> CheckResult:
  if model is None:
    return CheckResult(
      check_id="V-3.4",
      name="Lista wartości IfcSite.Name",
      status=PENDING_USER_REVIEW,
      message="Brak IfcSite",
      value=[],
    )

  names = get_entity_names(model, "IfcSite")
  return CheckResult(
    check_id="V-3.4",
    name="Lista wartości IfcSite.Name",
    status=PENDING_USER_REVIEW,
    message=", ".join(names) if names else "Brak IfcSite",
    value=names,
  )


def extract_v35_file_size_mb(file_bytes: bytes | None) -> CheckResult:
  if file_bytes is None:
    return CheckResult(
      check_id="V-3.5",
      name="Rozmiar pliku w MB",
      status=PENDING_USER_REVIEW,
      message="Nie można pobrać rozmiaru pliku",
    )

  size_mb = format_file_size_mb(len(file_bytes))
  return CheckResult(
    check_id="V-3.5",
    name="Rozmiar pliku w MB",
    status=PENDING_USER_REVIEW,
    message=size_mb,
    value=len(file_bytes),
  )


def extract_v36_entity_count(model: Any | None) -> CheckResult:
  if model is None:
    return CheckResult(
      check_id="V-3.6",
      name="Łączna liczba encji w modelu",
      status=PENDING_USER_REVIEW,
      message="Nie można pobrać liczby encji",
    )

  entity_count = count_model_entities(model)
  return CheckResult(
    check_id="V-3.6",
    name="Łączna liczba encji w modelu",
    status=PENDING_USER_REVIEW,
    message=str(entity_count),
    value=entity_count,
  )


def extract_metadata(
  filename: str | None,
  file_bytes: bytes | None,
  model: Any | None,
) -> list[CheckResult]:
  """Ekstrahuje metadane V-3.1–V-3.6 do oceny użytkownika."""
  return [
    extract_v31_filename(filename),
    extract_v32_project_name(model),
    extract_v33_building_names(model),
    extract_v34_site_names(model),
    extract_v35_file_size_mb(file_bytes),
    extract_v36_entity_count(model),
  ]
