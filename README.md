# Campus ResHub API

A comprehensive Campus Resource Management System API built with Django and Django REST Framework. This system facilitates the management and booking of campus resources such as labs, classrooms, and event halls, complete with a role-based approval workflow.

## 🚀 Tech Stack

- **Backend Framework:** Django 6.0+, Django REST Framework (DRF)
- **Database:** MySQL
- **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Package Management:** `uv` (Modern Python package installer and resolver)
- **Documentation:** OpenAPI 3.0 (Swagger & Redoc) via `drf-spectacular`
- **Linting & Formatting:** Ruff

## ✨ Key Features

- **User Management**:
  - Role-based access control (Student, Faculty, Staff, Admin).
  - Secure registration and profile management.
- **Resource Management**:
  - CRUD operations for resources (Labs, Classrooms, Event Halls).
  - Availability tracking and capacity management.
  - Soft delete support for data integrity.
- **Booking System**:
  - Advanced scheduling with conflict detection.
  - Approval workflows (Auto-approve, Staff-approve, Admin-approve).
  - Recurring bookings and calendar overrides (Holidays/Working days).
- **Notifications**:
  - Real-time alerts for booking statuses and system updates.
- **Audit Logging**:
  - Comprehensive tracking of all critical actions for security and accountability.

## 🛠️ Getting Started

### Prerequisites

- Python 3.12+
- MySQL Server
- [uv](https://github.com/astral-sh/uv) (Recommended for package management)

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository_url>
    cd python09-campus-reshub-api
    ```

2.  **Environment Setup**
    Create a `.env` file in the root directory by copying the example:
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with your database credentials and secret keys:
    ```ini
    DJANGO_SECRET_KEY=your_secret_key
    DJANGO_DEBUG=True
    DB_NAME=campus_reshub_db
    DB_USER=root
    DB_PASSWORD=your_password
    DB_HOST=localhost
    DB_PORT=3306
    ```

3.  **Install Dependencies**
    Using `uv`:
    ```bash
    uv sync
    ```
    Or via standard pip (if you export requirements):
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Setup**
    Ensure your MySQL server is running and the database exists.
    ```bash
    uv run python manage.py migrate
    ```

5.  **Create Superuser**
    ```bash
    uv run python manage.py createsuperuser
    ```

6.  **Run the Server**
    ```bash
    uv run python manage.py runserver
    ```

## 📖 API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI:** [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
- **ReDoc:** [http://localhost:8000/api/v1/redoc/](http://localhost:8000/api/v1/redoc/)

## 📂 Project Structure

```
python09-campus-reshub-api/
├── apps/                   # Django Apps (Modular structure)
│   ├── accounts/           # User authentication & roles
│   ├── resources/          # Resource management logic
│   ├── bookings/           # Booking & scheduling logic
│   ├── notifications/      # Notification system
│   └── audit/              # Audit logging
├── config/                 # Project configuration (settings, urls)
├── core/                   # Shared utilities, mixins, and middleware
├── manage.py               # Django management script
└── pyproject.toml          # Project dependencies & metadata
```

## 🤝 Contributing

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request
