# Aplikacja Lista Zadań

## Członkowie zespołu

- Bartosz Bazan
- Jakub Ryczan
- Adam Czuchra

## Wybrany stos technologiczny

- Backend: Python + Flask
- Frontend: React / HTML / CSS
- Baza danych: SQLite

## Krótki opis projektu

Aplikacja jest prostym systemem typu lista zadań (ToDo list), który umożliwia użytkownikom rejestrację, bezpieczne logowanie oraz zarządzanie wyłącznie własnymi zadaniami. Głównym celem projektu jest dostarczenie wygodnego narzędzia do organizowania codziennych obowiązków z zachowaniem poufności danych użytkownika.

## Wymagania

- Python 3.10+
- Node.js 18+
- npm

## Uruchomienie backendu

W terminalu, w katalogu projektu:

```bash
cd backend
python -m venv .venv
```

Aktywacja środowiska:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Następnie:

```bash
pip install -r requirements.txt
```

Skopiuj `.env.example` do `.env` i ustaw własne, losowe wartości `SECRET_KEY`, `JWT_SECRET_KEY` oraz `ADMIN_PASSWORD`.
Na Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Uruchom serwer:

```bash
python app.py
```

Backend działa pod adresem `http://127.0.0.1:5000`. Baza `todo.db` utworzy się automatycznie.

## Uruchomienie frontendu

W drugim terminalu:

```bash
cd frontend
npm install
npm run dev
```

Otwórz `http://localhost:5173`.

## Endpointy API

| Metoda | Endpoint             | Dostęp    | Opis                                     |
| ------ | -------------------- | --------- | ---------------------------------------- |
| POST   | `/api/auth/register` | publiczny | Rejestracja                              |
| POST   | `/api/auth/login`    | publiczny | Logowanie                                |
| GET    | `/api/auth/me`       | JWT       | Dane zalogowanego użytkownika            |
| GET    | `/api/tasks`         | JWT       | Lista własnych zadań                     |
| POST   | `/api/tasks`         | JWT       | Dodanie zadania                          |
| PATCH  | `/api/tasks/<id>`    | JWT       | Edycja / zmiana statusu własnego zadania |
| DELETE | `/api/tasks/<id>`    | JWT       | Usunięcie własnego zadania               |
| GET    | `/api/health`        | publiczny | Status API                               |
| GET    | `/api/admin/database` | admin JWT | Struktura bazy i liczba rekordów         |

## Bezpieczeństwo i ważne uwagi

- Hasła są przechowywane jako bezpieczne hashe, nigdy jako tekst jawny.
- Każde zapytanie dotyczące zadania filtruje po identyfikatorze zalogowanego użytkownika. Próba dostępu do cudzego zadania kończy się odpowiedzią 404.
- API wymaga tokenu JWT dla operacji na zadaniach.
- Token jest przechowywany w `localStorage`, co jest wygodne dla projektu edukacyjnego, ale aplikacja produkcyjna powinna rozważyć tokeny w ciasteczkach `HttpOnly`, `Secure`, `SameSite` i dodatkowe zabezpieczenia CSRF.
- Przed wdrożeniem ustaw silne sekrety, wyłącz tryb debug, skonfiguruj HTTPS, ograniczenia CORS, limity prób logowania i kopie zapasowe.
- SQLite jest odpowiednia dla małej aplikacji demonstracyjnej; przy większym ruchu rozważ PostgreSQL.

## Git

Nie commituj pliku `.env`, tokenów ani bazy danych zawierającej prawdziwe dane użytkowników.

## Uruchomienie przez Podman (zalecane)

Wymagany jest Podman oraz `podman compose` (dostawca Compose, np. `podman-compose`).

1. W katalogu głównym projektu skopiuj przykładową konfigurację:

   ```bash
   cp .env.example .env
   ```

2. Wygeneruj dwa różne sekrety i wpisz je do `.env`. Możesz użyć:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Uruchom polecenie dwa razy i wklej wyniki odpowiednio do `SECRET_KEY` oraz `JWT_SECRET_KEY`.

3. Zbuduj obrazy i uruchom aplikację:

   ```bash
   podman compose up -d --build
   ```

4. Otwórz aplikację: http://localhost:8080

Przydatne polecenia:

```bash
podman compose ps
podman compose logs -f
podman compose down
```

`podman compose down` zatrzymuje i usuwa kontenery, ale pozostawia wolumen `todo_data`, w którym znajduje się baza SQLite. **Nie używaj `podman compose down -v`, jeśli chcesz zachować dane** — opcja `-v` usuwa również wolumen.

Frontend jest serwowany przez Nginx, który przekazuje żądania `/api/` do backendu Flask. Dzięki temu przeglądarka korzysta z jednego adresu i nie trzeba wystawiać portu backendu na hosta.

Plik `.env` zawiera sekrety — nie dodawaj go do repozytorium. Nie używaj przykładowych wartości w środowisku produkcyjnym.

Przy pierwszym uruchomieniu backend utworzy konto administratora na podstawie `ADMIN_USERNAME`, `ADMIN_EMAIL` i `ADMIN_PASSWORD`. Domyślna nazwa to `admin`, a hasło musi mieć co najmniej 8 znaków. Panel administratora pokazuje strukturę tabel i ich zawartość, ale ukrywa hasła, sekrety, tokeny oraz ich hashe.

## Tryb deweloperski z hot reload

Do pracy nad kodem można użyć osobnego pliku Compose z Vite HMR i przeładowywaniem backendu Flask:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

W tym trybie frontend jest dostępny pod adresem http://localhost:5173, a backend pod http://localhost:5000. Zmiany w plikach `frontend` i `backend` są wykrywane automatycznie. Aby zatrzymać środowisko:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml down
```
