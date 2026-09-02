"""Sprawdzenia klas IFC (V-4.x)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.models import CheckResult, CheckStatus


STANDARD_BUILDING_IFC_CLASSES: tuple[str, ...] = (
  "IfcBuilding",
  "IfcBuildingStorey",
  "IfcSite",
)


@dataclass
class ClassVerificationRow:
  """Pojedynczy wiersz tabeli wynikowej F-04."""

  class_name: str
  occurrence_count: int
  is_allowed: bool


def group_ifc_product_classes(model: Any) -> dict[str, int]:
  """Grupuje instancje IfcProduct według dokładnej klasy."""
  class_counts: dict[str, int] = {}
  for entity in model.by_type("IfcProduct"):
    class_name = entity.is_a()
    class_counts[class_name] = class_counts.get(class_name, 0) + 1
  return class_counts


def build_class_verification_rows(
  model: Any,
  allowed_classes: list[str],
) -> list[ClassVerificationRow]:
  """Buduje tabelę wynikową dla wszystkich klas modelu i listy dopuszczalnej."""
  allowed_set = set(allowed_classes)
  model_counts = group_ifc_product_classes(model)
  all_classes = sorted(allowed_set | set(model_counts.keys()))

  rows: list[ClassVerificationRow] = []
  for class_name in all_classes:
    rows.append(
      ClassVerificationRow(
        class_name=class_name,
        occurrence_count=model_counts.get(class_name, 0),
        is_allowed=class_name in allowed_set,
      )
    )
  return rows


def build_class_check_results(rows: list[ClassVerificationRow]) -> list[CheckResult]:
  """Tworzy osobne sprawdzenie V-4.x dla każdej klasy."""
  results: list[CheckResult] = []
  for index, row in enumerate(rows, start=1):
    allowed_label = "Tak" if row.is_allowed else "Nie"
    status = CheckStatus.PASS if row.is_allowed else CheckStatus.FAIL
    results.append(
      CheckResult(
        check_id=f"V-4.{index}",
        name=f"Klasa IFC: {row.class_name}",
        status=status,
        message=(
          f"Klasa `{row.class_name}` występuje {row.occurrence_count} raz(y). "
          f"Czy klasa dopuszczalna: {allowed_label}."
        ),
        value={
          "class_name": row.class_name,
          "occurrence_count": row.occurrence_count,
          "is_allowed": row.is_allowed,
          "allowed_label": allowed_label,
        },
      )
    )
  return results


def has_disallowed_classes(rows: list[ClassVerificationRow]) -> bool:
  """Sprawdza, czy w modelu występuje co najmniej jedna niedopuszczalna klasa."""
  return any(not row.is_allowed and row.occurrence_count > 0 for row in rows)


def normalize_allowed_classes(classes: list[str]) -> list[str]:
  """Dodaje standardowe klasy budynku do listy dopuszczalnych klas IFC."""
  return sorted(set(classes) | set(STANDARD_BUILDING_IFC_CLASSES))


def create_skipped_f04_result(message: str | None = None) -> CheckResult:
  """Tworzy wynik pominięcia funkcjonalności F-04."""
  return CheckResult(
    check_id="F-04",
    name="Weryfikacja dopuszczalnych klas IFC",
    status=CheckStatus.SKIPPED,
    message=message or "Funkcjonalność F-04 została pominięta przez użytkownika.",
  )
