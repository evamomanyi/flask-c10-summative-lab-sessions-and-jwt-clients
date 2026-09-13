from app import bcrypt, db
from models import User


def signup(client, username="alice", password="password123"):
    return client.post("/signup", json={
        "username": username,
        "password": password,
        "password_confirmation": password,
    })


def login(client, username="alice", password="password123"):
    return client.post("/login", json={"username": username, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["message"]


def test_signup_hashes_password(client, app):
    response = signup(client)
    assert response.status_code == 201
    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        assert user is not None
        assert user.password_hash != "password123"
        assert bcrypt.check_password_hash(user.password_hash, "password123")


def test_login_and_me(client):
    signup(client)
    response = login(client)
    assert response.status_code == 200
    token = response.json["token"]
    me = client.get("/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json["username"] == "alice"


def test_protected_routes_require_auth(client):
    assert client.get("/me").status_code == 401
    assert client.get("/notes").status_code == 401
    assert client.post("/notes", json={"title": "x", "content": "y"}).status_code == 401


def test_note_crud_and_pagination(client):
    signup(client)
    token = login(client).json["token"]
    headers = auth_headers(token)

    created = client.post("/notes", json={"title": "First", "content": "Hello", "category": "work"}, headers=headers)
    assert created.status_code == 201
    note_id = created.json["id"]

    listing = client.get("/notes?page=1&per_page=1", headers=headers)
    assert listing.status_code == 200
    assert listing.json["pagination"]["page"] == 1
    assert listing.json["pagination"]["per_page"] == 1
    assert len(listing.json["notes"]) == 1

    updated = client.patch(f"/notes/{note_id}", json={"title": "Updated"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json["title"] == "Updated"

    fetched = client.get(f"/notes/{note_id}", headers=headers)
    assert fetched.status_code == 200

    deleted = client.delete(f"/notes/{note_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get(f"/notes/{note_id}", headers=headers).status_code == 404


def test_users_cannot_access_each_others_notes(client):
    signup(client, "alice")
    alice_token = login(client, "alice").json["token"]
    note = client.post("/notes", json={"title": "Private", "content": "Alice only"}, headers=auth_headers(alice_token))
    note_id = note.json["id"]

    signup(client, "bob")
    bob_token = login(client, "bob").json["token"]
    bob_headers = auth_headers(bob_token)

    assert client.get(f"/notes/{note_id}", headers=bob_headers).status_code == 404
    assert client.patch(f"/notes/{note_id}", json={"title": "Hacked"}, headers=bob_headers).status_code == 404
    assert client.delete(f"/notes/{note_id}", headers=bob_headers).status_code == 404
    assert client.get("/notes", headers=bob_headers).json["notes"] == []
