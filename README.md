<!-- Improved compatibility of back to top link: See: https://github.com/pull/73 -->
<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

<!-- PROJECT LOGO AND TITLE -->
<p align="center">
  <h2 align="center">PIT-38 Calculator dla Trading 212</h2>
  <p align="center">
    Automatyczny kalkulator podatku PIT-38 na podstawie historii transakcji z Trading 212 (Invest & CFD).
    <br />
    <a href="#uwagi-podatkowe"><strong>Spis treści »</strong></a>
    <br />
    <a href="https://github.com/r00bertos1/pit-38-trading-212/issues/new?template=bug_report.md">Zgłoś błąd</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Spis Treści</summary>
  <ol>
    <li><a href="#about">O Projekcie</a></li>
    <li><a href="#start">Jak zacząć</a></li>
    <li><a href="#use">Instrukcja eksportu danych</a></li>
    <li><a href="#uwagi-podatkowe">Oświadczenie</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## <a name="about"></a>O Projekcie

Prosty skrypt w języku Python, który automatycznie oblicza wartości do formularza PIT-38 na podstawie historii transakcji z platformy Trading 212 (konta Invest oraz CFD). 

Skrypt przelicza transakcje w walutach obcych na PLN, automatycznie pobierając z API NBP **średnie kursy  z ostatniego dnia roboczego poprzedzającego dzień uzyskania przychodu lub poniesienia kosztu (d-1)**. Ponadto poprawnie wdraża **metodę FIFO** (First In, First Out) wymaganą dla kont Invest (akcji / ETF).

