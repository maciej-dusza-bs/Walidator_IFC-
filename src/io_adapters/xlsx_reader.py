"""Techniczny odczyt plików XLSX."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

import pandas as pd

IFC_CLASS_COLUMN = "IfcClass"
HEADER_SCAN_LIMIT = 30

XLSX_FORMAT_HINT = (
  "Oczekiwany format pliku XLSX:\n"
  "- rozszerzenie `.xlsx`;\n"
  "- arkusz z listą klas IFC;\n"
  "- wiersz nagłówka z kolumną `IfcClass` (może znajdować się poniżej tytułu arkusza);\n"
  "- jedna klasa na wiersz, np. `IfcWall`, `IfcDoor` lub kilka klas w jednej komórce oddzielonych `/`;\n"
  "- puste wiersze i duplikaty są pomijane automatycznie."
)


@dataclass
class XlsxSheetInfo:
  """Informacje o arkuszach w pliku XLSX."""

  sheet_names: list[str]
  error_message: str | None = None
  format_hint: str | None = None


@dataclass
class XlsxSheetColumnsInfo:
  """Informacje o kolumnach wybranego arkusza."""

  columns: list[str]
  error_message: str | None = None
  format_hint: str | None = None


@dataclass
class AllowedClassesLoadResult:
  """Wynik wczytania listy dopuszczalnych klas IFC."""

  classes: list[str]
  error_message: str | None = None
  format_hint: str | None = None
  selected_column: str | None = None


def _with_format_hint(message: str) -> tuple[str, str]:
  return message, XLSX_FORMAT_HINT


def _normalize_cell_value(value: object) -> str:
  if pd.isna(value):
    return ""
  return str(value).strip()


def _is_unnamed_column(column_name: str) -> bool:
  normalized = column_name.strip()
  return normalized.startswith("Unnamed:") or normalized.lower() == "nan"


def _detect_header_row_index(raw_dataframe: pd.DataFrame) -> int | None:
  """Wykrywa wiersz nagłówka, szukając kolumny `IfcClass` lub typowego wiersza tytułowego."""
  scan_limit = min(len(raw_dataframe), HEADER_SCAN_LIMIT)

  for row_index in range(scan_limit):
    row_values = [
      _normalize_cell_value(value)
      for value in raw_dataframe.iloc[row_index].tolist()
      if _normalize_cell_value(value)
    ]
    if IFC_CLASS_COLUMN in row_values:
      return row_index

  best_index: int | None = None
  best_score = 0
  for row_index in range(scan_limit):
    row_values = [
      _normalize_cell_value(value)
      for value in raw_dataframe.iloc[row_index].tolist()
      if _normalize_cell_value(value)
    ]
    if len(row_values) >= 2 and all(len(value) < 80 for value in row_values):
      if len(row_values) > best_score:
        best_score = len(row_values)
        best_index = row_index

  return best_index


def _clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
  """Usuwa puste kolumny bez nagłówka i normalizuje nazwy kolumn."""
  columns_to_keep: list[str] = []
  for column in dataframe.columns:
    column_name = _normalize_cell_value(column)
    if _is_unnamed_column(column_name):
      continue
    columns_to_keep.append(column)

  cleaned = dataframe[columns_to_keep].copy()
  cleaned.columns = [_normalize_cell_value(column) for column in cleaned.columns]
  return cleaned


def _read_raw_sheet_dataframe(file_bytes: bytes, sheet_name: str) -> pd.DataFrame | None:
  try:
    return pd.read_excel(
      BytesIO(file_bytes),
      sheet_name=sheet_name,
      header=None,
      engine="openpyxl",
    )
  except Exception:
    return None


def _read_sheet_dataframe(
  file_bytes: bytes,
  sheet_name: str,
) -> tuple[pd.DataFrame | None, str | None, str | None]:
  raw_dataframe = _read_raw_sheet_dataframe(file_bytes, sheet_name)
  if raw_dataframe is None:
    message, hint = _with_format_hint(
      f"Nie można odczytać arkusza `{sheet_name}`. Wybierz inny arkusz albo popraw zawartość pliku."
    )
    return None, message, hint

  header_row_index = _detect_header_row_index(raw_dataframe)
  if header_row_index is None:
    message, hint = _with_format_hint(
      f"Nie znaleziono wiersza nagłówka w arkuszu `{sheet_name}`. "
      f"Dodaj wiersz z kolumną `{IFC_CLASS_COLUMN}`."
    )
    return None, message, hint

  try:
    dataframe = pd.read_excel(
      BytesIO(file_bytes),
      sheet_name=sheet_name,
      header=header_row_index,
      engine="openpyxl",
    )
    return _clean_dataframe(dataframe), None, None
  except Exception:
    message, hint = _with_format_hint(
      f"Nie można odczytać arkusza `{sheet_name}` po wykryciu nagłówka. Popraw strukturę pliku."
    )
    return None, message, hint


def list_xlsx_sheet_names(file_bytes: bytes) -> XlsxSheetInfo:
  """Zwraca nazwy arkuszy z pliku XLSX lub komunikat błędu."""
  try:
    workbook = pd.ExcelFile(BytesIO(file_bytes))
    sheet_names = list(workbook.sheet_names)
    if not sheet_names:
      message, hint = _with_format_hint(
        "Plik XLSX nie zawiera żadnych arkuszy. Przygotuj plik z co najmniej jednym arkuszem danych."
      )
      return XlsxSheetInfo(sheet_names=[], error_message=message, format_hint=hint)
    return XlsxSheetInfo(sheet_names=sheet_names)
  except Exception:
    message, hint = _with_format_hint(
      "Nie można otworzyć pliku XLSX. Upewnij się, że przesyłasz poprawny plik Excel w formacie `.xlsx`."
    )
    return XlsxSheetInfo(sheet_names=[], error_message=message, format_hint=hint)


def list_sheet_columns(file_bytes: bytes, sheet_name: str) -> XlsxSheetColumnsInfo:
  """Zwraca nazwy kolumn z wybranego arkusza."""
  dataframe, error_message, format_hint = _read_sheet_dataframe(file_bytes, sheet_name)
  if dataframe is None:
    return XlsxSheetColumnsInfo(columns=[], error_message=error_message, format_hint=format_hint)

  columns = [str(column).strip() for column in dataframe.columns if str(column).strip()]
  if not columns:
    message, hint = _with_format_hint(
      f"Arkusz `{sheet_name}` nie zawiera nagłówków kolumn. Dodaj wiersz nagłówka z nazwą kolumny klas IFC."
    )
    return XlsxSheetColumnsInfo(columns=[], error_message=message, format_hint=hint)

  return XlsxSheetColumnsInfo(columns=columns)


def _expand_class_values(column_values: pd.Series) -> list[str]:
  """Rozdziela wartości komórek na pojedyncze nazwy klas IFC."""
  classes: set[str] = set()
  for raw_value in column_values.dropna().astype(str).str.strip():
    if not raw_value:
      continue
    for part in raw_value.split("/"):
      class_name = part.strip()
      if class_name:
        classes.add(class_name)
  return sorted(classes)


def read_allowed_ifc_classes(
  file_bytes: bytes,
  sheet_name: str,
  column_name: str | None = None,
) -> AllowedClassesLoadResult:
  """Wczytuje i normalizuje listę klas z wybranego arkusza i kolumny."""
  dataframe, error_message, format_hint = _read_sheet_dataframe(file_bytes, sheet_name)
  if dataframe is None:
    return AllowedClassesLoadResult(
      classes=[],
      error_message=error_message,
      format_hint=format_hint,
    )

  available_columns = list_sheet_columns(file_bytes, sheet_name).columns
  if not available_columns:
    return AllowedClassesLoadResult(
      classes=[],
      error_message=error_message or "Nie znaleziono kolumn w arkuszu.",
      format_hint=format_hint,
    )

  if len(available_columns) > 1 and not column_name:
    message, hint = _with_format_hint(
      "Arkusz zawiera więcej niż jedną kolumnę. Wybierz kolumnę z listą klas IFC i kliknij "
      "„Wczytaj listę klas” ponownie."
    )
    return AllowedClassesLoadResult(
      classes=[],
      error_message=message,
      format_hint=hint,
    )

  resolved_column = column_name or (
    available_columns[0] if len(available_columns) == 1 else IFC_CLASS_COLUMN
  )
  if resolved_column not in available_columns:
    message, hint = _with_format_hint(
      f"Wybrana kolumna `{resolved_column}` nie istnieje w arkuszu `{sheet_name}`. "
      f"Dostępne kolumny: {', '.join(available_columns)}."
    )
    return AllowedClassesLoadResult(
      classes=[],
      error_message=message,
      format_hint=hint,
      selected_column=resolved_column,
    )

  classes = _expand_class_values(dataframe[resolved_column])

  if not classes:
    message, hint = _with_format_hint(
      f"Kolumna `{resolved_column}` nie zawiera żadnych niepustych nazw klas IFC. "
      "Uzupełnij kolumnę wartościami, np. `IfcWall`, `IfcDoor`."
    )
    return AllowedClassesLoadResult(
      classes=[],
      error_message=message,
      format_hint=hint,
      selected_column=resolved_column,
    )

  return AllowedClassesLoadResult(
    classes=classes,
    selected_column=resolved_column,
  )
