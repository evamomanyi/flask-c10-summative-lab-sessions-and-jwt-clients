# Productivity Tool — Full Auth Flask Backend

## Project Description

A secure Flask REST API for a personal productivity application. The backend provides JWT authentication, securely hashed passwords, a user-owned Notes resource, complete CRUD operations, pagination, and authorization that prevents users from accessing one another's notes.

The repository includes the provided React JWT client in `client-with-jwt/`. The client expects the Flask API on port `5555` through its configured proxy.

## Features

- User registration and login
- JWT-based authentication
- `/me` endpoint for checking the authenticated user
- Bcrypt password hashing
- Unique usernames
- User-owned Notes resource
- Create, read, update, and delete notes
- Pagination on `GET /notes`
- Authorization enforced using the JWT identity
- Seed data for all models
- Flask-Migrate support
- Automated API tests

## Project Structure

```text
.
├── app.py
├── models.py
├── seed.py
├── Pipfile
├── README.md
├── migrations/
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── client-with-jwt/
└── client-with-sessions/
```

## Installation

Python 3.8.13 or newer is required.

```bash
pipenv install
pipenv install --dev
pipenv shell
```

## Environment Variables

For development, the application has a default JWT secret. For a real deployment, set a strong secret:

```bash
export JWT_SECRET_KEY="replace-with-a-long-random-secret"
```

Optional database configuration:

```bash
export DATABASE_URL="sqlite:///productivity.db"
```

## Database Setup

If migrations are already present:

```bash
pipenv run flask db upgrade
```

Seed the database:

```bash
pipenv run python seed.py
```

or:

```bash
pipenv run flask seed
```

The seed creates three users and starter notes.

Seed credentials:

| Username | Password |
|---|---|
| alice | password123 |
| bob | password123 |
| charlie | password123 |

## Running the API

The API runs on port `5555`, matching the React JWT client's proxy.

```bash
pipenv run python app.py
```

Or:

```bash
pipenv run flask --app app run --port 5555
```

API base URL: `http://localhost:5555`

## Running the JWT Frontend

Open another terminal:

```bash
cd client-with-jwt
npm install
npm start
```

The frontend runs on port `4000` and proxies API requests to `http://localhost:5555`.

## API Endpoints

### Public Authentication

| Method | Endpoint | Description | Status |
|---|---|---|---|
| GET | `/` | API welcome/health message | 200 |
| POST | `/signup` | Register a user and return a JWT | 201 |
| POST | `/login` | Authenticate a user and return a JWT | 200 |

### Protected Authentication

| Method | Endpoint | Description | Status |
|---|---|---|---|
| GET | `/me` | Return the currently authenticated user | 200 |

Protected requests require:

```text
Authorization: Bearer <JWT>
```

### Notes Resource

| Method | Endpoint | Description | Status |
|---|---|---|---|
| GET | `/notes` | Return the authenticated user's paginated notes | 200 |
| GET | `/notes/<id>` | Return one owned note | 200 / 404 |
| POST | `/notes` | Create a note owned by the authenticated user | 201 |
| PATCH | `/notes/<id>` | Update an owned note | 200 / 404 |
| DELETE | `/notes/<id>` | Delete an owned note | 200 / 404 |

Pagination example:

```text
GET /notes?page=1&per_page=10
```

The response includes the notes plus page metadata (`page`, `per_page`, `pages`, `total`, `has_next`, and `has_prev`).

## Example Requests

### Sign Up

```json
POST /signup
{
  "username": "alice",
  "password": "password123",
  "password_confirmation": "password123"
}
```

### Login

```json
POST /login
{
  "username": "alice",
  "password": "password123"
}
```

### Create Note

```json
POST /notes
Authorization: Bearer <JWT>
{
  "title": "Study Flask",
  "content": "Review authentication and authorization.",
  "category": "study"
}
```

## Testing

Run the automated tests with:

```bash
pipenv run pytest -q
```

The test suite covers authentication, password hashing, protected routes, CRUD operations, pagination, and cross-user authorization.

## Database Migrations

Create a migration after model changes:

```bash
pipenv run flask db migrate -m "describe the change"
```

Apply migrations:

```bash
pipenv run flask db upgrade
```


## Security and Authorization

Passwords are never stored in plaintext. They are hashed with Flask-Bcrypt before being persisted. JWT-protected endpoints obtain the user identity from the token rather than accepting a client-supplied `user_id`. Every Notes query is scoped to the authenticated user, preventing one user from viewing, editing, or deleting another user's records.
