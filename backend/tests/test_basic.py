from models import db, User, Task


def test_health_endpoint_returns_ok_status(client):
    """Sprawdza, czy endpoint /api/health zwraca status 200 oraz poprawną strukturę JSON."""
    res = client.get('/api/health')

    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_user_password_hashing_stores_secure_hash(app):
    """Sprawdza, czy hasło użytkownika jest hashowane i nie jest zapisywane jako tekst jawny."""
    user = User(username="jan_kowalski", email="jan@example.com")
    user.set_password("TajneHaslo123!")

    assert user.password_hash is not None
    assert user.password_hash != "TajneHaslo123!"
    assert user.check_password("TajneHaslo123!") is True


def test_user_password_verification_rejects_wrong_password(app):
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
