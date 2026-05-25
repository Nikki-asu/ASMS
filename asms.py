from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changeme-in-production")

# ---------------------------------------------------------------------------
# Auth setup
# ---------------------------------------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

USERS = {
    os.environ.get("ADMIN_USERNAME", "admin"): {
        "password": os.environ.get("ADMIN_PASSWORD", "changeme"),
        "role": "admin"
    },
    "demo": {
        "password": "demo123",
        "role": "demo"
    }
}

class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role

@login_manager.user_loader
def load_user(username):
    if username in USERS:
        return User(username, USERS[username]["role"])
    return None

def is_admin():
    return current_user.is_authenticated and current_user.role == "admin"

def demo_blocked():
    return jsonify({"error": "Demo limit reached — try again in a minute."}), 403

# ---------------------------------------------------------------------------
# Rate limiter — 5 writes per minute for demo users only
# ---------------------------------------------------------------------------

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],  # no global limit
    storage_uri="memory://"
)

def demo_limit():
    """Only apply rate limit if the current user is in demo role."""
    if current_user.is_authenticated and current_user.role == "demo":
        return "5 per minute"
    return "9999 per minute"  # effectively no limit for admin

# ---------------------------------------------------------------------------
# Database connections — admin uses real DB, demo uses demo DB
# ---------------------------------------------------------------------------

ADMIN_DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "asms"),
    "user":     os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),
}

DEMO_DB_CONFIG = {
    "host":     os.environ.get("DEMO_DB_HOST", "localhost"),
    "port":     int(os.environ.get("DEMO_DB_PORT", 5432)),
    "database": os.environ.get("DEMO_DB_NAME", "postgres"),
    "user":     os.environ.get("DEMO_DB_USER", "postgres"),
    "password": os.environ.get("DEMO_DB_PASSWORD", ""),
}

def get_conn():
    """Return a connection to the correct database based on the current user's role."""
    if current_user.is_authenticated and current_user.role == "demo":
        return psycopg2.connect(**DEMO_DB_CONFIG)
    return psycopg2.connect(**ADMIN_DB_CONFIG)

# ---------------------------------------------------------------------------
# Demo database midnight reset
# Wipes the demo DB and reseeds it from the original sample data
# ---------------------------------------------------------------------------

DEMO_OWNERS = [
    (1, "Freddie Mercury", "928-555-0101"),
    (2, "Janis Joplin",    "602-555-0234"),
    (3, "David Bowie",     "480-555-0387"),
    (4, "Stevie Nicks",    "623-555-0412"),
    (5, "Jim Morrison",    None),
]

DEMO_VEHICLES = [
    ("1HGBH41JXMN109186", "Toyota", "4Runner", 2022, "Blue",  4),
    ("2FMDK48C07BB12345", "Ford",   "Edge",    2022, "White", 1),
    ("3FADP4BJ5BM100234", "Ford",   "F-150",   2016, "Black", 3),
    ("1G1BE5SM4G7123456", "Chevy",  "HHR",     2016, "White", 2),
    ("1FMCU9J94GUB12345", "Ford",   "Ranger",  1997, "Blue",  1),
    ("1FTPW14V87FB12345", "Ford",   "Courier", 1992, "Blue",  5),
    ("1G6KD57Y55U123456", "Mercury","Cougar",  1952, "Red",   5),
]

