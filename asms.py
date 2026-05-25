from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

# db connection config 
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", 5432)),
    "database": os.environ.get("DB_NAME", "asms"),
    "user":     os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", ""),   
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

# serves the main page
@app.route("/")
def index():
    return render_template("index.html")

# owners - get all, add, update, delete

@app.route("/owners", methods=["GET"])
def get_owners():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM owner ORDER BY ownerid")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/owners", methods=["POST"])
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
def delete_service_record(serviceid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM service_record WHERE serviceid=%s", (serviceid,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"message": "service record deleted."})

if __name__ == "__main__":
    app.run(debug=True)