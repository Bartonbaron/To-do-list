import sys
import os
import pytest

# Dodajemy katalog backend do ścieżki, aby Python widział pliki app.py i models.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importujemy funkcję tworzącą aplikację (zamiast zmiennej app)
from app import create_app
from models import db

@pytest.fixture
def app():
    """Tworzy nową instancję aplikacji Flask przed każdym testem."""
    # 1. Wywołujemy funkcję, która zwraca gotowy obiekt aplikacji
    flask_app = create_app()

    # 2. Nadpisujemy ustawienia na czas testów (baza w pamięci RAM)
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "SECRET_KEY": "test-secret"
    })

    # 3. Tworzymy tabele w testowej bazie danych przed testem i czyścimy po nim
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Klient testowy do wysyłania zapytań HTTP."""
    return app.test_client()