DEMO_SERVICE_RECORDS = [
    ("2026-02-25", 27620, "Coolant flush and new battery",   1.75, 189.50, "1HGBH41JXMN109186"),
    ("2026-02-05", 121100,"Transmission fluid change",       1.50, 89.00,  "1G1BE5SM4G7123456"),
    ("2026-02-04", 74220, "Oil change",                      1.00, 52.80,  "1FMCU9J94GUB12345"),
    ("2025-11-30", 157700,"New windshield wipers",           0.25, 24.99,  "1FTPW14V87FB12345"),
    ("2025-11-28", 63200, "Detail cleaning",                 2.00, 0.00,   "2FMDK48C07BB12345"),
    ("2025-11-16", 89500, "Oil change",                      0.75, 42.93,  "1HGBH41JXMN109186"),
    ("2025-10-22", 46120, "New tires",                       0.50, 329.99, "1G1BE5SM4G7123456"),
    ("2025-10-14", 135400,"Oil change",                      0.75, 54.50,  "3FADP4BJ5BM100234"),
    ("2025-08-08", 31200, "Coolant flush",                   1.50, 32.65,  "1HGBH41JXMN109186"),
    ("2025-07-31", 55000, "Oil change and tire rotation",    1.00, 49.40,  "3FADP4BJ5BM100234"),
    ("2025-07-13", 87530, "Oil change",                      0.75, 38.80,  "1G1BE5SM4G7123456"),
]

def reset_demo_db():
    """Wipe and reseed the demo database. Runs at midnight daily."""
    try:
        conn = psycopg2.connect(**DEMO_DB_CONFIG)
        cur = conn.cursor()

        # wipe in reverse FK order
        cur.execute("DELETE FROM service_record")
        cur.execute("DELETE FROM vehicle")
        cur.execute("DELETE FROM owner")

        # reset sequences so IDs start from 1 again
        cur.execute("ALTER SEQUENCE owner_ownerid_seq RESTART WITH 1")
        cur.execute("ALTER SEQUENCE service_record_serviceid_seq RESTART WITH 1")

        # reseed owners
        for row in DEMO_OWNERS:
            cur.execute(
                "INSERT INTO owner (ownerid, name, phone) VALUES (%s, %s, %s)",
                row
            )

        # reseed vehicles
        for row in DEMO_VEHICLES:
            cur.execute(
                "INSERT INTO vehicle (vin, make, model, year, color, ownerid) VALUES (%s,%s,%s,%s,%s,%s)",
                row
            )

        # reseed service records
        for row in DEMO_SERVICE_RECORDS:
            cur.execute(
                """INSERT INTO service_record
                   (servicedate, mileage, description, laborhours, partscost, vin)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                row
            )

        conn.commit()
        cur.close(); conn.close()
        print("Demo database reset successfully.")
    except Exception as e:
        print(f"Demo reset failed: {e}")

# schedule midnight reset
scheduler = BackgroundScheduler()
scheduler.add_job(reset_demo_db, "cron", hour=0, minute=0)
scheduler.start()

# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user_data = USERS.get(username)
        if user_data and user_data["password"] == password:
            login_user(User(username, user_data["role"]))
            return redirect(url_for("index"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# serves the main page
@app.route("/")
@login_required
def index():
    return render_template("index.html", role=current_user.role)

# owners - get all, add, update, delete

@app.route("/owners", methods=["GET"])
@login_required
def get_owners():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM owner ORDER BY ownerid")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/owners", methods=["POST"])
@login_required
@limiter.limit(demo_limit)
def add_owner():
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO owner (name, phone) VALUES (%s, %s) RETURNING ownerid",
        (data["name"], data.get("phone") or None)
    )
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return jsonify({"ownerid": new_id, "message": "owner added."})

@app.route("/owners/<int:ownerid>", methods=["PUT"])
@login_required
@limiter.limit(demo_limit)
def update_owner(ownerid):
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE owner SET name=%s, phone=%s WHERE ownerid=%s",
        (data["name"], data.get("phone") or None, ownerid)
    )
    conn.commit(); cur.close(); conn.close()
    return jsonify({"message": "owner updated."})

@app.route("/owners/<int:ownerid>", methods=["DELETE"])
@login_required
@limiter.limit(demo_limit)
def delete_owner(ownerid):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM owner WHERE ownerid=%s", (ownerid,))
        conn.commit()
        msg = "owner deleted."
    except psycopg2.errors.ForeignKeyViolation:
        # cant delete an owner who still has vehicles linked to them
        conn.rollback()
        return jsonify({"error": "Cannot delete owner with registered vehicles."}), 400
    finally:
        cur.close(); conn.close()
    return jsonify({"message": msg})

# vehicles - get all, add, delete
# note: no update route for vehicles since vin is the primary key and shouldnt change

@app.route("/vehicles", methods=["GET"])
@login_required
def get_vehicles():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # joining owner so we can show the owner name in the table
    cur.execute("""
        SELECT v.vin, v.make, v.model, v.year, v.color, v.ownerid, o.name AS owner_name
        FROM vehicle v
        JOIN owner o ON v.ownerid = o.ownerid
        ORDER BY v.year DESC
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/vehicles", methods=["POST"])
@login_required
@limiter.limit(demo_limit)
def add_vehicle():
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO vehicle (vin, make, model, year, color, ownerid) VALUES (%s,%s,%s,%s,%s,%s)",
        (data["vin"], data["make"], data["model"], int(data["year"]),
         data.get("color") or None, int(data["ownerid"]))
    )
    conn.commit(); cur.close(); conn.close()
    return jsonify({"message": "vehicle added."})

