# 🏫 Campus ResHub API

> A robust Campus Resource Management System API built with Django and Django REST Framework. Facilitates the management and booking of campus resources (labs, classrooms, event halls) with a highly defensive concurrency architecture and role-based approval workflow.

## 🚀 Tech Stack

- **Framework:** Django 6.0+, Django REST Framework (DRF)
- **Database:** PostgreSQL / MySQL Compliant
- **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Package Manager:** `uv` (Modern Python dependency resolver)
- **API Documentation:** OpenAPI 3.0 via `drf-spectacular`
- **Linting:** Ruff

---

## ✨ Features & Architecture

### 🛡️ Defensive Engineering
- **Advanced Concurrency Control:** `select_for_update()`-backed transactions lock the relevant `Resource` row to serialize booking creation for that resource, helping prevent double-booking and other conflicting updates under concurrent load.
- **Immutable Audit Logging:** Built-in audit signal tracking comprehensively captures complex state mutations (`previous_state` & `new_state`) across all domain components for high-fidelity compliance tracking.
- **Resilient Data Architecture:** `SoftDeleteMixin` abstractions safely manage data retention policies without causing destructive relational DB cascades.

### ⚙️ Domain Capabilities
- **Synchronous Notifications:** Database-first `UserNotification` logic delivers immediate UI messages via isolated signals rather than complex external brokers.
- **Dynamic Access Vectors:** Fine-grained API View class configurations assert hyper-specific permissions based sequentially on account activity and mapped role (`IsActiveAndApproved`, `IsFacultyOrAdmin`).
- **Resource Processing:** Precise CRUD handling mapping exactly to exact working-day schedules overrides (`CalendarOverride`), restricting illegal out-of-bounds capacities.

---

## 🛠️ Getting Started

### Prerequisites
- **Python:** 3.12+
- **Database Server:** MySQL/PostgreSQL
- **Package Installer:** [uv](https://github.com/astral-sh/uv) (Recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository_url>
   cd python09-campus-reshub-api
   ```

2. **Environment Setup**
   Create a `.env` file in the root directory by copying the example:
   ```bash
   cp .env.example .env
   ```
   Update the `.env` file with your database credentials:
   ```ini
   DJANGO_SECRET_KEY=your_secret_key
   DJANGO_DEBUG=True
   DB_NAME=campus_reshub_db
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   ```

3. **Install Dependencies**
   Run the quick-sync using `uv`:
   ```bash
   uv sync
   ```

4. **Initialize Database**
   Ensure your server is initialized and execute the migration manifest:
   ```bash
   uv run python manage.py migrate
   ```

5. **Create Superuser Admin**
   ```bash
   uv run python manage.py createsuperuser
   ```

6. **Deploy Local Server**
   ```bash
   uv run python manage.py runserver
   ```

---

## 📖 API Documentation

Once the server builds successfully, the interactive schema definitions compile natively:

- **Swagger UI:** [http://localhost:8000/api/v1/docs/](http://localhost:8000/api/v1/docs/)
- **ReDoc:** [http://localhost:8000/api/v1/redoc/](http://localhost:8000/api/v1/redoc/)

---

## 📂 Project Structure

```text
python09-campus-reshub-api/
├── apps/                   # Segregated Django feature modules
│   ├── accounts/           # User models, authentication tokens & RBAC requests
│   ├── resources/          # Capacity bindings, schedules, overrides
│   ├── bookings/           # Concurrency-safe transactions, approvals
│   ├── notifications/      # Local synchronous messaging subsystem
│   └── audit/              # Immutable state-preservation logs
├── config/                 # Root configurations (settings, routing)
├── core/                   # Shared validations, SoftDeleteMixin, custom Response objects
├── manage.py               # Django execution engine
└── pyproject.toml          # Dependency manifestations
```

---

## 🤝 Contributing
1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

