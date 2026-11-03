import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if len(username) < 3 or len(username) > 40:
        return jsonify(message="Nazwa użytkownika musi mieć od 3 do 40 znaków."), 400
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify(message="Użytkownik lub e-mail jest już zajęty."), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    token = create_access_token(identity=str(user.id))
    return jsonify(token=token, user={"id": user.id, "username": user.username, "email": user.email}), 201

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    login_value = (data.get("login") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter(
        (db.func.lower(User.email) == login_value) |
        (db.func.lower(User.username) == login_value)
    ).first()

    if not user or not user.check_password(password):
        return jsonify(message="Nieprawidłowy login lub hasło."), 401

    token = create_access_token(identity=str(user.id))
    return jsonify(token=token, user={"id": user.id, "username": user.username, "email": user.email})

@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify(message="Użytkownik nie istnieje."), 404
    return jsonify(user={"id": user.id, "username": user.username, "email": user.email})
