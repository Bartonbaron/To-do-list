from models import db, Task


# --- POBIERANIE ZADAŃ (GET /api/tasks) ---

def test_list_tasks_returns_empty_list_initially(client, auth_headers):
    """Sprawdza, czy dla nowego użytkownika lista zadań jest początkowo pusta."""
    res = client.get('/api/tasks', headers=auth_headers)

    assert res.status_code == 200
    data = res.get_json()
    assert data == {"tasks": []}


def test_list_tasks_requires_authentication(client):
    """Sprawdza, czy próba pobrania zadań bez tokenu JWT kończy się błędem 401 Unauthorized."""
    res = client.get('/api/tasks')

    assert res.status_code == 401


# --- TWORZENIE ZADAŃ (POST /api/tasks) ---

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


# --- AKTUALIZACJA ZADAŃ (PATCH /api/tasks/<id>) ---

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


# --- USUWANIE ZADAŃ (DELETE /api/tasks/<id>) ---

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


# --- IZOLACJA DANYCH UŻYTKOWNIKÓW (BOLA / IDOR) ---

def test_user_cannot_see_another_users_tasks(client, auth_headers, second_auth_headers):
    """Sprawdza, czy użytkownik widzi wyłącznie własne zadania i nie ma wglądu w zadania innych osób."""
    client.post('/api/tasks', json={"title": "Prywatne zadanie użytkownika 1"}, headers=auth_headers)

    res_user2 = client.get('/api/tasks', headers=second_auth_headers)
    assert res_user2.status_code == 200
    assert res_user2.get_json()["tasks"] == []


def test_user_cannot_update_another_users_task(client, auth_headers, second_auth_headers):
    """Sprawdza, czy próba edycji cudzego zadania kończy się błędem 404 i nie zmienia treści zadania."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie użytkownika 1"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    hack_res = client.patch(f'/api/tasks/{task_id}', json={"title": "Przejęte"}, headers=second_auth_headers)
    assert hack_res.status_code == 404

    list_res = client.get('/api/tasks', headers=auth_headers)
    assert list_res.get_json()["tasks"][0]["title"] == "Zadanie użytkownika 1"


def test_user_cannot_delete_another_users_task(client, auth_headers, second_auth_headers):
    """Sprawdza, czy próba usunięcia cudzego zadania kończy się błędem 404 i zadanie pozostaje w bazie."""
    create_res = client.post('/api/tasks', json={"title": "Zadanie użytkownika 1"}, headers=auth_headers)
    task_id = create_res.get_json()["task"]["id"]

    del_res = client.delete(f'/api/tasks/{task_id}', headers=second_auth_headers)
    assert del_res.status_code == 404

    list_res = client.get('/api/tasks', headers=auth_headers)
    assert len(list_res.get_json()["tasks"]) == 1
