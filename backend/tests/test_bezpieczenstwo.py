from routes.admin import is_sensitive_column


# --- SCENARIUSZE BEZPIECZEŃSTWA (Wymagane: min. 2) ---

def test_me_endpoint_fails_without_token(client):
    """Sprawdza, czy wywołanie /api/auth/me bez tokenu JWT zwraca status 401 Unauthorized."""
    res = client.get('/api/auth/me')

    assert res.status_code == 401


def test_list_tasks_requires_authentication(client):
    """Sprawdza, czy próba pobrania zadań bez tokenu JWT kończy się błędem 401 Unauthorized."""
    res = client.get('/api/tasks')

    assert res.status_code == 401


def test_user_cannot_see_another_users_tasks(client, auth_headers, second_auth_headers):
    """BOLA/IDOR: Sprawdza, czy użytkownik widzi wyłącznie własne zadania i nie ma wglądu w zadania innych osób."""
    client.post('/api/tasks', json={"title": "Prywatne zadanie użytkownika 1"}, headers=auth_headers)

    res_user2 = client.get('/api/tasks', headers=second_auth_headers)
    assert res_user2.status_code == 200
    assert res_user2.get_json()["tasks"] == []


def test_user_cannot_update_another_users_task(client, auth_headers, second_auth_headers):
    """BOLA/IDOR: Sprawdza, czy próba edycji cudzego zadania kończy się błędem 404 i nie zmienia treści zadania."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie użytkownika 1"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    hack_res = client.patch(f'/api/tasks/{task_id}', json={"title": "Przejęte"}, headers=second_auth_headers)
    assert hack_res.status_code == 404

    list_res = client.get('/api/tasks', headers=auth_headers)
    assert list_res.get_json()["tasks"][0]["title"] == "Zadanie użytkownika 1"


def test_user_cannot_delete_another_users_task(client, auth_headers, second_auth_headers):
    """BOLA/IDOR: Sprawdza, czy próba usunięcia cudzego zadania kończy się błędem 404 i zadanie pozostaje w bazie."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie użytkownika 1"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    del_res = client.delete(f'/api/tasks/{task_id}', headers=second_auth_headers)
    assert del_res.status_code == 404

    list_res = client.get('/api/tasks', headers=auth_headers)
    assert len(list_res.get_json()["tasks"]) == 1


def test_admin_database_endpoint_denies_regular_user(client, auth_headers):
    """Sprawdza, czy zwykły zalogowany użytkownik nie ma dostępu do panelu administratora (błąd 403)."""
    res = client.get('/api/admin/database', headers=auth_headers)

    assert res.status_code == 403
    assert "message" in res.get_json()


def test_admin_database_endpoint_hides_sensitive_columns(client, admin_headers):
    """Sprawdza, czy panel administratora nie ujawnia wrażliwych kolumn (np. password_hash)."""
    res = client.get('/api/admin/database', headers=admin_headers)

    assert res.status_code == 200
    data = res.get_json()
    assert "tables" in data

    user_table = next((t for t in data["tables"] if t["name"] == "user"), None)
    assert user_table is not None
    column_names = [col["name"] for col in user_table["columns"]]
    assert "username" in column_names
    assert "password_hash" not in column_names


def test_sensitive_column_detects_password_hash():
    """Sprawdza wykrywanie kolumny password_hash jako wrażliwej."""
    assert is_sensitive_column("password_hash") is True


def test_sensitive_column_detects_access_token():
    """Sprawdza wykrywanie kolumny access_token jako wrażliwej."""
    assert is_sensitive_column("access_token") is True


def test_sensitive_column_detects_secret_marker_case_insensitively():
    """Sprawdza wykrywanie kluczy/sekretów bez względu na wielkość liter."""
    assert is_sensitive_column("API_SECRET_KEY") is True


def test_sensitive_column_detects_token_marker_in_column_name():
    """Sprawdza wykrywanie tokenów odświeżania jako kolumny wrażliwej."""
    assert is_sensitive_column("refresh_token_expiry") is True
