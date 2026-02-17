# Campus Resource Hub — Backend API

A RESTful backend API for campus resource management built with **Django** and **Django REST Framework**. Connects to an existing Azure MySQL database for managing users, resources (labs, classrooms, event halls), and bookings.

## Tech Stack

| Layer        | Technology                          |
| ------------ | ----------------------------------- |
| Language     | Python 3.12+                        |
| Framework    | Django 6.0, Django REST Framework   |
| Database     | Azure MySQL (campus_reshub_db)      |
| Pkg Manager  | uv                                  |
| CORS         | django-cors-headers                 |
| Config       | python-decouple (.env)              |

## Setup Instructions

### 1. Clone & Install

```bash
git clone <repo-url>
cd python09-campus-reshub-api

# Install dependencies with uv
uv sync
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=campus_reshub_db
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host.mysql.database.azure.com
DB_PORT=3306
FRONTEND_URL=http://localhost:5173
```

### 3. Run the Server

```bash
uv run python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

## API Endpoints

### Users (`/api/users/`)

| Method   | Endpoint            | Description                                |
| -------- | ------------------- | ------------------------------------------ |
| `POST`   | `/api/users/`       | Create a new user                          |
| `GET`    | `/api/users/`       | List all users (filter: `?status=ACTIVE`)  |
| `GET`    | `/api/users/{id}/`  | Get user by ID                             |
| `PUT`    | `/api/users/{id}/`  | Update a user                              |
| `DELETE` | `/api/users/{id}/`  | Delete a user                              |

### Resources (`/api/resources/`)

| Method   | Endpoint                | Description            |
| -------- | ----------------------- | ---------------------- |
| `POST`   | `/api/resources/`       | Create a resource      |
| `GET`    | `/api/resources/`       | List all resources     |
| `GET`    | `/api/resources/{id}/`  | Get resource by ID     |
| `PUT`    | `/api/resources/{id}/`  | Update a resource      |
| `DELETE` | `/api/resources/{id}/`  | Delete a resource      |

### Bookings (`/api/bookings/`)

| Method   | Endpoint                | Description                                     |
| -------- | ----------------------- | ----------------------------------------------- |
| `POST`   | `/api/bookings/`        | Create a booking (conflict detection: 409)       |
| `GET`    | `/api/bookings/`        | List all bookings (with nested user & resource)  |
| `GET`    | `/api/bookings/{id}/`   | Get booking by ID (with nested user & resource)  |
| `PUT`    | `/api/bookings/{id}/`   | Update a booking (status change, re-validation)  |
| `DELETE` | `/api/bookings/{id}/`   | Delete a booking                                 |

## Response Format

**Success (single object):**
```json
{
  "success": true,
  "data": { ... }
}
```

**Success (list):**
```json
{
  "success": true,
  "count": 10,
  "data": [ ... ]
}
```

**Error:**
```json
{
  "success": false,
  "message": "description",
  "errors": { ... }
}
```

## Project Structure

```
python09-campus-reshub-api/
├── config/                # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── exception_handlers.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/              # User management app
├── resources/             # Resource management app
├── bookings/              # Booking management app
├── .env                   # Environment variables (not in git)
├── manage.py
├── pyproject.toml
└── README.md
```
