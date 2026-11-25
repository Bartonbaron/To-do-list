from datetime import datetime, timezone

from models import db, User, Task
from routes.admin import is_sensitive_column


# --- TESTY JEDNOSTKOWE MODELI I FUNKCJI WEWNĘTRZNYCH ---

def test_user_password_hashing_stores_secure_hash():
    """Sprawdza, czy hasło użytkownika jest hashowane i nie jest zapisywane jako tekst jawny."""
    user = User(username="jan_kowalski", email="jan@example.com")
    user.set_password("TajneHaslo123!")

    assert user.password_hash is not None
    assert user.password_hash != "TajneHaslo123!"
    assert user.check_password("TajneHaslo123!") is True


def test_user_password_verification_rejects_wrong_password():
    """Sprawdza, czy weryfikacja hasła zwraca False dla nieprawidłowego hasła."""
    user = User(username="jan_kowalski", email="jan@example.com")
    user.set_password("TajneHaslo123!")

    assert user.check_password("ZleHaslo123!") is False


def test_task_to_dict_returns_expected_fields(app):
    """Sprawdza, czy metoda to_dict modelu Task poprawnie serializuje wszystkie pola zadania."""
    with app.app_context():
        user = User(username="taskowner", email="owner@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        task = Task(title="Zadanie testowe", description="Opis testowy", user_id=user.id)
        db.session.add(task)
        db.session.commit()

        task_dict = task.to_dict()
        assert task_dict["id"] == task.id
        assert task_dict["title"] == "Zadanie testowe"
        assert task_dict["description"] == "Opis testowy"
        assert task_dict["completed"] is False
        assert "created_at" in task_dict


def test_task_to_dict_serializes_timestamp_as_iso8601():
    """Sprawdza, czy metoda to_dict serializuje znacznik czasu do formatu ISO 8601."""
    created_at = datetime(2026, 11, 24, 12, 30, tzinfo=timezone.utc)
    task = Task(
        id=1,
        title="Unit test task",
        description="",
        completed=False,
        created_at=created_at,
        user_id=1,
    )

    assert task.to_dict()["created_at"] == "2026-11-24T12:30:00+00:00"


def test_sensitive_column_allows_non_sensitive_column():
    """Sprawdza, czy standardowa kolumna (username) nie jest blokowana jako wrażliwa."""
    assert is_sensitive_column("username") is False


# --- TESTY JEDNOSTKOWE REJESTRACJI, LOGOWANIA I PROFILU ---

def test_register_valid_user_creates_account(client, app):
    """Sprawdza, czy rejestracja z prawidłowymi danymi tworzy użytkownika w bazie i zwraca token."""
    res = client.post('/api/auth/register', json={
        "username": "nowy_user",
        "email": "NOWY@Example.com",
        "password": "password123"
    })

    assert res.status_code == 201
    data = res.get_json()
    assert "token" in data
    assert data["user"]["username"] == "nowy_user"
    assert data["user"]["email"] == "nowy@example.com"
    assert data["user"]["is_admin"] is False

    with app.app_context():
        user_in_db = User.query.filter_by(username="nowy_user").first()
        assert user_in_db is not None
        assert user_in_db.email == "nowy@example.com"


def test_register_fails_when_username_too_short(client, app):
    """Sprawdza, czy rejestracja ze zbyt krótką nazwą użytkownika (< 3 znaki) jest odrzucana (400)."""
    res = client.post('/api/auth/register', json={
        "username": "ab",
        "email": "short@example.com",
        "password": "password123"
    })

    assert res.status_code == 400
    assert "message" in res.get_json()

    with app.app_context():
        assert User.query.filter_by(email="short@example.com").first() is None


def test_register_fails_when_username_too_long(client, app):
    """Sprawdza, czy rejestracja ze zbyt długą nazwą użytkownika (> 40 znaków) jest odrzucana (400)."""
    long_username = "u" * 41
    res = client.post('/api/auth/register', json={
        "username": long_username,
        "email": "long@example.com",
        "password": "password123"
    })

    assert res.status_code == 400
    assert "message" in res.get_json()

    with app.app_context():
        assert User.query.filter_by(email="long@example.com").first() is None


def test_register_fails_for_duplicate_username(client, registered_user):
    """Sprawdza, czy próba rejestracji z zajętą nazwą użytkownika zwraca błąd 409 Conflict."""
    res = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "inny_email@example.com",
        "password": "password123"
    })

    assert res.status_code == 409
    assert "message" in res.get_json()


