from models import User, db


# --- FUNKCJE POMOCNICZE (HELPERS) DO BUDOWANIA SCENARIUSZY ---

def _register(client, username, email, password="password123"):
    return client.post('/api/auth/register', json={
        "username": username,
        "email": email,
        "password": password
    })


def _login(client, login_value, password="password123"):
    return client.post('/api/auth/login', json={
        "login": login_value,
        "password": password
    })


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def _create_task(client, headers, title, description=""):
    return client.post('/api/tasks', json={
        "title": title,
        "description": description
    }, headers=headers)


# --- TESTY INTEGRACYJNE (Wymagane: min. 5) ---

def test_integration_full_user_task_lifecycle(client):
    """
    Scenariusz 1: Pełny cykl życia zadania użytkownika:
    Rejestracja -> weryfikacja profilu (/me) -> dodanie zadania -> pobranie listy ->
    oznaczenie jako wykonane -> sprawdzenie aktualizacji na liście.
    """
    # 1. Rejestracja
    reg_res = _register(client, "janek_dev", "janek@example.com")
    assert reg_res.status_code == 201
    headers = _auth_header(reg_res.get_json()["token"])

    # 2. Sprawdzenie profilu zalogowanego użytkownika
    me_res = client.get('/api/auth/me', headers=headers)
    assert me_res.status_code == 200
    assert me_res.get_json()["user"]["username"] == "janek_dev"

    # 3. Dodanie zadania
    create_res = _create_task(client, headers, "Wdrożyć testy integracyjne", "Etap 3 DevSecOps")
    assert create_res.status_code == 201
    task_id = create_res.get_json()["task"]["id"]

    # 4. Pobranie listy zadań i weryfikacja
    list_res = client.get('/api/tasks', headers=headers)
    assert list_res.status_code == 200
    tasks = list_res.get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["completed"] is False

    # 5. Oznaczenie zadania jako wykonane
    patch_res = client.patch(f'/api/tasks/{task_id}', json={"completed": True}, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.get_json()["task"]["completed"] is True

    # 6. Ponowne sprawdzenie listy zadań po zmianie
    final_list = client.get('/api/tasks', headers=headers).get_json()["tasks"]
    assert final_list[0]["completed"] is True


def test_integration_login_manage_multiple_tasks_and_delete(client):
    """
    Scenariusz 2: Rejestracja -> ponowne logowanie e-mailem -> utworzenie 2 zadań ->
    usunięcie pierwszego zadania -> weryfikacja, że na liście pozostało tylko drugie zadanie.
    """
    # 1. Rejestracja i ponowne logowanie za pomocą e-maila
    assert _register(client, "kasia_qa", "kasia@example.com").status_code == 201
    login_res = _login(client, "KASIA@example.com")
    assert login_res.status_code == 200
    headers = _auth_header(login_res.get_json()["token"])

    # 2. Dodanie dwóch zadań
    t1 = _create_task(client, headers, "Zadanie pierwsze").get_json()["task"]
    t2 = _create_task(client, headers, "Zadanie drugie").get_json()["task"]

    tasks_before = client.get('/api/tasks', headers=headers).get_json()["tasks"]
    assert len(tasks_before) == 2

    # 3. Usunięcie pierwszego zadania
    del_res = client.delete(f"/api/tasks/{t1['id']}", headers=headers)
    assert del_res.status_code == 200

    # 4. Weryfikacja stanu końcowego listy
    tasks_after = client.get('/api/tasks', headers=headers).get_json()["tasks"]
    assert len(tasks_after) == 1
    assert tasks_after[0]["id"] == t2["id"]
    assert tasks_after[0]["title"] == "Zadanie drugie"


def test_integration_validation_errors_do_not_corrupt_state(client):
    """
    Scenariusz 3: Odporność przepływu na błędy użytkownika:
    Rejestracja -> nieudana próba utworzenia zadania (pusty tytuł) -> poprawne utworzenie ->
    nieudana próba edycji (błędny typ completed) -> weryfikacja, że pierwotne dane przetrwały.
    """
    reg_res = _register(client, "marek_ops", "marek@example.com")
    headers = _auth_header(reg_res.get_json()["token"])

    # 1. Błędne dodanie zadania (pusty tytuł -> 400)
    bad_create = _create_task(client, headers, "   ")
    assert bad_create.status_code == 400
    assert client.get('/api/tasks', headers=headers).get_json()["tasks"] == []

    # 2. Poprawne dodanie zadania (201)
    good_create = _create_task(client, headers, "Stabilne zadanie", "Opis początkowy")
    assert good_create.status_code == 201
    task_id = good_create.get_json()["task"]["id"]

    # 3. Błędna aktualizacja zadania (string zamiast bool -> 400)
    bad_patch = client.patch(f'/api/tasks/{task_id}', json={"completed": "tak"}, headers=headers)
    assert bad_patch.status_code == 400

    # 4. Weryfikacja, że zadanie zachowało poprawny stan w bazie
    tasks = client.get('/api/tasks', headers=headers).get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Stabilne zadanie"
    assert tasks[0]["completed"] is False


def test_integration_multi_user_isolation_workflow(client):
    """
    Scenariusz 4: Współpraca i izolacja danych dwóch użytkowników w jednym przepływie:
    User A tworzy zadanie i je aktualizuje -> User B loguje się, dodaje swoje zadanie,
    próbuje odczytać/zmienić/usunąć zadanie Usera A (404) -> każdy widzi wyłącznie swoje dane.
    """
    # 1. User A tworzy i edytuje swoje zadanie
    headers_a = _auth_header(_register(client, "user_alpha", "alpha@example.com").get_json()["token"])
    task_a_id = _create_task(client, headers_a, "Tajny projekt Alpha").get_json()["task"]["id"]
    client.patch(f'/api/tasks/{task_a_id}', json={"description": "Zaktualizowany opis"}, headers=headers_a)

    # 2. User B rejestruje się i tworzy własne zadanie
    headers_b = _auth_header(_register(client, "user_beta", "beta@example.com").get_json()["token"])
    _create_task(client, headers_b, "Zadanie Beta")

    # 3. User B próbuje przejąć lub usunąć zadanie Usera A
    assert client.patch(f'/api/tasks/{task_a_id}', json={"title": "Hacked"}, headers=headers_b).status_code == 404
    assert client.delete(f'/api/tasks/{task_a_id}', headers=headers_b).status_code == 404

    # 4. Weryfikacja izolacji list obu użytkowników
    tasks_a = client.get('/api/tasks', headers=headers_a).get_json()["tasks"]
    tasks_b = client.get('/api/tasks', headers=headers_b).get_json()["tasks"]

    assert len(tasks_a) == 1
    assert tasks_a[0]["title"] == "Tajny projekt Alpha"
    assert tasks_a[0]["description"] == "Zaktualizowany opis"

    assert len(tasks_b) == 1
    assert tasks_b[0]["title"] == "Zadanie Beta"


def test_integration_role_based_access_admin_vs_regular_user(client, app):
    """
    Scenariusz 5: Pełny przepływ autoryzacji ról (RBAC):
    Zwykły użytkownik rejestruje się i dostaje odmowę dostępu do /api/admin/database (403) ->
    administrator loguje się i pobiera strukturę tabel z ukrytymi kolumnami wrażliwymi (200).
    """
    # 1. Zwykły użytkownik próbuje wejść do zasobów administratora
    user_headers = _auth_header(_register(client, "zwykly_user", "zwykly@example.com").get_json()["token"])
    forbidden_res = client.get('/api/admin/database', headers=user_headers)
    assert forbidden_res.status_code == 403

    # 2. Utworzenie konta administratora w bazie i logowanie przez API
    with app.app_context():
        admin = User(username="superadmin", email="superadmin@example.com", is_admin=True)
        admin.set_password("AdminSecret123!")
        db.session.add(admin)
        db.session.commit()

    admin_login = _login(client, "superadmin", "AdminSecret123!")
    assert admin_login.status_code == 200
    admin_headers = _auth_header(admin_login.get_json()["token"])

    # 3. Administrator pobiera podgląd bazy i weryfikuje maskowanie haseł
    admin_res = client.get('/api/admin/database', headers=admin_headers)
    assert admin_res.status_code == 200
    tables = admin_res.get_json()["tables"]
    user_table = next(t for t in tables if t["name"] == "user")
    col_names = [c["name"] for c in user_table["columns"]]
    assert "email" in col_names
    assert "password_hash" not in col_names
