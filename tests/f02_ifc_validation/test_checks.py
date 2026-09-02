"""Testy sprawdzeń F-02."""

from pathlib import Path

import pytest

from src.core.models import CheckStatus
from src.features.f02_ifc_validation.checks import (
  check_v21_file_uploaded,
  check_v22_extension,
  check_v23_file_size,
  check_v24_iso_header,
  check_v25_file_schema,
  check_v27_single_ifc_project,
  check_v28_schema_ifc2x3,
)
from src.features.f02_ifc_validation.service import can_proceed_after_f02, validate_ifc_file
from src.io_adapters.ifc_reader import MAX_IFC_FILE_SIZE_BYTES
from tests.fixtures.ifc_content import (
  CORRUPT_IFC,
  INVALID_HEADER_IFC,
  NO_FILE_SCHEMA_IFC,
  TOO_SMALL_IFC,
)


def test_v21_pass_when_file_uploaded() -> None:
  result = check_v21_file_uploaded("model.ifc", b"1234567890")

  assert result.status == CheckStatus.PASS


def test_v21_fail_when_file_missing() -> None:
  result = check_v21_file_uploaded(None, None)

  assert result.status == CheckStatus.FAIL


def test_v22_pass_for_ifc_extension() -> None:
  result = check_v22_extension("model.IFC")

  assert result.status == CheckStatus.PASS


def test_v22_fail_for_invalid_extension() -> None:
  result = check_v22_extension("model.txt")

  assert result.status == CheckStatus.FAIL


def test_v23_fail_for_too_small_file() -> None:
  result = check_v23_file_size(TOO_SMALL_IFC)

  assert result.status == CheckStatus.FAIL
  assert "7 B" in result.message


def test_v23_fail_for_too_large_file() -> None:
  oversized = b"x" * (MAX_IFC_FILE_SIZE_BYTES + 1)
  result = check_v23_file_size(oversized)

  assert result.status == CheckStatus.FAIL


def test_v24_fail_for_invalid_header() -> None:
  result, header = check_v24_iso_header(INVALID_HEADER_IFC)

  assert result.status == CheckStatus.FAIL
  assert header is not None


def test_v25_fail_without_file_schema() -> None:
  result, header = check_v24_iso_header(NO_FILE_SCHEMA_IFC)
  assert result.status == CheckStatus.PASS

  schema_result = check_v25_file_schema(header)

  assert schema_result.status == CheckStatus.FAIL


def test_validate_ifc_file_success(generated_ifc_fixtures: dict[str, Path]) -> None:
  valid_path = generated_ifc_fixtures["valid"]
  file_bytes = valid_path.read_bytes()

  results, temp_path, model = validate_ifc_file(valid_path.name, file_bytes)

  assert temp_path is not None
  assert model is not None
  assert all(result.status == CheckStatus.PASS for result in results)
  assert can_proceed_after_f02(results, v28_accepted=False) is True


def test_validate_ifc_file_stops_on_corrupt_file() -> None:
  results, temp_path, model = validate_ifc_file("corrupt.ifc", CORRUPT_IFC)

  assert temp_path is None
  assert model is None
  assert any(result.check_id == "V-2.6" and result.status == CheckStatus.FAIL for result in results)
  assert not any(result.check_id == "V-2.8" for result in results)


def test_v27_fail_for_multiple_projects(generated_ifc_fixtures: dict[str, Path]) -> None:
  import ifcopenshell

  multi_path = generated_ifc_fixtures["multi_project"]
  model = ifcopenshell.open(str(multi_path))
  result = check_v27_single_ifc_project(model)

  assert result.status == CheckStatus.FAIL
  assert result.value == 2


def test_v27_fail_for_missing_project(generated_ifc_fixtures: dict[str, Path]) -> None:
  import ifcopenshell

  no_project_path = generated_ifc_fixtures["no_project"]
  model = ifcopenshell.open(str(no_project_path))
  result = check_v27_single_ifc_project(model)

  assert result.status == CheckStatus.FAIL
  assert result.value == 0


def test_v28_warning_for_ifc4_schema(generated_ifc_fixtures: dict[str, Path]) -> None:
  import ifcopenshell

  ifc4_path = generated_ifc_fixtures["ifc4"]
  model = ifcopenshell.open(str(ifc4_path))
  result = check_v28_schema_ifc2x3(model)

  assert result.status == CheckStatus.WARNING
  assert result.value == "IFC4"


def test_can_proceed_requires_v28_acceptance(generated_ifc_fixtures: dict[str, Path]) -> None:
  ifc4_path = generated_ifc_fixtures["ifc4"]
  results, _, _ = validate_ifc_file(ifc4_path.name, ifc4_path.read_bytes())

  assert can_proceed_after_f02(results, v28_accepted=False) is False
  assert can_proceed_after_f02(results, v28_accepted=True) is True
