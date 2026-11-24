import sys
import os
import pytest

# 1. Dodajemy katalog backend do ścieżki w sposób niezależny od systemu operacyjnego
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

# 2. Importujemy Config ZANIM zaimportujemy app.py!
from config import Config

# Nadpisujemy bazę na bazę w pamięci RAM, aby testy nie tworzyły plików na dysku
# i były w pełni niezależne od lokalnego środowiska oraz systemu operacyjnego.
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
Config.TESTING = True
Config.JWT_SECRET_KEY = "bardzo-dlugi-i-bezpieczny-klucz-testowy-jwt-minimum-32-znaki"
Config.SECRET_KEY = "bardzo-dlugi-i-bezpieczny-klucz-testowy-secret-32-znaki"
Config.ADMIN_USERNAME = ""
Config.ADMIN_EMAIL = ""
Config.ADMIN_PASSWORD = ""

# 3. Dopiero teraz bezpiecznie importujemy create_app i modele
from app import create_app
from models import db, User


@pytest.fixture
def app():
    """Tworzy czystą instancję aplikacji z bazą w pamięci RAM przed każdym testem."""
    flask_app = create_app()

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Klient testowy do wysyłania zapytań HTTP."""
    return app.test_client()


@pytest.fixture
def registered_user(client):
    """Rejestruje standardowego użytkownika testowego i zwraca dane odpowiedzi (w tym token)."""
    response = client.post('/api/auth/register', json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })
    return response.get_json()


@pytest.fixture
def auth_headers(registered_user):
    """Zwraca nagłówki autoryzacyjne JWT dla domyślnego użytkownika testowego."""
    token = registered_user["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_auth_headers(client):
    """Rejestruje drugiego użytkownika i zwraca jego nagłówki JWT (do testów izolacji / BOLA)."""
    response = client.post('/api/auth/register', json={
        "username": "otheruser",
        "email": "other@example.com",
        "password": "password123"
    })
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(app, client):
    """Tworzy użytkownika z uprawnieniami administratora i zwraca nagłówki JWT."""
    with app.app_context():
        admin = User(username="adminuser", email="admin@example.com", is_admin=True)
        admin.set_password("adminpass123")
        db.session.add(admin)
        db.session.commit()

    response = client.post('/api/auth/login', json={
        "login": "adminuser",
        "password": "adminpass123"
    })
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
