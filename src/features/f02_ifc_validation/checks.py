"""Sprawdzenia walidacji pliku IFC (V-2.1–V-2.8)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.models import CheckResult, CheckStatus
from src.io_adapters.ifc_reader import (
  MAX_IFC_FILE_SIZE_BYTES,
  MIN_IFC_FILE_SIZE_BYTES,
  count_ifc_projects,
  format_file_size,
  get_model_schema,
  open_ifc_model,
  read_file_header,
  write_temp_ifc_file,
)

IFC2X3_SCHEMA = "IFC2X3"
BLOCKING_CHECK_IDS = tuple(f"V-2.{index}" for index in range(1, 8))


@dataclass
class ValidationArtifacts:
  """Dane techniczne wygenerowane podczas walidacji."""

  header_text: str | None = None
  temp_path: Path | None = None
  model: Any | None = None
  schema: str | None = None


def check_v21_file_uploaded(filename: str | None, file_bytes: bytes | None) -> CheckResult:
  if filename and file_bytes is not None:
    return CheckResult(
      check_id="V-2.1",
      name="Plik został przesłany",
      status=CheckStatus.PASS,
      message="Plik został przesłany i jest gotowy do walidacji.",
      value=filename,
    )
  return CheckResult(
    check_id="V-2.1",
    name="Plik został przesłany",
    status=CheckStatus.FAIL,
    message=(
      "Nie wybrano pliku IFC. Wybierz plik do kontroli albo zakończ proces, "
      "jeśli nie chcesz kontynuować."
    ),
  )


def check_v22_extension(filename: str | None) -> CheckResult:
  if filename and filename.lower().endswith(".ifc"):
    return CheckResult(
      check_id="V-2.2",
      name="Rozszerzenie pliku to `.ifc`",
      status=CheckStatus.PASS,
      message="Rozszerzenie pliku jest poprawne. To nie jest jednak gwarancja poprawnej zawartości.",
      value=filename,
    )
  return CheckResult(
    check_id="V-2.2",
    name="Rozszerzenie pliku to `.ifc`",
    status=CheckStatus.FAIL,
    message=(
      "Plik został odrzucony, ponieważ nie ma rozszerzenia `.ifc`. "
      "Wybierz plik IFC o poprawnym rozszerzeniu."
    ),
    value=filename,
  )


def check_v23_file_size(file_bytes: bytes | None) -> CheckResult:
  if file_bytes is None:
    return CheckResult(
      check_id="V-2.3",
      name="Rozmiar wynosi od 10 B do 50 MB",
      status=CheckStatus.FAIL,
      message="Nie można sprawdzić rozmiaru, ponieważ plik nie został przesłany.",
    )

  size = len(file_bytes)
  if MIN_IFC_FILE_SIZE_BYTES <= size <= MAX_IFC_FILE_SIZE_BYTES:
    return CheckResult(
      check_id="V-2.3",
      name="Rozmiar wynosi od 10 B do 50 MB",
      status=CheckStatus.PASS,
      message="Rozmiar pliku mieści się w dopuszczalnym zakresie.",
      value=size,
    )

  allowed_range = (
    f"{format_file_size(MIN_IFC_FILE_SIZE_BYTES)} – "
    f"{format_file_size(MAX_IFC_FILE_SIZE_BYTES)}"
  )
  return CheckResult(
    check_id="V-2.3",
    name="Rozmiar wynosi od 10 B do 50 MB",
    status=CheckStatus.FAIL,
    message=(
      f"Rozmiar pliku ({format_file_size(size)}) jest poza dopuszczalnym zakresem "
      f"({allowed_range}). Wybierz inny plik IFC."
    ),
    value=size,
  )


def check_v24_iso_header(file_bytes: bytes | None) -> tuple[CheckResult, str | None]:
  if file_bytes is None:
    return (
      CheckResult(
        check_id="V-2.4",
        name="Nagłówek zawiera `ISO-10303-21`",
        status=CheckStatus.FAIL,
        message="Nie można odczytać nagłówka, ponieważ plik nie został przesłany.",
      ),
      None,
    )

  header_text = read_file_header(file_bytes)
  if "ISO-10303-21" in header_text:
    return (
      CheckResult(
        check_id="V-2.4",
        name="Nagłówek zawiera `ISO-10303-21`",
        status=CheckStatus.PASS,
        message="Nagłówek zawiera identyfikator formatu IFC-SPF.",
      ),
      header_text,
    )

  return (
    CheckResult(
      check_id="V-2.4",
      name="Nagłówek zawiera `ISO-10303-21`",
      status=CheckStatus.FAIL,
      message=(
        "Plik nie wygląda na poprawny plik IFC-SPF, ponieważ w nagłówku brakuje "
        "identyfikatora `ISO-10303-21`. Sprawdź źródło eksportu modelu."
      ),
    ),
    header_text,
  )


def check_v25_file_schema(header_text: str | None) -> CheckResult:
  if header_text and "FILE_SCHEMA" in header_text:
    return CheckResult(
      check_id="V-2.5",
      name="Nagłówek zawiera `FILE_SCHEMA`",
      status=CheckStatus.PASS,
      message="Nagłówek zawiera deklarację schematu IFC.",
    )
  return CheckResult(
    check_id="V-2.5",
    name="Nagłówek zawiera `FILE_SCHEMA`",
    status=CheckStatus.FAIL,
    message=(
      "Plik wygląda na błędnie wyeksportowany, ponieważ w nagłówku brakuje "
      "deklaracji `FILE_SCHEMA`. Poproś o ponowny eksport modelu."
    ),
  )


def check_v26_open_with_ifcopenshell(file_bytes: bytes | None) -> tuple[CheckResult, Path | None, Any | None]:
  if file_bytes is None:
    return (
      CheckResult(
        check_id="V-2.6",
        name="IfcOpenShell otwiera plik",
        status=CheckStatus.FAIL,
        message="Nie można otworzyć pliku, ponieważ nie został przesłany.",
      ),
      None,
      None,
    )

  temp_file = write_temp_ifc_file(file_bytes)
  try:
    model = open_ifc_model(temp_file.path)
    return (
      CheckResult(
        check_id="V-2.6",
        name="IfcOpenShell otwiera plik",
        status=CheckStatus.PASS,
        message="Plik został poprawnie otwarty przez IfcOpenShell.",
      ),
      temp_file.path,
      model,
    )
  except Exception:
    temp_file.cleanup()
    return (
      CheckResult(
        check_id="V-2.6",
        name="IfcOpenShell otwiera plik",
        status=CheckStatus.FAIL,
        message=(
          "Nie udało się otworzyć pliku jako modelu IFC. Plik może być uszkodzony "
          "lub niekompletny. Sprawdź plik i spróbuj ponownie."
        ),
      ),
      None,
      None,
    )


def check_v27_single_ifc_project(model: Any | None) -> CheckResult:
  if model is None:
    return CheckResult(
      check_id="V-2.7",
      name="Model zawiera dokładnie jeden `IfcProject`",
      status=CheckStatus.FAIL,
      message="Nie można zweryfikować liczby projektów, ponieważ model nie został otwarty.",
    )

  project_count = count_ifc_projects(model)
  if project_count == 1:
    return CheckResult(
      check_id="V-2.7",
      name="Model zawiera dokładnie jeden `IfcProject`",
      status=CheckStatus.PASS,
      message="Model zawiera dokładnie jeden element `IfcProject`.",
      value=project_count,
    )

  if project_count == 0:
    message = (
      "Model nie zawiera elementu `IfcProject`. Audyt modelu został zablokowany. "
      "Uzupełnij model o projekt IFC lub wybierz inny plik."
    )
  else:
    message = (
      f"Model zawiera {project_count} elementów `IfcProject`, a wymagany jest dokładnie jeden. "
      "Audyt modelu został zablokowany. Wybierz poprawny plik IFC."
    )

  return CheckResult(
    check_id="V-2.7",
    name="Model zawiera dokładnie jeden `IfcProject`",
    status=CheckStatus.FAIL,
    message=message,
    value=project_count,
  )


def check_v28_schema_ifc2x3(model: Any | None) -> CheckResult:
  if model is None:
    return CheckResult(
      check_id="V-2.8",
      name="Schemat modelu to IFC2X3",
      status=CheckStatus.FAIL,
      message="Nie można odczytać schematu, ponieważ model nie został otwarty.",
    )

  schema = get_model_schema(model)
  if schema.upper() == IFC2X3_SCHEMA:
    return CheckResult(
      check_id="V-2.8",
      name="Schemat modelu to IFC2X3",
      status=CheckStatus.PASS,
      message="Schemat modelu to IFC2X3.",
      value=schema,
    )

  return CheckResult(
    check_id="V-2.8",
    name="Schemat modelu to IFC2X3",
    status=CheckStatus.WARNING,
    message=(
      f"Odczytany schemat modelu to `{schema}`, a aplikacja oczekuje IFC2X3. "
      "Zaakceptuj ostrzeżenie, aby kontynuować audyt."
    ),
    value=schema,
  )
