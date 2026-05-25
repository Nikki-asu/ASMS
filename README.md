# Automotive Shop Management System (ASMS)

A full-stack web application for managing a small automotive shop's records — owners, vehicles, and service history. Built with Python Flask and PostgreSQL.

## Live Demo
🔗 *Coming soon via Render*

## Features

- **Owner Management** — Add, edit, search, and delete customer records
- **Vehicle Registry** — Register vehicles by VIN with make, model, year, and color; linked to owners via foreign key
- **Service History** — Log and track service records including mileage, labor hours, parts cost, and description
- **Live Search** — Client-side filtering across all three tabs with no page reloads
- **Relational Data** — JOINs across all three tables so service records display vehicle and owner context together
- **Foreign Key Enforcement** — Owners with registered vehicles cannot be deleted; vehicles cascade-delete their service records

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, Vanilla JavaScript (single-page, no framework) |
| Backend | Python 3, Flask |
| Database | PostgreSQL |
| DB Driver | psycopg2 |
| Hosting | Render (web service) |
| Database Hosting | Supabase (PostgreSQL) |

## Project Structure

```
ASMS/
├── asms.py              # Flask app — all routes and DB logic
├── requirements.txt     # Python dependencies
├── Procfile             # Render deployment config
├── templates/
│   └── index.html       # Single-page frontend
└── sql/
    ├── 01_ddl_create_tables.sql   # Schema — owner, vehicle, service_record
    └── 02_dml_insert_data.sql     # Sample data for demo
```

## Database Schema

Three tables with proper relational constraints:

- **owner** (`ownerid`, `name`, `phone`)
- **vehicle** (`vin` PK, `make`, `model`, `year`, `color`, `ownerid` FK)
- **service_record** (`serviceid`, `servicedate`, `mileage`, `description`, `laborhours`, `partscost`, `vin` FK)

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/Nikki-asu/ASMS.git
cd ASMS
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set environment variables**

Create a `.env` file (never committed) or set these in your terminal:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=asms
DB_USER=postgres
DB_PASSWORD=your_password
```

**5. Set up the database**

Run the SQL files against your local PostgreSQL instance:
```bash
psql -U postgres -d asms -f sql/01_ddl_create_tables.sql
psql -U postgres -d asms -f sql/02_dml_insert_data.sql
```

**6. Run the app**
```bash
python asms.py
```

Visit `http://localhost:5000`

## Deployment

Deployed on **Render** connected to a **Supabase** PostgreSQL database. Environment variables are configured in the Render dashboard — no credentials are stored in the codebase.

## Background

Originally built as a CSE 412 (Database Management) course project at Arizona State University. Being extended post-course with production deployment, environment-based configuration, and authentication.
