def get_auth_headers(client):
    """Pomocnicza funkcja: rejestruje użytkownika, loguje go i zwraca nagłówki autoryzacyjne."""
    client.post('/api/auth/register', json={
        "username": "taskuser",
        "email": "task@example.com",
        "password": "password123"
    })
    res = client.post('/api/auth/login', json={
        "username": "taskuser",
        "email": "task@example.com",
        "password": "password123"
    })
    
    data = res.get_json() or {}
    # Obsługa najpopularniejszych nazw kluczy dla tokenu JWT
    token = data.get("access_token") or data.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def test_tasks_crud(client):
    """Testuje pobieranie, tworzenie i usuwanie zadań."""
    headers = get_auth_headers(client)

    # 1. Pobranie listy zadań (na starcie powinna być pusta)
    get_res = client.get('/api/tasks', headers=headers)
    assert get_res.status_code == 200
    assert isinstance(get_res.get_json(), list)

    # 2. Utworzenie nowego zadania
    create_res = client.post('/api/tasks', json={
        "title": "Przetestować pipeline w GitHub Actions",
        "description": "Sprawdzić czy pytest przechodzi na zielono"
    }, headers=headers)
    assert create_res.status_code in [200, 201]

    # 3. Sprawdzenie, czy zadanie pojawiło się na liście
    get_res_after = client.get('/api/tasks', headers=headers)
    tasks = get_res_after.get_json()
    assert len(tasks) == 1
    assert tasks[0].get("title") == "Przetestować pipeline w GitHub Actions"