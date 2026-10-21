# Wymagania projektowe - System Zarządzania Zadaniami (TaskFlow)

Dokument zawiera specyfikację wymagań funkcjonalnych, niefunkcjonalnych, bezpieczeństwa oraz model zagrożeń dla Etapu 1 projektu z przedmiotu Projektowanie, Bezpieczeństwo i Operacje (DevSecOps).

---

## 1. Cel aplikacji

Aplikacja "TaskFlow" to prosty system webowy przeznaczony do zarządzania zadaniami osobistymi (ang. To-Do List). Głównym celem systemu jest umożliwienie użytkownikom rejestracji, uwierzytelniania oraz bezpiecznego organizowania własnej pracy poprzez tworzenie, edycję, oznaczanie statusu i usuwanie zadań.

Aplikacja gwarantuje pełną izolację danych: żaden użytkownik nie ma wglądu w listę zadań innych zarejestrowanych osób.

---

## 2. Rodzaje użytkowników i uprawnienia (RBAC)

W systemie zdefiniowano następujące role użytkowników:

### 2.1. Użytkownik niezalogowany (Gość)

Jest to każda osoba odwiedzająca aplikację przed procesem uwierzytelnienia.

- Możliwości:
  - Przeglądanie strony głównej i powitalnej.
  - Rejestracja nowego konta poprzez podanie unikalnej nazwy użytkownika oraz hasła spełniającego reguły złożoności.
  - Logowanie do istniejącego konta (uwierzytelnianie).
- Ograniczenia:
  - Brak dostępu do modułu zadań.
  - Próba wywołania jakiegokolwiek chronionego zasobu API skutkuje błędem HTTP 401 Unauthorized.

### 2.2. Użytkownik zalogowany (Standardowy)

Użytkownik, który przeszedł pomyślnie proces uwierzytelnienia i posiada ważny token sesyjny (JWT).

- Możliwości:
  - Wyświetlanie listy wyłącznie własnych zadań.
  - Tworzenie nowych zadań (tytuł, opis, priorytet, termin).
  - Edycja treści, priorytetu oraz terminu własnych zadań.
  - Zmiana statusu zadania (do zrobienia, w trakcie, zakończone).
  - Usuwanie własnych zadań z bazy danych.
  - Wylogowanie się z aplikacji (unieważnienie sesji po stronie klienta).
- Ograniczenia:
  - Ścisła izolacja: brak możliwości podglądu, edycji ani usunięcia zadań należących do innych użytkowników.
  - Brak uprawnień do operacji administracyjnych.

### 2.3. Administrator systemu (Rola opcjonalna / techniczna)

Rola przeznaczona do celów serwisowych i nadzoru nad platformą.

- Możliwości:
  - Przeglądanie logów bezpieczeństwa oraz statystyk systemowych (np. liczba zarejestrowanych kont).
  - Blokowanie kont użytkowników naruszających zasady bezpieczeństwa (np. wykrycie prób ataków typu Brute-Force).
- Ograniczenia:
  - Zgodnie z zasadą prywatności (Privacy by Design), administrator nie ma bezpośredniego wglądu w prywatne treści zadań użytkowników.

### 2.4. Macierz uprawnień

| Akcja / Zasób                    | Użytkownik niezalogowany | Użytkownik standardowy | Administrator |
| :------------------------------- | :----------------------: | :--------------------: | :-----------: |
| Rejestracja konta                |           Tak            |          Nie           |      Nie      |
| Logowanie do systemu             |           Tak            |          Nie           |      Tak      |
| Przeglądanie własnych zadań      |           Nie            |          Tak           |      Nie      |
| Tworzenie nowych zadań           |           Nie            |          Tak           |      Nie      |
| Edycja / Usuwanie własnych zadań |           Nie            |          Tak           |      Nie      |
| Dostęp do zadań innych osób      |           Nie            |          Nie           |      Nie      |
| Podgląd logów audytowych         |           Nie            |          Nie           |      Tak      |
| Blokada konta użytkownika        |           Nie            |          Nie           |      Tak      |

---

## 3. Wymagania funkcjonalne

