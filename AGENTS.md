# AGENTS.md — Walidator IFC MVP

## 1. Źródła wymagań

- Przed rozpoczęciem pracy przeczytaj `PROJECT_SPEC.md`.
- `PROJECT_SPEC.md` określa, **co** ma robić aplikacja.
- Ten plik określa, **jak** należy ją implementować.
- Jeżeli wymaganie jest niejednoznaczne lub sprzeczne, nie zgaduj. Opisz problem i poproś użytkownika o decyzję.

## 2. Zakres pracy

- Implementuj wyłącznie funkcjonalność wskazaną w bieżącym poleceniu.
- Nie implementuj kolejnych funkcjonalności „przy okazji”.
- Nie implementuj F-05, dopóki jej wymagania nie zostaną osobno zdefiniowane.
- Nie dodawaj logowania, bazy danych, wersji serwerowej, obsługi wielu modeli ani innych funkcji spoza `PROJECT_SPEC.md`.
- Zachowuj zgodność wsteczną z ukończonymi funkcjonalnościami.

## 3. Technologie

- Python 3.11.
- Streamlit 1.62 — lokalny interfejs webowy.
- IfcOpenShell 0.8.5 — odczyt modeli IFC.
- pandas i openpyxl — odczyt danych XLSX i generowanie raportu XLSX.
- pytest — testy automatyczne.
- `streamlit.testing.v1.AppTest` — podstawowy test interfejsu.
- `python-docx` dodaj dopiero wtedy, gdy zatwierdzona funkcjonalność rzeczywiście wymaga odczytu DOCX.
- Zależności aplikacji zapisuj i przypinaj do sprawdzonych wersji w `requirements.txt`.

## 4. Architektura

Stosuj poniższy podział odpowiedzialności:

```text
ifc-audit-lab/
├── app.py
├── requirements.txt
├── README.md
├── PROJECT_SPEC.md
├── AGENTS.md
├── .streamlit/
│   └── config.toml
├── src/
│   ├── core/
│   │   ├── models.py
│   │   ├── audit_context.py
│   │   ├── audit_engine.py
│   │   └── check_registry.py
│   ├── io_adapters/
│   │   ├── ifc_reader.py
│   │   ├── xlsx_reader.py
│   │   └── docx_reader.py
│   ├── features/
│   │   ├── f02_ifc_validation/
│   │   │   ├── checks.py
│   │   │   └── service.py
│   │   ├── f03_ifc_metadata/
│   │   │   ├── checks.py
│   │   │   └── service.py
│   │   ├── f04_ifc_classes/
│   │   │   ├── checks.py
│   │   │   └── service.py
│   │   ├── f05_ifcwall_parameters/
│   │   └── f06_report/
│   │       └── report_generator.py
│   └── ui/
│       ├── workflow.py
│       └── components.py
└── tests/
    ├── fixtures/
    ├── core/
    ├── f02_ifc_validation/
    ├── f03_ifc_metadata/
    ├── f04_ifc_classes/
    ├── f06_report/
    └── test_app.py
```

Każdy katalog Pythona powinien być pakietem zawierającym `__init__.py`. Plik `docx_reader.py` twórz tylko wtedy, gdy zostanie potrzebny.

## 5. Granice modułów

- `app.py` tylko uruchamia i składa interfejs.
- `src/ui/` odpowiada za prezentację, nawigację i obsługę `st.session_state`.
- `src/features/` zawiera logikę poszczególnych funkcjonalności. Moduły te nie mogą importować Streamlit.
- `src/io_adapters/` odpowiada wyłącznie za techniczny odczyt i zapis plików.
- `src/core/audit_engine.py` uruchamia funkcjonalności i gromadzi ich wyniki.
- `src/core/check_registry.py` określa kolejność sprawdzeń.
- `src/features/f06_report/` tworzy raport wyłącznie na podstawie ujednoliconych wyników; nie zna szczegółów działania sprawdzeń.

## 6. Kontrakt sprawdzenia

- Każde sprawdzenie ma osobną funkcję lub klasę oraz identyfikator zgodny z `PROJECT_SPEC.md`, np. `V-2.3`.
- Funkcje sprawdzające w obrębie funkcjonalności zapisuj w jej pliku `checks.py`.
- Plik `service.py` jedynie uruchamia właściwe sprawdzenia w określonej kolejności.
- Każde sprawdzenie zwraca `CheckResult` zdefiniowany centralnie w `src/core/models.py`.

