# PROJECT_SPEC.md — Walidator IFC MVP

## 1. Cel i zakres

Aplikacja automatyzuje kontrolę jednego modelu IFC. Jest lokalną aplikacją webową uruchamianą na komputerze użytkownika.

Aplikacja:

- przyjmuje jeden plik IFC o wielkości od 10 B do 50 MB;
- oczekuje modelu zapisanego w schemacie IFC2X3;
- wykonuje kolejne grupy sprawdzeń jako oddzielne funkcjonalności;
- w wybranych funkcjonalnościach może przyjmować dodatkowe pliki XLSX lub DOCX;
- gromadzi wyniki wykonanych sprawdzeń;
- generuje Raport Kontroli w formacie XLSX.

Każde sprawdzenie posiada unikalny identyfikator i zwraca wynik w ujednoliconym formacie. Dodanie nowego sprawdzenia nie powinno wymagać zmiany interfejsu ani mechanizmu raportowania.

## 2. F-01 — Uruchomienie aplikacji

Aplikacja uruchamia się lokalnie poleceniem:

```bash
streamlit run app.py
```

Po uruchomieniu pokazuje polski interfejs oraz instrukcję rozpoczęcia kontroli.

## 3. F-02 — Wczytanie i walidacja modelu IFC

### 3.1. Wejście

Użytkownik przesyła jeden plik IFC przeznaczony do kontroli.

### 3.2. Sprawdzenia

| ID | Sprawdzenie | PASS | Brak spełnienia warunku |
|---|---|---|---|
| V-2.1 | Plik został przesłany | Przejdź dalej | Poproś o wybór pliku albo zakończenie kontroli |
| V-2.2 | Rozszerzenie pliku to `.ifc` | Przejdź dalej | Odrzuć plik; rozszerzenie nie jest dowodem poprawności zawartości |
| V-2.3 | Rozmiar wynosi od 10 B do 50 MB | Przejdź dalej | Pokaż rzeczywisty i dopuszczalny rozmiar |
| V-2.4 | Nagłówek zawiera `ISO-10303-21` | Przejdź dalej | Poinformuj, że plik nie wygląda na IFC-SPF |
| V-2.5 | Nagłówek zawiera `FILE_SCHEMA` | Przejdź dalej | Poinformuj, że plik jest błędnie wyeksportowany |
| V-2.6 | IfcOpenShell otwiera plik | Przejdź dalej | Przechwyć wyjątek i pokaż bezpieczny komunikat |
| V-2.7 | Model zawiera dokładnie jeden `IfcProject` | Przejdź dalej | Zablokuj audyt modelu bez `IfcProject` albo z wieloma `IfcProject` |
| V-2.8 | Schemat modelu to IFC2X3 | Przejdź dalej | Pokaż `WARNING`, odczytany schemat i poproś o akceptację przed przejściem dalej |

FAIL któregokolwiek sprawdzenia V-2.1–V-2.7 blokuje dalszy audyt. V-2.8 nie blokuje audytu po świadomej akceptacji ostrzeżenia przez użytkownika.

Po zakończeniu walidacji aplikacja pokazuje podsumowanie. Przejście do F-03 jest możliwe dopiero po spełnieniu powyższych warunków.

## 4. F-03 — Weryfikacja metadanych pliku i modelu

### 4.1. Dane do prezentacji

| ID | Dane | Gdy wartość jest dostępna | Gdy wartości nie można pobrać |
|---|---|---|---|
| V-3.1 | Nazwa pliku | Pokaż wartość | Pokaż „Brak możliwości pobrania nazwy pliku” |
| V-3.2 | `IfcProject.Name` | Pokaż wartość | Pokaż „Brak wartości IfcProject.Name” |
| V-3.3 | Lista wartości `IfcBuilding.Name` | Pokaż listę | Pokaż „Brak budynku IFC” |
| V-3.4 | Lista wartości `IfcSite.Name` | Pokaż listę | Pokaż „Brak IfcSite” |
| V-3.5 | Rozmiar pliku w MB | Pokaż wartość | Pokaż „Nie można pobrać rozmiaru pliku” |
| V-3.6 | Łączna liczba encji w modelu | Pokaż wartość | Pokaż „Nie można pobrać liczby encji” |

### 4.2. Ocena użytkownika

- Dane są prezentowane w tabeli.
- Dla każdej pozycji użytkownik wybiera `PASS` albo `FAIL`.
- Ocena jest ręczną decyzją użytkownika.
- Komentarz jest opcjonalny.
- Przejście do kolejnego kroku wymaga nadania statusu wszystkim pozycjom.

