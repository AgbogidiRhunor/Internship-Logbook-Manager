# SIWES Logbook Manager

**Students Industrial Work Experience Scheme — Institutional Internship Logbook Platform**

A production-grade Django web application for Nigerian universities to manage student SIWES internship logbooks, lecturer supervision, and grading.

---

## Features

### Student
- Self-registration with full internship details
- Daily log entries with photo uploads
- Automatic month/week/day computation
- Filter logs by month, week, day of week
- Real-time progress bar and grading status
- Cannot log outside internship date range
- Cannot create duplicate entries for the same day

### Lecturer
- Registration with admin-approval gate (cannot access until approved)
- View all students within same university / faculty / department
- Search and filter by graded / not-graded status
- View complete student profile and full logbook
- Holistic grading (entire internship, not per-day)
- Export graded summaries as CSV and PDF

### Admin
- Approve or reject lecturer registrations
- Suspend and reactivate any user
- Manage universities, faculties, departments (full CRUD)
- View all students, lecturers, logs, grades
- Audit log of all administrative actions
- System analytics dashboard

---

## Architecture

```
siwes/
├── .env.example
├── requirements.txt
├── DEPLOYMENT.md
├── README.md
└── siwes_logbook/
    ├── manage.py
    ├── core/                  # Settings, URLs, WSGI, context processors
    │   └── management/
    │       └── commands/
    │           └── seed_data.py
    ├── accounts/              # CustomUser, StudentProfile, LecturerProfile
    ├── institutions/          # University, Faculty, Department (admin-managed)
    ├── logbook/               # DailyLogEntry with computed fields
    ├── grading/               # GradeRecord, CSV/PDF exports
    ├── dashboard/             # Role-routing dashboard views
    ├── static/
    │   ├── css/main.css
    │   └── js/
    │       ├── main.js
    │       └── cascade_selects.js
    └── templates/
        ├── base.html
        └── partials/
```

---

## Quick Start

### 1. Clone and configure
```bash
git clone <repo> siwes
cd siwes
cp .env.example .env
# Edit .env with your database credentials and secret key
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up PostgreSQL
```sql
CREATE DATABASE siwes_db;
CREATE USER siwes_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE siwes_db TO siwes_user;
```

### 4. Migrate and seed
```bash
cd siwes_logbook
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data       # Loads 5 Nigerian universities with faculties and departments
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 5. Run development server
```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

---

## User Roles and Access

| Role | Registration | Access |
|------|-------------|--------|
| Student | Self-register at `/accounts/register/student/` | Immediate |
| Lecturer | Self-register at `/accounts/register/lecturer/` | After admin approval |
| Admin | Created via `createsuperuser` or Django admin | Immediate |

---

## Environment Variables

See `.env.example` for all required variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key (generate a long random string) |
| `DEBUG` | `True` for development, `False` for production |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `DB_HOST` | PostgreSQL host (default: `localhost`) |
| `DB_PORT` | PostgreSQL port (default: `5432`) |
| `EMAIL_HOST` | SMTP server hostname |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |

---

## Seed Data

The `seed_data` command loads the following Nigerian universities:

- University of Lagos (UNILAG)
- University of Nigeria, Nsukka (UNN)
- Obafemi Awolowo University (OAU)
- Ahmadu Bello University (ABU)
- University of Ibadan (UI)

Each with realistic faculties and departments. **All seeded data is fully editable through the Django admin.**

To re-seed (development only):
```bash
python manage.py seed_data --clear
```

---

## Running Tests

```bash
python manage.py test --verbosity=2
```

Tests cover:
- Student signup validation (duplicates, password mismatch, date range)
- Lecturer approval workflow
- Duplicate log prevention
- Log date boundary validation
- Lecturer scope restriction (cross-department access blocked)
- Grading workflow (score → letter grade, out-of-range rejection)
- Export permissions (students blocked, unapproved lecturers blocked)
- Rate limit endpoint structure

---

## Security Features

- Custom user model with role-based access from day one
- CSRF protection on all forms
- Rate limiting on login and registration endpoints (`django-ratelimit`)
- Secure cookies and HSTS in production
- Input validation on all forms with length limits
- File upload validation (type + size)
- Lecturer scope enforcement (cannot view students outside their dept)
- Students cannot view each other's logs
- Audit log of all admin actions
- No secrets in code — all via environment variables
- XSS protection via Django's template auto-escaping
- Password strength validation

---

## Production Deployment

See `DEPLOYMENT.md` for the full guide covering:
- PostgreSQL setup
- Gunicorn systemd service
- Nginx reverse proxy configuration
- SSL/TLS with Let's Encrypt
- File permissions
- Pre-launch checklist

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Django 4.2 |
| Database | PostgreSQL 14+ |
| Frontend | HTML5, CSS3, Vanilla JS, Django Templates |
| PDF Export | ReportLab |
| Static Files | WhiteNoise |
| Rate Limiting | django-ratelimit |
| WSGI Server | Gunicorn |
| Reverse Proxy | Nginx |

---

## License

Built for Nigerian university SIWES management. Institutional use.