Minimalne pola `CheckResult`:

- `check_id`;
- `name`;
- `status`;
- `message`;
- `value` — opcjonalna wartość lub szczegóły wyniku;
- `comment` — opcjonalny komentarz użytkownika.

Dozwolone statusy:

- `PASS`;
- `FAIL`;
- `WARNING`;
- `SKIPPED`;
- `ERROR`.

Nie zwracaj z funkcji sprawdzających gotowych komunikatów Streamlit ani elementów interfejsu.

## 7. Obsługa plików

- Rozszerzenie pliku traktuj tylko jako kontrolę wstępną, nie jako dowód poprawności zawartości.
- Plik IFC przekazywany do IfcOpenShell zapisuj w bezpiecznym pliku tymczasowym z rozszerzeniem `.ifc` i usuwaj po użyciu.
- Przechwytuj błędy odczytu. W interfejsie nie pokazuj surowego wyjątku ani tracebacku.
- Pliki XLSX waliduj przed użyciem danych.
- Raport XLSX generuj w pamięci, np. w `BytesIO`, i udostępniaj przez `st.download_button`.
- Nie zapisuj przesłanych modeli i raportów na stałe, jeżeli specyfikacja tego nie wymaga.

## 8. Streamlit i UX

- Stan bieżącego kroku, wyników i decyzji użytkownika przechowuj w `st.session_state`.
- Interfejs i komunikaty są w języku polskim.
- Pokazuj numer bieżącego kroku i pasek postępu.
- Kolejne kroki pozostają nieaktywne do spełnienia warunków wcześniejszego kroku.
- Status komunikuj tekstem i ikoną, nie wyłącznie kolorem.
- Każdy komunikat błędu wyjaśnia: co się stało, dlaczego blokuje dalszą pracę i co użytkownik powinien zrobić.
- Preferuj natywne komponenty Streamlit. Nie dodawaj własnego CSS ani JavaScriptu bez wyraźnej potrzeby.

## 9. Zasady kodowania

- Stosuj type hints dla publicznych funkcji i modeli danych.
- Preferuj `dataclass`, `Enum`, `pathlib`, `tempfile` i małe funkcje o jednej odpowiedzialności.
- Nie używaj `except:` ani pustych bloków obsługi błędów.
- Nie duplikuj logiki walidacji pomiędzy interfejsem, funkcjonalnościami i raportem.
- Nie umieszczaj logiki biznesowej w `app.py`.
- Nie wykonuj niepotrzebnych refaktoryzacji plików niezwiązanych z bieżącym zadaniem.
- Nie dodawaj abstrakcji, zależności ani konfiguracji, które nie są potrzebne w aktualnym MVP.

## 10. Testy

- Każde sprawdzenie posiada co najmniej test przypadku poprawnego i niepoprawnego.
- Testy jednostkowe nie uruchamiają interfejsu Streamlit.
- Dla każdej funkcjonalności testuj również jej `service.py` i agregację wyników.
- Test raportu otwiera wygenerowany plik XLSX i sprawdza wymagane arkusze oraz kluczowe wartości.
- Co najmniej jeden test AppTest sprawdza uruchomienie aplikacji i podstawowy przebieg interfejsu.
- Używaj małych, kontrolowanych plików z `tests/fixtures/`.
- Po każdej zmianie uruchom cały zestaw poleceniem `pytest`.
- Nie uznawaj zadania za ukończone, jeśli jakikolwiek test nie przechodzi.

## 11. Sposób pracy agenta

1. Przeczytaj odpowiednią część `PROJECT_SPEC.md` oraz istniejący kod i testy.
2. Przed implementacją krótko wskaż planowane pliki i testy.
3. Wprowadź najmniejszą zmianę realizującą bieżące wymaganie.
4. Dodaj lub zaktualizuj testy.
5. Uruchom cały zestaw `pytest`.
6. Jeśli testy nie przechodzą, zdiagnozuj i popraw problem w zakresie bieżącego zadania.
7. Na końcu podaj: zmienione pliki, zrealizowane wymagania, wynik testów i ewentualne nierozstrzygnięte kwestie.

