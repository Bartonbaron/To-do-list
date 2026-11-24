from models import User


# --- REJESTRACJA (/api/auth/register) ---

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


# --- LOGOWANIE (/api/auth/login) ---

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


# --- PROFIL ZALOGOWANEGO UŻYTKOWNIKA (/api/auth/me) ---

def test_me_endpoint_returns_current_user_data(client, auth_headers):
    """Sprawdza, czy endpoint /api/auth/me zwraca poprawne dane zalogowanego użytkownika."""
    res = client.get('/api/auth/me', headers=auth_headers)

    assert res.status_code == 200
    user_data = res.get_json()["user"]
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "test@example.com"
    assert user_data["is_admin"] is False


def test_me_endpoint_fails_without_token(client):
    """Sprawdza, czy wywołanie /api/auth/me bez tokenu JWT zwraca status 401 Unauthorized."""
    res = client.get('/api/auth/me')

    assert res.status_code == 401
