import sqlite3
import uuid
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "elcomputers_secret"

# -----------------------------
# DATABASE SETUP
# -----------------------------

conn = sqlite3.connect("repairs.db")
cursor = conn.cursor()

# Repairs table
cursor.execute("""
CREATE TABLE IF NOT EXISTS repairs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id TEXT,
    name TEXT,
    phone TEXT,
    device TEXT,
    problem TEXT,
    status TEXT
)
""")

# Technicians table
cursor.execute("""
CREATE TABLE IF NOT EXISTS technicians(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

conn.commit()
conn.close()

# -----------------------------
# HOME PAGE
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# BOOK REPAIR
# -----------------------------

@app.route("/book", methods=["GET","POST"])
def book():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        device = request.form["device"]
        problem = request.form["problem"]

        repair_id = "EL" + str(uuid.uuid4())[:8]

        conn = sqlite3.connect("repairs.db")
        cursor = conn.cursor()

        cursor.execute(
        "INSERT INTO repairs (repair_id,name,phone,device,problem,status) VALUES (?,?,?,?,?,?)",
        (repair_id,name,phone,device,problem,"Received")
        )

        conn.commit()
        conn.close()

        return f"Repair booked successfully! Your Repair ID is {repair_id}"

    return render_template("book.html")


# -----------------------------
# TRACK REPAIR
# -----------------------------

@app.route("/track", methods=["GET","POST"])
def track():

    repair = None

    if request.method == "POST":

        repair_id = request.form["repair_id"]

        conn = sqlite3.connect("repairs.db")
        cursor = conn.cursor()

        cursor.execute(
        "SELECT * FROM repairs WHERE repair_id=?",
        (repair_id,)
        )

        repair = cursor.fetchone()

        conn.close()

    return render_template("track.html", repair=repair)


# -----------------------------
# UPDATE REPAIR STATUS
# -----------------------------

@app.route("/update/<repair_id>", methods=["POST"])
def update(repair_id):

    import pywhatkit

    status = request.form["status"]

    conn = sqlite3.connect("repairs.db")
    cursor = conn.cursor()

    cursor.execute(
    "UPDATE repairs SET status=? WHERE repair_id=?",
    (status,repair_id)
    )

    conn.commit()

    cursor.execute(
    "SELECT phone FROM repairs WHERE repair_id=?",
    (repair_id,)
    )

    phone = cursor.fetchone()[0]

    conn.close()

    if status == "Completed":

        message = f"""
EL COMPUTERS & ELECTRONICS

Repair Completed

Repair ID: {repair_id}

Please collect your device from our shop.
"""

        pywhatkit.sendwhatmsg_instantly("+265"+phone, message)

    return redirect("/admin")


# -----------------------------
# INVOICE
# -----------------------------

@app.route("/invoice/<repair_id>")
def invoice(repair_id):

    conn = sqlite3.connect("repairs.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT * FROM repairs WHERE repair_id=?",
    (repair_id,)
    )

    repair = cursor.fetchone()

    conn.close()

    return render_template("invoice.html", repair=repair)


# -----------------------------
# SEARCH REPAIR
# -----------------------------

@app.route("/search")
def search():

    phone = request.args.get("phone")

    conn = sqlite3.connect("repairs.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT * FROM repairs WHERE phone=?",
    (phone,)
    )

    repairs = cursor.fetchall()

    conn.close()

    return render_template("dashboard.html", repairs=repairs)


# -----------------------------
# ADMIN LOGIN
# -----------------------------

@app.route("/admin", methods=["GET","POST"])
def admin():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "elcomputers":

            session["admin"] = True
            return redirect("/dashboard")

        else:
            return render_template(
            "admin_login.html",
            error="Invalid username or password"
            )

    return render_template("admin_login.html")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn = sqlite3.connect("repairs.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM repairs")
    repairs = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM repairs")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM repairs WHERE status='Completed'")
    completed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM repairs WHERE status='Repairing'")
    repairing = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        repairs=repairs,
        total=total,
        completed=completed,
        repairing=repairing
    )


# -----------------------------
# TECHNICIAN LOGIN
# -----------------------------

@app.route("/technician", methods=["GET","POST"])
def technician():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("repairs.db")
        cursor = conn.cursor()

        cursor.execute(
        "SELECT * FROM technicians WHERE username=? AND password=?",
        (username,password)
        )

        tech = cursor.fetchone()

        if tech:

            cursor.execute("SELECT * FROM repairs")
            repairs = cursor.fetchall()

            conn.close()

            return render_template("tech_dashboard.html", repairs=repairs)

    return render_template("tech_login.html")


# -----------------------------
# ANALYTICS
# -----------------------------

@app.route("/analytics")
def analytics():

    conn = sqlite3.connect("repairs.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT status, COUNT(*) FROM repairs GROUP BY status"
    )

    data = cursor.fetchall()

    conn.close()

    return render_template("analytics.html", data=data)


# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


# -----------------------------
# RUN SERVER
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)