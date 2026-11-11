from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import inspect, text

from models import User, db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

SENSITIVE_COLUMN_NAMES = {"password", "password_hash", "secret", "token", "access_token"}


def is_sensitive_column(column_name):
    normalized_name = column_name.lower()
    return normalized_name in SENSITIVE_COLUMN_NAMES or any(
        marker in normalized_name for marker in ("password", "secret", "token")
    )


def admin_required(view):
    @jwt_required()
    def wrapped(*args, **kwargs):
        user = db.session.get(User, int(get_jwt_identity()))
        if not user or not user.is_admin:
            return jsonify(message="Dostęp tylko dla administratora."), 403
        return view(*args, **kwargs)

    wrapped.__name__ = view.__name__
    return wrapped


@admin_bp.get("/database")
@admin_required
def database_structure():
    inspector = inspect(db.engine)
    tables = []
    for table_name in inspector.get_table_names():
        all_columns = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "primary_key": column["primary_key"],
            }
            for column in inspector.get_columns(table_name)
        ]
        columns = [column for column in all_columns if not is_sensitive_column(column["name"])]
        visible_column_names = [column["name"] for column in columns]
        rows = db.session.execute(
            text(f'SELECT * FROM "{table_name}"')
        ).mappings().all()
        contents = [
            {name: row[name] for name in visible_column_names}
            for row in rows
        ]
        row_count = db.session.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar_one()
        tables.append({
            "name": table_name,
            "columns": columns,
            "row_count": row_count,
            "rows": contents,
        })
    return jsonify(tables=tables)
