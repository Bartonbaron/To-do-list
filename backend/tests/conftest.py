import sys
import os
import pytest

# 1. Dodajemy katalog backend do ścieżki
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

# 2. Importujemy Config ZANIM zaimportujemy app.py!
from config import Config

# Nadpisujemy ścieżkę "/app/instance/todo.db" na bazę w pamięci RAM,
# żeby linijka "app = create_app()" wykonywana przy imporcie app.py nie wywaliła błędu
Config.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
Config.TESTING = True
Config.JWT_SECRET_KEY = "bardzo-dlugi-i-bezpieczny-klucz-testowy-jwt-minimum-32-znaki"
Config.SECRET_KEY = "bardzo-dlugi-i-bezpieczny-klucz-testowy-secret-32-znaki"

# 3. Dopiero teraz bezpiecznie importujemy create_app i db
from app import create_app
from models import db

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