## 5. F-04 — Weryfikacja dopuszczalnych klas IFC

### 5.1. Plik z listą klas

Użytkownik przesyła plik XLSX zawierający listę dopuszczalnych klas IFC. Wymagana nazwa kolumny: `IfcClass`.

Wymagania dla pliku:

- plik XLSX musi dać się otworzyć;
- jeśli skoroszyt zawiera kilka arkuszy, użytkownik wybiera jeden z nich;
- wybrany arkusz musi zawierać niepustą kolumnę `IfcClass`;
- białe znaki na początku i końcu wartości są usuwane;
- puste wartości są pomijane;
- duplikaty są usuwane;
- nazwy klas są porównywane dokładnie po usunięciu białych znaków.

Jeżeli pliku nie można poprawnie wczytać, użytkownik może:

- przesłać inny plik;
- pominąć F-04 i przejść do następnego kroku;
- zakończyć całą kontrolę.

Pominięta funkcjonalność otrzymuje status `SKIPPED`.

### 5.2. Sprawdzenie klas

- Sprawdzenie obejmuje wszystkie instancje `IfcProduct` wraz z podtypami.
- Dla każdej instancji pobierz dokładną klasę przez `entity.is_a()`.
- Pogrupuj instancje według klasy.
- Porównaj klasy występujące w modelu z listą z kolumny `IfcClass`.
- Dodaj do wyniku również klasy dopuszczalne, które nie występują w modelu, z liczbą wystąpień równą `0`.

Tabela wynikowa zawiera kolumny:

| Kolumna | Zawartość |
|---|---|
| Klasa IFC | Dokładna nazwa klasy IFC |
| Liczba wystąpień | Liczba instancji danej klasy w modelu |
| Czy klasa dopuszczalna | `Tak` albo `Nie` |

## 6. F-05 — Weryfikacja szczegółowa parametrów IfcWall

Zakres funkcjonalności nie został jeszcze określony. F-05 nie może być implementowana do czasu uzupełnienia i zatwierdzenia wymagań.

## 7. F-06 — Generowanie raportu

### 7.1. Plik wynikowy

- Format: XLSX.
- Nazwa: `Raport_z_kontroli_<nazwa_pliku_bez_rozszerzenia>.xlsx`.
- Raport jest generowany w pamięci i udostępniany użytkownikowi do pobrania.

### 7.2. Arkusz `Podsumowanie`

Arkusz zawiera:

- nazwę kontrolowanego pliku;
- datę i godzinę wykonania kontroli;
- listę wykonanych funkcjonalności i sprawdzeń;
- status każdego sprawdzenia;
- komentarze użytkownika;
- informację o funkcjonalnościach pominiętych.

Status całej kontroli wynosi `FAIL`, jeżeli co najmniej jedno wykonane sprawdzenie ma status `FAIL` albo `ERROR`. W przeciwnym razie status całej kontroli wynosi `PASS`. Status `SKIPPED` pozostaje widoczny w raporcie.

### 7.3. Arkusz `F-03 Weryfikacja Metadanych`

Arkusz zawiera tytuł „F-03 Weryfikacja metadanych pliku i modelu” oraz tabelę z wynikami V-3.1–V-3.6, statusami i komentarzami użytkownika.

### 7.4. Arkusz `F-04 Weryfikacja Klas IFC`

Arkusz zawiera tytuł „F-04 Weryfikacja dopuszczalnych klas IFC” oraz tabelę wynikową opisaną w punkcie 5.2.

## 8. Wymagania UX

- Na górze strony znajduje się numer bieżącego kroku i pasek postępu.
- Kolejne kroki są nieaktywne do czasu spełnienia warunków wcześniejszego kroku.
- Status jest komunikowany tekstem i ikoną, nie wyłącznie kolorem.
- Każdy błąd informuje: co się stało, dlaczego blokuje dalszą pracę i co użytkownik powinien zrobić.

## 9. Kryteria akceptacji

- `streamlit run app.py` uruchamia aplikację bez błędu.
- Poprawne pliki testowe IFC2X3 i XLSX pozwalają wykonać F-02–F-04 oraz pobrać raport XLSX.
- Błędne dane blokują właściwy krok i wyświetlają instrukcję poprawy.
- Wyniki raportu są zgodne z danymi testowymi.
- Wszystkie testy uruchamiane poleceniem `pytest` przechodzą bez błędów.

