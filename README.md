# Vehicle Job Tracker

A vehicle service/inspection tracking app built with **FastAPI**, **Jinja2**, **SQLAlchemy** and **PostgreSQL** — using exactly the columns and dropdowns you specified, with role-based access control.

## 1. Fields (exact order, per your spec — no extra columns)

| # | Column | Type |
|---|---|---|
| 1 | Vehicle No. | Text |
| 2 | Device ID | Text |
| 3 | Company Name | Dropdown (16 companies) |
| 4 | Date | Date picker |
| 5 | Location | Text |
| 6 | Before Images | Link (paste OneDrive folder/file link) → renders as a clickable "View ↗" link |
| 7 | After Images | Link → clickable |
| 8 | Service Form | Link (OneDrive folder) → clickable |
| 9 | PO Number | Text |
| 10 | Device type | Dropdown: `CNo1-KG`, `CN01-KGP`, `CN02-QN`, `8204`, `SP5D`, `SP5IP` |
| 11 | Service Type | Hierarchical dropdown: **New Installation** / **Servicing** / **Inspection** / **Uninstallation** → (if Inspection) **Tempering** or **Redo** |
| 12 | Tempering | Multi-select checkboxes (Water Damage, DSM Cam, ADAS, GPS, Rear View Camera, Sim, SD Card, Main Wiring, Back Camera Wiring) — stored as a comma-separated list |
| 13 | Tempering Evidence | Link (OneDrive folder) → clickable |
| 14 | Service checklist | 15 checkboxes (Verify Camera Angles → Seal All Connections) |
| 15 | Notes | Textarea |

This exact order is used on the **Add Record** form, the **Search** results table, and the **Excel export**.

## 2. Roles (per your spec)

| Role | Dashboard & Search | Add Records | Edit Records | Admin Panel | Delete records | Manage users |
|---|---|---|---|---|---|---|
| **Super Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (incl. other Super Admins) |
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (cannot touch Super Admin accounts) |
| **User** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Field Support** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

- **User** and **Field Support** can add and edit records but never see the Admin Panel link and are redirected if they try to access `/admin` directly.
- **Viewer** can only see and search records; cannot create, edit, or delete.
- **Super Admin** / **Admin** / **Field Support** can delete records. Only Super Admin/Admin can manage users.
- The system always protects the **last active Super Admin/Admin** — it can't be demoted, deactivated, or deleted, so you can never lock yourself out.
- Only a **Super Admin** can create, edit, or delete another **Super Admin** account.

## 3. Features

- **Sign In** — clean, centered login form with gradient background, professional UI, session-based login, bcrypt-hashed passwords.
- **Sign Up** (`/signup`) — self-service account request form (Full Name, Username, Password). New accounts start **unapproved** and cannot sign in — an admin must approve them from the Admin Panel and assign their role first. Login attempts on a pending account show "pending administrator approval" instead of granting access.
- **Dashboard** — add a new record with the full form (all 15 columns + hierarchical Service Type + multi-select Tempering + 15-item checklist), quick search, **View** (read-only modal), **Edit** (modal, pre-filled, hidden for Viewers), **Delete** (Admin roles only). Form is completely hidden for Viewer role users.
- **Search** — filter by Vehicle/Device No., Company Name, Location (default: "Lahore"), Device type, Service Type (including Uninstallation), and a date range; pagination (10/25/50/100/200 rows); **Export to Excel** reproducing the exact 15-column layout — checkbox symbols (☑/☐), clickable links, and `M/D/YYYY` dates.
- **Admin Panel** — **Pending Approvals** (approve a sign-up with a chosen role, or reject/delete the request), add users directly (Full Name → Username → Password → Role), assign roles (Super Admin, Admin, User, Field Support, Viewer), activate/deactivate, reset passwords, delete users.
- Smooth top navbar, flash messages, clean professional styling matching your reference screenshots.

## 4. Prerequisites

- Python 3.10+
- PostgreSQL running locally, with a database created:

```sql
CREATE DATABASE jobtrack;
```

## 5. Setup

```bash
cd vehicle_job_tracker
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env: DATABASE_URL, SECRET_KEY, APP_NAME, default admin credentials
```

