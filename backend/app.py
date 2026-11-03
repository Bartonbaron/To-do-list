from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes.auth import auth_bp
from routes.tasks import tasks_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    JWTManager(app)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
