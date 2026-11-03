from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Task

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")

def current_user_id():
    return int(get_jwt_identity())

@tasks_bp.get("")
@jwt_required()
def list_tasks():
    tasks = Task.query.filter_by(user_id=current_user_id()).order_by(Task.created_at.desc()).all()
    return jsonify(tasks=[task.to_dict() for task in tasks])

@tasks_bp.post("")
@jwt_required()
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    if not title or len(title) > 160:
        return jsonify(message="Tytuł jest wymagany i może mieć maksymalnie 160 znaków."), 400
    if len(description) > 1000:
        return jsonify(message="Opis może mieć maksymalnie 1000 znaków."), 400

    task = Task(title=title, description=description, user_id=current_user_id())
    db.session.add(task)
    db.session.commit()
    return jsonify(task=task.to_dict()), 201

def owned_task(task_id):
    return Task.query.filter_by(id=task_id, user_id=current_user_id()).first()

@tasks_bp.patch("/<int:task_id>")
@jwt_required()
def update_task(task_id):
    task = owned_task(task_id)
    if not task:
        return jsonify(message="Nie znaleziono zadania."), 404
    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title or len(title) > 160:
            return jsonify(message="Tytuł jest wymagany i może mieć maksymalnie 160 znaków."), 400
        task.title = title
    if "description" in data:
        description = (data.get("description") or "").strip()
        if len(description) > 1000:
            return jsonify(message="Opis może mieć maksymalnie 1000 znaków."), 400
        task.description = description
    if "completed" in data:
        if not isinstance(data["completed"], bool):
            return jsonify(message="Pole completed musi być wartością true/false."), 400
        task.completed = data["completed"]

    db.session.commit()
    return jsonify(task=task.to_dict())

@tasks_bp.delete("/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    task = owned_task(task_id)
    if not task:
        return jsonify(message="Nie znaleziono zadania."), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify(message="Zadanie usunięte.")
