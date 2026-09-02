"""Testy service F-04."""

from pathlib import Path

import ifcopenshell

from src.core.audit_context import AuditContext
from src.core.models import CheckStatus
from src.features.f04_ifc_classes import register_f04_feature
from src.features.f04_ifc_classes.service import (
  load_allowed_classes,
  run_class_verification,
  run_f04_ifc_classes,
  skip_f04,
)


def test_load_allowed_classes_normalizes_values(generated_xlsx_fixtures: dict[str, Path]) -> None:
  valid_path = generated_xlsx_fixtures["valid"]
  result = load_allowed_classes(valid_path.read_bytes(), "Klasy", "IfcClass")

  assert result.error_message is None
  assert result.classes == ["IfcBuilding", "IfcBuildingStorey", "IfcDoor", "IfcSite", "IfcWall"]


def test_load_allowed_classes_missing_column_selection(generated_xlsx_fixtures: dict[str, Path]) -> None:
  multi_column_path = generated_xlsx_fixtures["multi_column"]
  result = load_allowed_classes(multi_column_path.read_bytes(), "Klasy")

  assert result.classes == []
  assert result.error_message is not None


def test_run_class_verification_updates_context(
  generated_ifc_fixtures: dict[str, Path],
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  xlsx_path = generated_xlsx_fixtures["valid"]
  allowed = load_allowed_classes(xlsx_path.read_bytes(), "Klasy", "IfcClass").classes
  context = AuditContext(ifc_model=model, f04_allowed_classes=allowed, f03_completed=True)

  results = run_class_verification(context)

  assert context.f04_completed is True
  assert context.f04_has_failures is False
  assert all(result.status == CheckStatus.PASS for result in results)


def test_run_class_verification_detects_failures(generated_ifc_fixtures: dict[str, Path]) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  context = AuditContext(
    ifc_model=model,
    f04_allowed_classes=["IfcWall"],
    f03_completed=True,
  )

  results = run_class_verification(context)

  assert context.f04_has_failures is True
  assert any(result.status == CheckStatus.FAIL for result in results)


def test_skip_f04_marks_feature_as_skipped() -> None:
  context = AuditContext(f03_completed=True)

  results = skip_f04(context)

  assert context.f04_skipped is True
  assert context.f04_completed is False
  assert results[0].status == CheckStatus.SKIPPED


def test_run_f04_ifc_classes_via_registry(
  generated_ifc_fixtures: dict[str, Path],
  generated_xlsx_fixtures: dict[str, Path],
) -> None:
  register_f04_feature()
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  xlsx_path = generated_xlsx_fixtures["valid"]
  allowed = load_allowed_classes(xlsx_path.read_bytes(), "Klasy", "IfcClass").classes
  context = AuditContext(ifc_model=model, f04_allowed_classes=allowed)

  results = run_f04_ifc_classes(context)

  assert len(results) >= 2
  assert len(context.f04_results) == len(results)
