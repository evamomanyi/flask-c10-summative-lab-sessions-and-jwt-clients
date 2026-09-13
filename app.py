import os
from datetime import timedelta

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///productivity.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-only-change-this-secret"),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=2),
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from models import User, Note

    @app.get("/")
    def home():
        return jsonify({"message": "Productivity API is running"}), 200

    @app.post("/signup")
    def signup():
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip()
        password = data.get("password", "")
        confirmation = data.get("password_confirmation", "")

        errors = []
        if not username:
            errors.append("Username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters")
        if not isinstance(password, str) or len(password) < 6:
            errors.append("Password must be at least 6 characters")
        if password != confirmation:
            errors.append("Password confirmation does not match")
        if username and User.query.filter_by(username=username).first():
            errors.append("Username is already taken")

        if errors:
            return jsonify({"errors": errors}), 422

        user = User(username=username)
        user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "user": user.to_dict()}), 201

    @app.post("/login")
    def login():
        data = request.get_json(silent=True) or {}
        username = str(data.get("username", "")).strip()
        password = data.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({"errors": ["Invalid username or password"]}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({"token": token, "user": user.to_dict()}), 200

    @app.get("/me")
    @jwt_required()
    def me():
        user = User.query.get(int(get_jwt_identity()))
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user.to_dict()), 200

    @app.get("/notes")
    @jwt_required()
    def get_notes():
        user_id = int(get_jwt_identity())
        try:
            page = max(1, int(request.args.get("page", 1)))
            per_page = min(max(1, int(request.args.get("per_page", 10))), 100)
        except (TypeError, ValueError):
            return jsonify({"error": "page and per_page must be integers"}), 400

        pagination = (
            Note.query.filter_by(user_id=user_id)
            .order_by(Note.created_at.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return jsonify({
            "notes": [note.to_dict() for note in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }), 200

    @app.post("/notes")
    @jwt_required()
    def create_note():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        content = str(data.get("content", "")).strip()
        category = str(data.get("category", "general")).strip() or "general"

        errors = []
        if not title:
            errors.append("Title is required")
        if not content:
            errors.append("Content is required")
        if errors:
            return jsonify({"errors": errors}), 422

        note = Note(title=title, content=content, category=category, user_id=int(get_jwt_identity()))
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    def get_owned_note(note_id):
        return Note.query.filter_by(id=note_id, user_id=int(get_jwt_identity())).first()

    @app.get("/notes/<int:note_id>")
    @jwt_required()
    def get_note(note_id):
        note = get_owned_note(note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        return jsonify(note.to_dict()), 200

    @app.patch("/notes/<int:note_id>")
    @jwt_required()
    def update_note(note_id):
        note = get_owned_note(note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        data = request.get_json(silent=True) or {}

        if "title" in data:
            title = str(data["title"]).strip()
            if not title:
                return jsonify({"errors": ["Title cannot be empty"]}), 422
            note.title = title
        if "content" in data:
            content = str(data["content"]).strip()
            if not content:
                return jsonify({"errors": ["Content cannot be empty"]}), 422
            note.content = content
        if "category" in data:
            note.category = str(data["category"]).strip() or "general"

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.delete("/notes/<int:note_id>")
    @jwt_required()
    def delete_note(note_id):
        note = get_owned_note(note_id)
        if not note:
            return jsonify({"error": "Note not found"}), 404
        db.session.delete(note)
        db.session.commit()
        return jsonify({"message": "Note deleted successfully"}), 200

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authentication required"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid authentication token"}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Authentication token has expired"}), 401

    @app.cli.command("seed")
    def seed_command():
        from seed import seed_database
        seed_database()
        print("Database seeded successfully.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5555)), debug=True)
