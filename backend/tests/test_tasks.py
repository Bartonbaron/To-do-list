def get_auth_headers(client):
    """Rejestruje użytkownika i zwraca nagłówek Authorization z tokenem JWT."""
    res = client.post('/api/auth/register', json={
        "username": "taskuser",
        "email": "task@example.com",
        "password": "password123"
    })
    token = res.get_json().get("token")
    return {"Authorization": f"Bearer {token}"}

def test_tasks_crud(client):
    """Testuje pobieranie i tworzenie zadań."""
    headers = get_auth_headers(client)

    # 1. Pobranie listy zadań (na starcie pusta pod kluczem "tasks")
    get_res = client.get('/api/tasks', headers=headers)
    assert get_res.status_code == 200
    data = get_res.get_json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert len(data["tasks"]) == 0

    # 2. Utworzenie nowego zadania
    create_res = client.post('/api/tasks', json={
        "title": "Przetestować pipeline w GitHub Actions",
        "description": "Sprawdzić czy pytest przechodzi na zielono"
    }, headers=headers)
    assert create_res.status_code in [200, 201], f"Błąd tworzenia zadania: {create_res.get_data(as_text=True)}"

    # 3. Sprawdzenie, czy zadanie pojawiło się na liście
    get_res_after = client.get('/api/tasks', headers=headers)
    tasks = get_res_after.get_json().get("tasks", [])
    assert len(tasks) == 1
    assert tasks[0].get("title") == "Przetestować pipeline w GitHub Actions"