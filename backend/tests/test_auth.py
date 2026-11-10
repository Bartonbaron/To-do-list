def test_health_endpoint(client):
    """Sprawdza czy endpoint /api/health działa poprawnie."""
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}

def test_register_and_login(client):
    """Testuje pełny proces rejestracji nowego użytkownika i logowania."""
    # 1. Rejestracja nowego użytkownika
    reg_response = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert reg_response.status_code == 201
    assert "token" in reg_response.get_json()

    # 2. Próba ponownej rejestracji tego samego użytkownika (błąd 409)
    dup_response = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert dup_response.status_code == 409

    # 3. Logowanie poprawnymi danymi (używamy klucza "login" zgodnie z routes/auth.py)
    login_response = client.post('/api/auth/login', json={
        "login": "testuser",
        "password": "password123"
    })
    assert login_response.status_code == 200
    token = login_response.get_json().get("token")
    assert token is not None

    # 4. Pobranie danych zalogowanego użytkownika (/api/auth/me)
    me_response = client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.get_json()["user"]["username"] == "testuser"

    # 5. Logowanie błędnym hasłem
    bad_login = client.post('/api/auth/login', json={
        "login": "testuser",
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401