# Walidator_IFC-
Zautomatyzowana walidacja pliku ifc

1.	Ogólny opis aplikacji
•	Aplikacja webowa w języku Python, uruchamiana lokalnie na komputerze użytkownika. 
•	Aplikacja przyjmuje jeden plik IFC o wielkości do 50 MB. Wersja demonstracyjna obsługuje modele zapisane w schemacie IFC2X3. 
•	Po wczytaniu i walidacji pliku aplikacja wykonuje kolejne grupy sprawdzeń opisane jako odrębne funkcjonalności. 
•	Każde sprawdzenie jest niezależną funkcją lub klasą, zwracającą wynik w ujednoliconym formacie. Dodanie nowego sprawdzenia nie powinno wymagać zmiany interfejsu ani mechanizmu raportowania. 
•	Wybrane funkcjonalności mogą przyjmować dodatkowe pliki XLSX lub DOCX. Obsługa każdego formatu jest wydzielona od logiki sprawdzeń. 
•	Wyniki wszystkich wykonanych sprawdzeń są gromadzone w czasie działania aplikacji. W ostatnim kroku aplikacja generuje Raport Kontroli w formacie XLSX, zawierający podsumowanie oraz wyniki poszczególnych funkcjonalności.
