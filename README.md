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

Nie commituj pliku `.env`, tokenów ani bazy danych (pliki .db) zawierającej prawdziwe dane użytkowników.

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
---

## Wymagania środowiskowe

Do uruchomienia projektu wymagane są:
* **Docker** wraz z **Docker Compose** lub **Podman** z `podman-compose` (zalecane do uruchomienia w kontenerach)
* Alternatywnie (do uruchomienia lokalnego bez kontenerów):
  * **Python** 3.10+ (Backend)
  * **Node.js** 18+ oraz `npm` (Frontend)

---

## Sposób instalacji

1. **Sklonuj repozytorium na dysk:**
   ```bash
   git clone <ADRES_TWOJEGO_REPOZYTORIUM>
   cd To-do-list
   ```

2. **Skonfiguruj zmienne środowiskowe:**
   Skopiuj przykładowy plik konfiguracyjny `.env.example` do pliku `.env`:
   ```bash
   cp .env.example .env
   ```

---

## Sposób uruchomienia

### Opcja 1: Za pomocą kontenerów (Podman / Docker) – zalecana
W głównym katalogu projektu (tam, gdzie znajduje się plik `compose.yaml`) wykonaj:

```bash
# Dla Podmana:
podman compose up -d --build

# Dla Dockera:
docker compose up -d --build
```

Aby uruchomić testy jednostkowe backendu wewnątrz kontenera:
```bash
podman compose exec backend pytest
```

### Opcja 2: Uruchomienie lokalne (bez kontenerów)

**Backend (Flask):**
```bash
cd backend
python -m venv venv
# Aktywacja środowiska (Windows PowerShell): .\venv\Scripts\Activate.ps1
# Aktywacja środowiska (Linux/macOS): source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Frontend (React + Vite):**
```bash
cd frontend
npm install
npm run dev
```

---

## Adres aplikacji

Po uruchomieniu poszczególne usługi są dostępne pod adresami:
* **Frontend (Aplikacja webowa):** `http://localhost:5173` (lub `http://localhost:80` / port zdefiniowany w `compose.yaml`)
* **Backend (REST API):** `http://localhost:5000`
* **Healthcheck API:** `http://localhost:5000/api/health`

---

## Opis endpointów API

Wszystkie endpointy poza rejestracją, logowaniem oraz `/api/health` wymagają przekazania tokenu JWT w nagłówku:
`Authorization: Bearer <token_jwt>`

| Metoda | Endpoint | Wymaga JWT | Opis |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/health` | Nie | Sprawdzenie stanu działania serwera API |
| `POST` | `/api/auth/register` | Nie | Rejestracja nowego użytkownika (zwraca token JWT) |
| `POST` | `/api/auth/login` | Nie | Logowanie użytkownika po nazwie lub e-mailu (zwraca token JWT) |
| `GET` | `/api/auth/me` | Tak | Pobranie danych aktualnie zalogowanego użytkownika |
| `GET` | `/api/tasks` | Tak | Pobranie listy wszystkich zadań zalogowanego użytkownika |
| `POST` | `/api/tasks` | Tak | Utworzenie nowego zadania |
| `PUT` / `PATCH` | `/api/tasks/<id>` | Tak | Aktualizacja istniejącego zadania (np. zmiana statusu/tytułu) |
| `DELETE` | `/api/tasks/<id>` | Tak | Usunięcie zadania o podanym ID |

---

## Przykładowe żądania (Requests)

### 1. Sprawdzenie statusu API (`/api/health`)
```bash
curl -X GET http://localhost:5000/api/health
```
**Odpowiedź (200 OK):**
```json
{
  "status": "ok"
}
```

### 2. Rejestracja użytkownika (`/api/auth/register`)
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jan_kowalski",
    "email": "jan@example.com",
    "password": "SilneHaslo123"
  }'
```
**Odpowiedź (201 Created):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "jan_kowalski",
    "email": "jan@example.com"
  }
}
```

### 3. Logowanie użytkownika (`/api/auth/login`)
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "login": "jan_kowalski",
    "password": "SilneHaslo123"
  }'
```

### 4. Utworzenie nowego zadania (`/api/tasks`)
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TWOJ_TOKEN_JWT>" \
  -d '{
    "title": "Przygotować pipeline CI/CD",
    "description": "Skonfigurować automatyczne testy w GitHub Actions"
  }'
```

### 5. Pobranie listy zadań (`/api/tasks`)
```bash
curl -X GET http://localhost:5000/api/tasks \
  -H "Authorization: Bearer <TWOJ_TOKEN_JWT>"
```
**Odpowiedź (200 OK):**
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Przygotować pipeline CI/CD",
      "description": "Skonfigurować automatyczne testy w GitHub Actions"
    }
  ]
}
```