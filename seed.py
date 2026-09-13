from faker import Faker

from app import app, bcrypt, db
from models import Note, User

fake = Faker()


def seed_database():
    with app.app_context():
        db.create_all()

        if User.query.count() > 0:
            return

        users = []
        for username, password in [("alice", "password123"), ("bob", "password123"), ("charlie", "password123")]:
            user = User(
                username=username,
                password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            )
            db.session.add(user)
            users.append(user)

        db.session.flush()

        notes = [
            Note(title="Welcome", content="This is Alice's first note.", category="personal", user_id=users[0].id),
            Note(title="Study Plan", content="Review Flask authentication and SQLAlchemy.", category="study", user_id=users[0].id),
            Note(title="Project Ideas", content="Build a useful productivity application.", category="work", user_id=users[1].id),
            Note(title="Weekend", content="Plan activities for the weekend.", category="personal", user_id=users[2].id),
        ]
        db.session.add_all(notes)
        db.session.commit()


if __name__ == "__main__":
    seed_database()
    print("Seed complete.")