[🔝 Powrót na górę](#readme-top)

<!-- GETTING STARTED -->
## <a name="start"></a>Jak zacząć

Aby uruchomić projekt na swoim komputerze, postępuj zgodnie z poniższymi instrukcjami.

### Wymagania:
* Zainstalowany `Python 3`

### Instalacja i Uruchomienie:

1. Po pobraniu projektu zainstaluj wymagane biblioteki (m.in. do obsługi zapytań API):
```bash
pip install -r requirements.txt
```

2. Umieść pliki z danymi w odpowiednim folderze (domyślnie `data/2025/`). Oczekiwane nazwy plików to `trading-212-invest.csv` i `trading-212-cfd.json`.

3. Uruchom skrypt podając rok, dla którego chcesz policzyć podatek:
```bash
python pit38_calculator.py --rok 2025
```

Możesz również podać własną ścieżkę do plików z danymi:
```bash
python pit38_calculator.py --rok 2024 --dir inna_sciezka_na_dysku
```

[🔝 Powrót na górę](#readme-top)

<!-- USAGE -->
## <a name="use"></a>Instrukcja eksportu danych z Trading 212

Aby skrypt poprawnie obliczył podatek, musisz wyeksportować historię ze swoich kont. Skrypt wymaga osobnego pliku dla konta Invest oraz osobnego dla konta CFD.

### 1. Eksport danych z konta Invest (Akcje / ETF)
*(na podstawie poradnika z [KalkulatorGieldowy.pl](https://kalkulatorgieldowy.pl/articles/manuals/trading212.html))*

Rozliczenie konta Invest dotyczy obrotu na akcjach, ETF, wypłaconych dywidend oraz odsetek z wolnych środków.

1. Zaloguj się na swoje konto Trading 212 i przejdź do sekcji Historii.
2. Wybierz opcję eksportu danych do pliku CSV.
3. **Bardzo ważne (FIFO):** Raport z Trading212 Invest musi obejmować dane **od samego początku istnienia konta**, a nie tylko ze stycznia danego roku z którego się rozliczasz! Dzięki jednoczesnemu wczytaniu całej historii, skrypt prawidłowo obliczy koszty według metody FIFO.
4. Ustawiając zakres wyeksportuj raporty dla poszczególnych lat (T212 pozwala wyeksportować max 1 rok kalendarzowy).
5. Złącz pobrane pliki ze sobą lub umieść plik transakcji jako `trading-212-invest.csv` we właściwym folderze danego roku (np. `data/2025/trading-212-invest.csv`). Skrypt sam przeparsuje właściwe rekordy z ubiegłych lat w poszukiwaniu cen zakupu.

### 2. Eksport danych z konta CFD
*(autorem tego rozwiązania jest [DarkSpine433](https://github.com/DarkSpine433/T212-CFD-DATA))*

Rozliczenie konta CFD wymaga zastosowania małego skryptu wbudowanego przez społeczność, wyciągającego m.in. kluczowe opłaty overnight fees.

**Opcja A: Poprzez pasek zakładek (Bookmarklet) - Zalecana**
1. Wejdź na oficjalną stronę [T212-CFD-DATA Exporter](https://darkspine433.github.io/T212-CFD-DATA/).
2. Przeciągnij zielony przycisk z rakietą "T212 Export Tool" na swój pasek zakładek w przeglądarce.
3. Zaloguj się do swojego konta Trading 212 i upewnij się, że jesteś w zakładce konta **CFD**.
4. Kliknij w dodaną przed chwilą zakładkę. W okienkach podaj walutę konta (np. PLN) oraz ramy czasowe z rozliczanego roku podatkowego (od stycznia, do końca grudnia).
5. Pobierz wygenerowany plik, zmień jego nazwę na `trading-212-cfd.json` i wrzuć do (np. `data/2025/trading-212-cfd.json`). 

**Opcja B: Przez konsolę F12 Developer Tools**
1. Otwórz Chrome lub Firefox, zaloguj się do konta CFD w Trading 212 w przeglądarce.
2. Wciśnij na klawiaturze `F12` i wejdź do zakładki **Console / Konsola**.
3. Skopiuj kod ze strony projektu od [DarkSpinez433](https://darkspine433.github.io/T212-CFD-DATA/).
4. Wklej ten kod w konsolę. (Uwaga: Przeglądarka ze względów bezpieczeństwa czasem poprosi najpierw o wpisanie hasła zaporowego jak np. `allow pasting` zanim pozwoli puścić skrypt).
5. Naciśnij Enter i postępuj wedle takich samych kroków (wybór waluty, wybór dat od i do).


[🔝 Powrót na górę](#readme-top)


## <a name="uwagi-podatkowe"></a>⚠️ Oświadczenie i Użycie

Narzędzie i kalkulator zostały przygotowane w dobrej wierze jako materiał *open-source*. Są one udostępniane "tak jak są" (as-is), całkowicie za darmo i jako "hobby" projekt. 
Autor **nie przejmuje odpowiedzialności** za ewentualne nieścisłości, błędy w wygenerowanych statystykach, ewentualne luki logiki przeliczania kursu NBP w nietypowe święta międzynarodowe ani za prawne i podatkowe utrudnienia przy błędnym wypełnianiu PIT-38 na ich podstawie. Skrypt to jedynie estymacja dla pomocy w osobistym rozliczeniu. Pamiętaj, aby potwierdzać wyniki u doradcy lub księgowego.


<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/r00bertos1/pit-38-trading-212.svg?style=for-the-badge
[contributors-url]: https://github.com/r00bertos1/pit-38-trading-212/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/r00bertos1/pit-38-trading-212.svg?style=for-the-badge
[forks-url]: https://github.com/r00bertos1/pit-38-trading-212/network/members
[stars-shield]: https://img.shields.io/github/stars/r00bertos1/pit-38-trading-212.svg?style=for-the-badge
[stars-url]: https://github.com/r00bertos1/pit-38-trading-212/stargazers
[issues-shield]: https://img.shields.io/github/issues/r00bertos1/pit-38-trading-212.svg?style=for-the-badge
[issues-url]: https://github.com/r00bertos1/pit-38-trading-212/issues
[license-shield]: https://img.shields.io/github/license/r00bertos1/pit-38-trading-212.svg?style=for-the-badge
[license-url]: https://github.com/r00bertos1/pit-38-trading-212/blob/master/LICENSE.txt