def test_register_fails_for_duplicate_email(client, registered_user):
    """Sprawdza, czy próba rejestracji z zajętym adresem e-mail zwraca błąd 409 Conflict."""
    res = client.post('/api/auth/register', json={
        "username": "inny_user",
        "email": "test@example.com",
        "password": "password123"
    })

    assert res.status_code == 409
    assert "message" in res.get_json()


def test_login_with_valid_username_returns_token(client, registered_user):
    """Sprawdza, czy logowanie poprawną nazwą użytkownika i hasłem zwraca status 200 i token JWT."""
    res = client.post('/api/auth/login', json={
        "login": "testuser",
        "password": "password123"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data.get("token") is not None
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"


def test_login_with_valid_email_returns_token(client, registered_user):
    """Sprawdza, czy logowanie za pomocą adresu e-mail (niezależnie od wielkości liter) działa poprawnie."""
    res = client.post('/api/auth/login', json={
        "login": "TEST@example.com",
        "password": "password123"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data.get("token") is not None
    assert data["user"]["username"] == "testuser"


def test_login_fails_with_wrong_password(client, registered_user):
    """Sprawdza, czy logowanie z błędnym hasłem zwraca status 401 Unauthorized."""
    res = client.post('/api/auth/login', json={
        "login": "testuser",
        "password": "wrongpassword"
    })

    assert res.status_code == 401
    assert "token" not in res.get_json()


def test_login_fails_for_nonexistent_user(client):
    """Sprawdza, czy logowanie na nieistniejące konto zwraca status 401 Unauthorized."""
    res = client.post('/api/auth/login', json={
        "login": "ghost_user",
        "password": "password123"
    })

    assert res.status_code == 401
    assert "token" not in res.get_json()


def test_me_endpoint_returns_current_user_data(client, auth_headers):
    """Sprawdza, czy endpoint /api/auth/me zwraca poprawne dane zalogowanego użytkownika."""
    res = client.get('/api/auth/me', headers=auth_headers)

    assert res.status_code == 200
    user_data = res.get_json()["user"]
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    assert user_data["is_admin"] is False


# --- TESTY JEDNOSTKOWE ZADAŃ (CRUD I WALIDACJA) ---

def test_list_tasks_returns_empty_list_initially(client, auth_headers):
    """Sprawdza, czy dla nowego użytkownika lista zadań jest początkowo pusta."""
    res = client.get('/api/tasks', headers=auth_headers)

    assert res.status_code == 200
    assert res.get_json() == {"tasks": []}


def test_create_task_with_valid_data_persists_task(client, auth_headers, app):
    """Sprawdza, czy utworzenie zadania z prawidłowymi danymi zapisuje je w bazie i zwraca jego dane."""
    res = client.post('/api/tasks', json={
        "title": "Przetestować pipeline w GitHub Actions",
        "description": "Sprawdzić czy pytest przechodzi na zielono"
    }, headers=auth_headers)

    assert res.status_code == 201
    task_data = res.get_json()["task"]
    assert task_data["title"] == "Przetestować pipeline w GitHub Actions"
    assert task_data["description"] == "Sprawdzić czy pytest przechodzi na zielono"
    assert task_data["completed"] is False

    with app.app_context():
        task_in_db = db.session.get(Task, task_data["id"])
        assert task_in_db is not None
        assert task_in_db.title == "Przetestować pipeline w GitHub Actions"


def test_create_task_fails_when_title_is_empty(client, auth_headers, app):
    """Sprawdza, czy próba utworzenia zadania z pustym tytułem zwraca błąd 400 i nie zapisuje zadania."""
    res = client.post('/api/tasks', json={
        "title": "   ",
        "description": "Opis zadania bez tytułu"
    }, headers=auth_headers)

    assert res.status_code == 400
    assert "message" in res.get_json()

    with app.app_context():
        assert Task.query.count() == 0


def test_create_task_fails_when_title_exceeds_max_length(client, auth_headers, app):
    """Sprawdza, czy tytuł przekraczający 160 znaków jest odrzucany z kodem 400."""
    res = client.post('/api/tasks', json={
        "title": "A" * 161,
        "description": "Poprawny opis"
    }, headers=auth_headers)

    assert res.status_code == 400
    with app.app_context():
        assert Task.query.count() == 0


def test_create_task_fails_when_description_exceeds_max_length(client, auth_headers, app):
    """Sprawdza, czy opis przekraczający 1000 znaków jest odrzucany z kodem 400."""
    res = client.post('/api/tasks', json={
        "title": "Poprawny tytuł",
        "description": "D" * 1001
    }, headers=auth_headers)

    assert res.status_code == 400
    with app.app_context():
        assert Task.query.count() == 0


def test_update_task_modifies_title_and_completed_status(client, auth_headers):
    """Sprawdza, czy edycja własnego zadania faktycznie aktualizuje jego tytuł, opis i status wykonania."""
    create_res = client.post('/api/tasks', json={
        "title": "Stary tytuł",
        "description": "Stary opis"
    }, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    update_res = client.patch(f'/api/tasks/{task_id}', json={
        "title": "Nowy tytuł",
        "description": "Nowy opis",
        "completed": True
    }, headers=auth_headers)

    assert update_res.status_code == 200
    updated_task = update_res.get_json()["task"]
    assert updated_task["title"] == "Nowy tytuł"
    assert updated_task["description"] == "Nowy opis"
    assert updated_task["completed"] is True


def test_update_task_fails_with_invalid_completed_type(client, auth_headers):
    """Sprawdza, czy przekazanie wartości innej niż boolean w polu completed zwraca błąd 400."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    update_res = client.patch(f'/api/tasks/{task_id}', json={
        "completed": "tak"
    }, headers=auth_headers)

    assert update_res.status_code == 400
    assert "message" in update_res.get_json()


def test_update_task_fails_with_empty_title(client, auth_headers):
    """Sprawdza, czy próba zmiany tytułu zadania na pusty ciąg znaków kończy się błędem 400."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    update_res = client.patch(f'/api/tasks/{task_id}', json={
        "title": ""
    }, headers=auth_headers)

    assert update_res.status_code == 400


def test_update_nonexistent_task_returns_404(client, auth_headers):
    """Sprawdza, czy próba edycji nieistniejącego zadania zwraca kod 404 Not Found."""
    res = client.patch('/api/tasks/9999', json={"title": "Nowy tytuł"}, headers=auth_headers)

    assert res.status_code == 404


def test_delete_task_removes_it_from_database(client, auth_headers):
    """Sprawdza, czy usunięcie zadania faktycznie usuwa je z listy zadań użytkownika."""
    create_res = client.post('/api/tasks', json={"title": "Do usunięcia"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    del_res = client.delete(f'/api/tasks/{task_id}', headers=auth_headers)
    assert del_res.status_code == 200

    list_res = client.get('/api/tasks', headers=auth_headers)
    assert list_res.get_json()["tasks"] == []


def test_delete_nonexistent_task_returns_404(client, auth_headers):
    """Sprawdza, czy próba usunięcia nieistniejącego zadania zwraca błąd 404 Not Found."""
    res = client.delete('/api/tasks/9999', headers=auth_headers)

    assert res.status_code == 404
