from datetime import datetime, timezone

from models import db, User, Task
from routes.admin import is_sensitive_column


def test_health_endpoint_returns_ok_status(client):
    """Sprawdza, czy endpoint /api/health zwraca status 200 oraz poprawną strukturę JSON."""
    res = client.get('/api/health')

    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


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


def test_sensitive_column_detects_password_hash():
    assert is_sensitive_column("password_hash") is True


def test_sensitive_column_detects_access_token():
    assert is_sensitive_column("access_token") is True


def test_sensitive_column_detects_secret_marker_case_insensitively():
    assert is_sensitive_column("API_SECRET_KEY") is True


def test_sensitive_column_detects_token_marker_in_column_name():
    assert is_sensitive_column("refresh_token_expiry") is True


def test_sensitive_column_allows_non_sensitive_column():
    assert is_sensitive_column("username") is False


def test_admin_database_endpoint_returns_tables_for_admin(client, admin_headers):
    """Sprawdza, czy administrator może pobrać strukturę bazy oraz że wrażliwe kolumny są ukryte."""
    res = client.get('/api/admin/database', headers=admin_headers)

    assert res.status_code == 200
    data = res.get_json()
    assert "tables" in data

    user_table = next((t for t in data["tables"] if t["name"] == "user"), None)
    assert user_table is not None
    column_names = [col["name"] for col in user_table["columns"]]
    assert "username" in column_names
    assert "password_hash" not in column_names


def test_admin_database_endpoint_denies_regular_user(client, auth_headers):
    """Sprawdza, czy zwykły zalogowany użytkownik nie ma dostępu do panelu administratora (błąd 403)."""
    res = client.get('/api/admin/database', headers=auth_headers)

    assert res.status_code == 403
    assert "message" in res.get_json()
