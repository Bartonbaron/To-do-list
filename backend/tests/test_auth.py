def test_register_and_login(client):
    """Testuje pełny proces rejestracji nowego użytkownika i logowania."""
    # 1. Rejestracja nowego użytkownika
    reg_response = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    
    # Jeśli Twój endpoint rejestracji nie ma prefiksu /api/auth, dostosuj ścieżkę powyżej
    assert reg_response.status_code in [200, 201], f"Błąd rejestracji: {reg_response.get_data(as_text=True)}"

    # 2. Próba ponownej rejestracji tego samego użytkownika (powinna zwrócić błąd 400 lub 409)
    dup_response = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert dup_response.status_code in [400, 409]

    # 3. Logowanie poprawnymi danymi
    login_response = client.post('/api/auth/login', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    assert login_response.status_code == 200

    # 4. Logowanie błędnym hasłem
    bad_login = client.post('/api/auth/login', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401