`.env`:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobtrack
SECRET_KEY=replace-with-a-long-random-string
APP_NAME=Vehicle Job Tracker
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=Admin@123
DEFAULT_ADMIN_FULLNAME=System Administrator
SESSION_MAX_AGE=28800
```

## 6. Initialize the database

```bash
python scripts/init_db.py
```

This creates all tables and seeds a default **Super Admin** account. **Log in and change the password immediately** via the Admin Panel.

## 7. Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000**.

## 8. Project structure

```
vehicle_job_tracker/
├── app/
│   ├── main.py            # FastAPI app, middleware, router registration
│   ├── config.py          # env-based settings (incl. APP_NAME)
│   ├── database.py        # SQLAlchemy engine/session
│   ├── models.py          # User, Job models
│   ├── choices.py         # every dropdown/checklist list — single source of truth
│   ├── security.py        # bcrypt password hashing
│   ├── dependencies.py    # session auth helpers, flash messages
│   ├── render.py          # shared Jinja2Templates instance + template filters
│   ├── routers/
│   │   ├── auth.py        # /login /logout
│   │   ├── dashboard.py   # /dashboard  (create/update/delete records)
│   │   ├── search.py      # /search  (filters, pagination, /search/export)
│   │   └── admin.py       # /admin  (user management)
│   ├── templates/
│   │   ├── base.html, login.html, dashboard.html, search.html, admin.html
│   │   └── components/navbar.html, checklist_fields.html (shared macros)
│   └── static/             # CSS/JS
├── scripts/init_db.py     # creates tables + seeds default Super Admin
├── requirements.txt
└── .env.example
```

## 9. Project Architecture

### Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **ORM**: SQLAlchemy 2.0 (database abstraction)
- **Database**: PostgreSQL (relational database)
- **Templating**: Jinja2 (server-side HTML rendering)
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Security**: bcrypt (password hashing), session-based auth
- **Export**: OpenPyXL (Excel generation)

### Core Architecture Layers

#### 1. **Request Entry Point** (`app/main.py`)
- FastAPI application initialization
- Middleware setup (Sessions, CORS, exception handlers)
- Router registration for auth, dashboard, search, admin
- Global Jinja2 environment + custom filters

#### 2. **Authentication & Authorization** (`app/dependencies.py`, `app/security.py`)
- Session-based authentication (no JWT, using FastAPI SessionMiddleware)
- `get_current_user()` — retrieves logged-in user from session
- Role-based access control (RBAC) via user.role field
- Password hashing via bcrypt

#### 3. **Data Layer** (`app/models.py`, `app/database.py`)
- **User model**: id, username, full_name, password_hash, role, is_active, created_at
- **Job model**: 15 fields (vehicle_no, device_id, company_name, job_date, location, before_images, after_images, service_form, po_number, device_type, service_type, tempering, tempering_evidence, 15 checklist columns, notes, created_by, created_at)
- SQLAlchemy SessionLocal for DB connections
- Automatic table creation via `create_all()`

#### 4. **Business Logic** (`app/routers/`)
- **`auth.py`**: Login/logout flow, session management
- **`dashboard.py`**: CRUD operations for Job records, role-based permissions
- **`search.py`**: Filtering, pagination, Excel export
- **`admin.py`**: User management (create/edit/delete/reset), role assignment

#### 5. **Configuration & Choices** (`app/config.py`, `app/choices.py`)
- Environment-based settings (DB URL, SECRET_KEY, APP_NAME, session max age)
- **Single source of truth** for all dropdown/checklist options
  - Company names, device types, service types, tempering evidence, checklist fields
  - Changes here automatically propagate to forms, filters, and exports

#### 6. **Rendering** (`app/render.py`, `app/templates/`)
- Jinja2Templates instance with custom filters:
  - `role_label` — converts role slug to display name
  - `evidence_link` — converts URLs to clickable "View ↗" links
  - `split_comma` — splits comma-separated strings for template loops
- Base layout (`base.html`) with navbar, flash messages, CSS/JS injection
- Page-specific templates (login, dashboard, search, admin)
- Reusable components (navbar, checklist inputs, service type selector)

### Data Flow

#### Add/Edit Record Flow
```
Browser Form Submit
    ↓
POST /dashboard/jobs/create or /dashboard/jobs/{id}/update
    ↓
app/routers/dashboard.py (create_job / update_job)
    ↓
Role check: Viewer → denied; User/Field Support/Admin → allowed
    ↓
