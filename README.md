# MunTech - School Management System

A production-ready, multi-tenant school management platform built with Django 5.0.1.

---

## 🚀 Quick Start (2 minutes)

### 1. Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup Environment
Create `.env` file in project root:
```
SECRET_KEY=your-django-secret-key
DEBUG=True
GOOGLE_CLIENT_ID=your-google-oauth-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
```

### 4. Initialize Database
```powershell
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start Development Server
```powershell
python manage.py runserver
```

**Access**: http://localhost:8000

---

## 📊 Features

### Core Modules
- **Users**: Multi-role authentication (Admin, Principal, Teacher, Parent, Student)
- **Dashboard**: Central management interface
- **Admissions**: Student enrollment and applications
- **Attendance**: Daily class attendance tracking
# MunTech — School Management System (cleaned)

This repository is a Django-based school management platform. This `README` focuses on secure local setup, cleanup steps for repository hygiene, and production deployment notes.

**Target stack**: Django (6.x recommended for this repo), PostgreSQL (production), Gunicorn + WhiteNoise, `django-allauth` for auth.

**Important:** remove any secrets from the repository. Do not commit `.env` or `.venv`.

**Quick local setup**

- **1. Create & activate a venv** (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

- **2. Install dependencies**:

```powershell
pip install -r requirements.txt
```

- **3. Create an environment file (local only)**

Create a file named `.env` locally (do NOT commit). Use `.env.example` as a template.

Required env vars (example):

- `SECRET_KEY` — generate a strong random key
- `DEBUG` — `True` for local dev only
- `DATABASE_URL` — e.g. `sqlite:///db.sqlite3` or a Postgres URL
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` — OAuth credentials

- **4. Initialize the database:**

```powershell
python manage.py migrate
python manage.py createsuperuser
```

- **5. Collect static files (for production testing):**

```powershell
python manage.py collectstatic --noinput
```

- **6. Run the dev server:**

```powershell
python manage.py runserver
```

Access: http://localhost:8000

Repository hygiene & security (must-do before sharing/pushing)

- **Remove sensitive files from Git history:**
   - Ensure `.env`, `.venv/`, `staticfiles/`, `server.log`, and `server_error.log` are removed from the repo and added to `.gitignore`.
   - To remove from history, use `git rm --cached <file>` and then rewrite history with `git filter-repo` or `bfg` if needed (requires care and coordination).

- **Rotate secrets:**
   - Revoke and re-issue `SECRET_KEY` and any OAuth keys that were exposed.

- **Keep vendor/static builds out of repo:**
   - Do not commit `staticfiles/`. Store app assets in `static/` and produce collected assets via `collectstatic`.

Deployment (Railway / Heroku-like)

- **Procfile** (already included):

```
release: python manage.py migrate
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

- **Environment variables to set in production**:

- `DEBUG=False`
- `SECRET_KEY` (strong, unique)
- `DATABASE_URL` (Postgres provided by the platform)
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

- **Static files**: use WhiteNoise for simple deployments, or serve from a CDN/S3. Ensure `collectstatic` runs during the build.

CI & quality

- Add a CI workflow to run migrations, tests, linters, and formatting on push.
- Recommended tools: `pre-commit`, `black`, `isort`, `flake8`.

Notes & next steps (recommended)

- Confirm the Django target version (repo logs showed Django 6.x locally); update `requirements.txt` and `runtime.txt` to match.
- Remove large vendor files (Grappelli, TinyMCE packages) from the repo and rely on package installs or CDNs.
- Harden `config/settings.py` to read from env, configure `dj_database_url`, enforce `ALLOWED_HOSTS`, secure cookies, and enable WhiteNoise.

I implemented the following changes for you:

- Added `.env.example` (copy to `.env` locally and fill secrets).
- Implemented `NgrokMiddleware` in `core/ngrok_middleware.py` for forwarded headers.
- Updated `requirements.txt` to Django 6.0.1 and added development tools.
- Added GitHub Actions CI (`.github/workflows/ci.yml`).
- Added pre-commit configuration and `pyproject.toml` for formatting.
- Added `scripts/remove_sensitive.ps1` and repository cleanup guidance in `DEPLOYMENT.md`.

Next recommended steps: remove the tracked `.env` and run the cleanup script, then rotate secrets and reconfigure GitHub/Railway environment variables.

---

## 📞 Support

- **Admin Panel**: http://localhost:8000/admin/
- **Login**: http://localhost:8000/accounts/login/

---

## ✅ Production Ready

- ✅ 8 modules implemented
- ✅ CSRF security fixed
- ✅ Multi-tenant architecture
- ✅ Google OAuth configured
- ✅ Railway deployment ready

**Deploy to Railway now!** 🚀

---

**Version**: 2.0 | **Last Updated**: January 2026