@app.route("/vehicles/<vin>", methods=["DELETE"])
@login_required
@limiter.limit(demo_limit)
def delete_vehicle(vin):
    conn = get_conn()
    cur = conn.cursor()
    try:
        # have to delete service records first or postgres throws a foreign key error
        cur.execute("DELETE FROM service_record WHERE vin=%s", (vin,))
        cur.execute("DELETE FROM vehicle WHERE vin=%s", (vin,))
        conn.commit()
        msg = "vehicle and its service records deleted."
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close(); conn.close()
    return jsonify({"message": msg})

# service records - get all or filter by vin, add, update, delete

@app.route("/service_records", methods=["GET"])
@login_required
def get_service_records():
    vin = request.args.get("vin")
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if vin:
        # filter by vin if one was passed in the query string
        cur.execute("""
            SELECT sr.*, v.make, v.model, v.year, o.name AS owner_name
            FROM service_record sr
            JOIN vehicle v ON sr.vin = v.vin
            JOIN owner   o ON v.ownerid = o.ownerid
            WHERE sr.vin = %s
            ORDER BY sr.servicedate DESC
        """, (vin,))
    else:
        # otherwise just grab everything
        cur.execute("""
            SELECT sr.*, v.make, v.model, v.year, o.name AS owner_name
            FROM service_record sr
            JOIN vehicle v ON sr.vin = v.vin
            JOIN owner   o ON v.ownerid = o.ownerid
            ORDER BY sr.servicedate DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/service_records", methods=["POST"])
@login_required
@limiter.limit(demo_limit)
def add_service_record():
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO service_record
           (servicedate, mileage, description, laborhours, partscost, vin)
           VALUES (%s,%s,%s,%s,%s,%s) RETURNING serviceid""",
        (data["servicedate"], int(data["mileage"]), data["description"],
         float(data["laborhours"]), float(data.get("partscost", 0)), data["vin"])
    )
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return jsonify({"serviceid": new_id, "message": "service record added."})

@app.route("/service_records/<int:serviceid>", methods=["PUT"])
@login_required
@limiter.limit(demo_limit)
def update_service_record(serviceid):
    data = request.json
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """UPDATE service_record
           SET servicedate=%s, mileage=%s, description=%s, laborhours=%s, partscost=%s
           WHERE serviceid=%s""",
        (data["servicedate"], int(data["mileage"]), data["description"],
         float(data["laborhours"]), float(data.get("partscost", 0)), serviceid)
    )
    conn.commit(); cur.close(); conn.close()
    return jsonify({"message": "service record updated."})

@app.route("/service_records/<int:serviceid>", methods=["DELETE"])
@login_required
@limiter.limit(demo_limit)
def delete_service_record(serviceid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM service_record WHERE serviceid=%s", (serviceid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"message": "service record deleted."})

if __name__ == "__main__":
    app.run(debug=True)