Form parsing: extract & validate fields
    ↓
_checklist_kwargs() — convert checkbox group to dict
_service_type_value() — combine top-level + inspection sub-type
_tempering_value() — join selected evidence items
    ↓
SQLAlchemy Job object created/updated
    ↓
db.commit()
    ↓
Flash message + redirect to /dashboard
```

#### Search & Export Flow
```
Browser GET /search?filters
    ↓
app/routers/search.py (search_page or search_export)
    ↓
SQLAlchemy filter() + pagination
    ↓
If export: convert to Excel via OpenPyXL
  - Reproduce exact 15-column layout
  - Render checkbox symbols (☑/☐)
  - Make URLs clickable
  - Format dates as M/D/YYYY
    ↓
Return HTML table (view) or .xlsx file (export)
```

### Role-Based Access Control (RBAC)

**Permission Matrix**:
- **Viewer**: Search only (no create, edit, delete)
- **User**: Create & edit records (no delete, no admin)
- **Field Support**: Create, edit & delete records (no admin)
- **Admin**: All record operations + user management + admin panel
- **Super Admin**: Full access, can manage other Super Admins

**Enforcement Points**:
1. Route handlers check `user.role` and `user.is_admin_level` / `user.can_delete_jobs`
2. Templates conditionally show/hide UI elements (`{% if user.role != 'viewer' %}`)
3. Delete operations require the `can_delete_jobs` flag (Admin-level roles + Field Support)
4. Admin Panel access check in router: `if not user.is_admin_level: redirect /dashboard`

### Key Design Patterns

1. **DRY (Don't Repeat Yourself)**: All dropdowns & checklists centralized in `app/choices.py`
2. **Middleware Authentication**: Session-based, automatic user injection into request scope
3. **Template Inheritance**: `base.html` shared across all pages for consistent navbar, styling, flashes
4. **Reusable Macros**: Jinja2 macros in `components/checklist_fields.html` for form fragments
5. **Helper Functions**: `_parse_date()`, `_checklist_kwargs()`, `_service_type_value()` in routers for repeated logic

### Database Schema (Simplified)

**User Table**:
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR UNIQUE NOT NULL,
  full_name VARCHAR,
  password_hash VARCHAR NOT NULL,
  role VARCHAR DEFAULT 'user',  -- super_admin, admin, user, field_support, viewer
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Job Table**:
```sql
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  vehicle_no VARCHAR NOT NULL,
  device_id VARCHAR,
  company_name VARCHAR,
  job_date DATE,
  location VARCHAR,
  before_images VARCHAR,
  after_images VARCHAR,
  service_form VARCHAR,
  po_number VARCHAR,
  device_type VARCHAR,
  service_type VARCHAR,
  tempering VARCHAR,  -- comma-separated evidence list
  tempering_evidence VARCHAR,
  -- 15 boolean checklist columns:
  verify_camera_angles BOOLEAN DEFAULT FALSE,
  memory_card BOOLEAN DEFAULT FALSE,
  sim BOOLEAN DEFAULT FALSE,
  ... (13 more)
  notes TEXT,
  created_by INTEGER FOREIGN KEY references users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 10. Changing a dropdown list later

Every dropdown/checklist option lives in **`app/choices.py`**. Add, remove, or rename an option there and it updates the Add form, Edit form, Search filters, and Excel export everywhere at once — no need to touch templates.

## 11. Deploying to your Linux server (later)

1. Provision PostgreSQL on the server and create the `jobtrack` database.
2. Copy the project, create a venv, `pip install -r requirements.txt`.
3. Set a **strong, unique** `SECRET_KEY` and real DB credentials in `.env` (never commit `.env`).
4. Run behind a process manager, e.g.:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
   ```
   with **systemd** to keep it running, and **nginx** in front as a reverse proxy handling HTTPS (Let's Encrypt).
5. In `app/main.py`, set `https_only=True` on the `SessionMiddleware` once you're serving over HTTPS.
6. Run `python scripts/init_db.py` once on the server to create tables.

## 12. Things you may want to add next

- **Alembic** migrations instead of `create_all`, once the schema is stable in production.
- **Audit log** of who created/edited/deleted each record.
- Bulk **image upload** instead of pasting links, if you want files hosted directly rather than linked from OneDrive.
- **Rate limiting** on `/login`.
