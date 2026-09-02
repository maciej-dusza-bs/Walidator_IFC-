# Walidator IFC MVP

Zautomatyzowana walidacja pliku IFC.

Lokalna aplikacja webowa w języku Python do kontroli pojedynczego modelu IFC (IFC2X3).

## Opis

- Aplikacja uruchamiana lokalnie na komputerze użytkownika.
- Przyjmuje jeden plik IFC o wielkości do 50 MB.
- Po wczytaniu i walidacji wykonuje kolejne grupy sprawdzeń jako odrębne funkcjonalności.
- Każde sprawdzenie zwraca wynik w ujednoliconym formacie.
- Wybrane funkcjonalności mogą przyjmować dodatkowe pliki XLSX lub DOCX.
- Na końcu generowany jest Raport Kontroli w formacie XLSX.

## Wymagania

- Python 3.11

## Instalacja

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uruchomienie

```bash
streamlit run app.py
```

## Testy

```bash
pytest
```

## Dokumentacja

- `PROJECT_SPEC.md` — wymagania funkcjonalne
- `AGENTS.md` — zasady implementacji