1. **Rejestracja użytkownika:** System umożliwia założenie nowego konta przy użyciu unikalnej nazwy użytkownika i hasła.
2. **Uwierzytelnianie użytkownika:** System weryfikuje dane logowania i wystawia token sesyjny (JWT) z ograniczonym czasem ważności.
3. **Pobieranie listy zadań:** Zalogowany użytkownik może pobrać listę wyłącznie swoich zadań.
4. **Dodawanie zadań:** Użytkownik może dodać nowe zadanie zawierające co najmniej tytuł oraz opcjonalny opis.
5. **Edycja i zmiana statusu:** Użytkownik może edytować istniejące zadanie oraz oznaczyć je jako wykonane.
6. **Usuwanie zadań:** Użytkownik może usunąć wybrane przez siebie zadanie.
7. **Wylogowanie:** System umożliwia zakończenie sesji i usunięcie tokenu autoryzacyjnego.

---

## 4. Wymagania pod kątem bezpieczeństwa

1. **Bezpieczne hashowanie haseł:** Hasła użytkowników nie są przechowywane w postaci jawnej; system używa silnego algorytmu hashującego z unikalną solą.
2. **Kontrola dostępu na poziomie obiektu (BOLA / IDOR Protection):** Backend sprawdza przy każdym żądaniu, czy edytowany lub usuwany zasób zadania należy do identyfikatora użytkownika zapisanego w tokenie sesyjnym.
3. **Ochrona przed SQL Injection:** Wszelkie zapytania do bazy danych są realizowane za pomocą mechanizmu ORM i zapytań parametryzowanych.
4. **Walidacja i sanityzacja danych:** Dane wejściowe przesyłane przez formularze są rygorystycznie walidowane po stronie backendu; frontend zabezpiecza dane przed wstrzyknięciem skryptów.
5. **Ochrona przed atakami Brute-Force (Rate Limiting):** Punkty końcowe logowania i rejestracji mają nałożone limity liczby zapytań na minutę z danego adresu IP.
6. **Szyfrowanie komunikacji (HTTPS / TLS):** Całość komunikacji pomiędzy klientem a serwerem odbywa się z wykorzystaniem szyfrowania TLS.
7. **Bezpieczne zarządzanie konfiguracją:** Tajne klucze, w tym klucz do podpisywania tokenów JWT, są wstrzykiwane za pomocą zmiennych środowiskowych i nie trafiają do repozytorium kodu.

---

## 5. Model zagrożeń (Threat Model)

| Zagrożenie                                         | Czego dotyczy                                                            | Możliwe konsekwencje                                                                           | Planowana kontrola / Działanie                                                                                                                             |
| :------------------------------------------------- | :----------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nieautoryzowany dostęp do cudzych zadań (IDOR)** | Endpointy operacji na zadaniach (`GET`, `PUT`, `DELETE /api/tasks/{id}`) | Użytkownik modyfikuje ID w żądaniu i odczytuje lub usuwa zadania innej osoby.                  | Backend każdorazowo weryfikuje relację: `task.user_id == current_user.id`. W przypadku braku zgodności zwracany jest błąd 403 Forbidden lub 404 Not Found. |
| **Atak słownikowy / Brute-Force na logowanie**     | Endpoint uwierzytelniania (`POST /api/auth/login`)                       | Przejęcie konta użytkownika w wyniku odgadnięcia słabego hasła.                                | Implementacja limitowania zapytań (Rate Limiting) oraz wymuszenie polityki minimalnej długości hasła (min. 8 znaków).                                      |
| **Wyciek bazy danych i kradzież poświadczeń**      | Tabela użytkowników w bazie danych                                       | Ujawnienie haseł użytkowników i ryzyko ataku Credential Stuffing w innych serwisach.           | Zastosowanie algorytmu haszującego bcrypt z dynamiczną solą; uniemożliwienie odzyskania haseł w postaci jawnej.                                            |
| **Wstrzyknięcie złośliwego kodu (Stored XSS)**     | Pola tekstowe zadania (tytuł, opis zadania)                              | Wykonanie złośliwego skryptu JavaScript w przeglądarce innego użytkownika lub przejęcie sesji. | Odpowiednie filtrowanie znaków na backendzie oraz automatyczne uciekanie encji HTML realizowane przez bibliotekę React podczas renderowania widoku.        |
