from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import inspect, text
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.tasks import tasks_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    with app.app_context():
        db.create_all()
        ensure_user_admin_column()
        ensure_admin_user(app.config)

    return app


def ensure_user_admin_column():
    if "is_admin" not in {column["name"] for column in inspect(db.engine).get_columns("user")}:
        db.session.execute(text("ALTER TABLE user ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
        db.session.commit()


def ensure_admin_user(config):
    username = config["ADMIN_USERNAME"].strip()
    email = config["ADMIN_EMAIL"].strip().lower()
    password = config["ADMIN_PASSWORD"]
    if not username and not email and not password:
        return
    if not username or not email or len(password) < 8:
        raise RuntimeError("ADMIN_USERNAME, ADMIN_EMAIL and an ADMIN_PASSWORD of at least 8 characters are required together.")

    admin = User.query.filter((User.username == username) | (User.email == email)).first()
    if not admin:
        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
    else:
        admin.is_admin = True
    db.session.commit()

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
