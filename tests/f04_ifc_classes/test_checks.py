"""Testy sprawdzeń F-04."""

from pathlib import Path

import ifcopenshell

from src.core.models import CheckStatus
from src.features.f04_ifc_classes.checks import (
  build_class_check_results,
  build_class_verification_rows,
  create_skipped_f04_result,
  group_ifc_product_classes,
  has_disallowed_classes,
)


def test_group_ifc_product_classes(generated_ifc_fixtures: dict[str, Path]) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))

  class_counts = group_ifc_product_classes(model)

  assert class_counts["IfcWall"] == 1
  assert class_counts["IfcDoor"] == 1


def test_build_class_verification_rows_includes_allowed_with_zero_count(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))

  rows = build_class_verification_rows(model, ["IfcWall", "IfcSlab"])

  row_by_class = {row.class_name: row for row in rows}
  assert row_by_class["IfcSlab"].occurrence_count == 0
  assert row_by_class["IfcSlab"].is_allowed is True
  assert row_by_class["IfcDoor"].is_allowed is False


def test_build_class_check_results_assigns_fail_for_disallowed_class(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  rows = build_class_verification_rows(model, ["IfcWall"])

  results = build_class_check_results(rows)
  door_result = next(result for result in results if result.value["class_name"] == "IfcDoor")

  assert door_result.check_id.startswith("V-4.")
  assert door_result.status == CheckStatus.FAIL
  assert has_disallowed_classes(rows) is True


def test_build_class_check_results_pass_for_allowed_classes(
  generated_ifc_fixtures: dict[str, Path],
) -> None:
  products_path = generated_ifc_fixtures["with_products"]
  model = ifcopenshell.open(str(products_path))
  rows = build_class_verification_rows(model, ["IfcWall", "IfcDoor"])

  results = build_class_check_results(rows)

  assert all(result.status == CheckStatus.PASS for result in results)
  assert has_disallowed_classes(rows) is False


def test_create_skipped_f04_result() -> None:
  result = create_skipped_f04_result()

  assert result.check_id == "F-04"
  assert result.status == CheckStatus.SKIPPED


def test_normalize_allowed_classes_adds_standard_building_classes() -> None:
  from src.features.f04_ifc_classes.checks import normalize_allowed_classes

  classes = normalize_allowed_classes(["IfcWall"])

  assert "IfcWall" in classes
  assert "IfcBuilding" in classes
  assert "IfcBuildingStorey" in classes
  assert "IfcSite" in classes
