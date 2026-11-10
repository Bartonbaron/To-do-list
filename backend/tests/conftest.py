import sys
import os
import pytest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_dir)

os.makedirs(os.path.join(backend_dir, 'instance'), exist_ok=True)

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

from app import create_app
from models import db

@pytest.fixture
def app():
    """Tworzy i konfiguruje czystą instancję aplikacji przed każdym testem."""
    flask_app = create_app()

    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "SECRET_KEY": "test-secret"
    })

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Klient testowy do wysyłania zapytań HTTP."""
    return app.test_client()