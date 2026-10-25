# app.py
from flask import Flask, request, session, redirect, render_template, g
import sqlite3, os

app = Flask(__name__)
app.secret_key = "dev-secret-do-not-use-in-prod"
DB = "sqli_lab.db"

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    d = g.pop("db", None)
    if d: d.close()

@app.route("/")
def index():
    return redirect("/login")

# ---------- VULNERABLE: Login (auth bypass + UNION possible) ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        # ❌ raw concatenation — intentional SQLi
        q = f"SELECT id, username, role FROM users WHERE username='{u}' AND password='{p}'"
        try:
            row = db().execute(q).fetchone()
        except Exception as e:
            return render_template("login.html", error=f"SQL error: {e}")
        if row:
            session["uid"] = row["id"]
            session["uname"] = row["username"]
            session["role"] = row["role"]
            return redirect("/search")
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------- VULNERABLE: Search (UNION / error-based dump) ----------
@app.route("/search")
def search():
    if "uid" not in session: return redirect("/login")
    term = request.args.get("q", "")
    results, err = [], None
    if term:
        # ❌ raw concat + no column count discipline
        q = f"SELECT id, name, price FROM products WHERE name LIKE '%{term}%'"
        try:
            results = db().execute(q).fetchall()
        except Exception as e:
            err = str(e)
    return render_template("search.html", q=term, results=results, err=err)

# ---------- VULNERABLE: Order history (UNION with users table) ----------
@app.route("/orders")
def orders():
    if "uid" not in session: return redirect("/login")
    uid = request.args.get("uid", session["uid"])   # ❌ uid taken from user input
    q = (f"SELECT o.id, p.name, o.qty, o.note "
         f"FROM orders o JOIN products p ON p.id=o.product_id "
         f"WHERE o.user_id = {uid}")               # ❌ raw int injection point
    try:
        rows = db().execute(q).fetchall()
        err = None
    except Exception as e:
        rows, err = [], str(e)
    return render_template("orders.html", rows=rows, err=err, uid=uid)

# ---------- VULNERABLE: Admin console (role escalation check) ----------
@app.route("/admin")
def admin():
    if "uid" not in session: return redirect("/login")
    # ❌ role check pulled from a second query using session uid, but we trust session
    role = session.get("role")
    if role != "admin":
        return "403 Forbidden — admins only", 403
    key = request.args.get("key", "")
    q = f"SELECT value FROM secrets WHERE key = '{key}'"  # ❌ another SQLi
    try:
        row = db().execute(q).fetchone()
        val = row["value"] if row else None
    except Exception as e:
        val = f"SQL error: {e}"
    return render_template("admin.html", value=val, key=key)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)