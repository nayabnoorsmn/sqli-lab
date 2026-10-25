# init_db.py
import sqlite3, os, hashlib

DB = "sqli_lab.db"
if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

c.executescript("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'student',
    email TEXT
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    stock INTEGER
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    qty INTEGER,
    note TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(product_id) REFERENCES products(id)
);

CREATE TABLE secrets (
    id INTEGER PRIMARY KEY,
    key TEXT,
    value TEXT
);
""")

def h(p): return hashlib.sha256(p.encode()).hexdigest()

users = [
    ("amna",   h("password123"), "student", "amna@school.edu"),
    ("ibrahim",     h("qwerty"),      "student", "ibrahim@school.edu"),
    ("hamza", h("letmein"),     "student", "hamza@school.edu"),
    ("admin",   h("S3cr3tAdm1n!"), "admin",  "admin@school.edu"),
]
c.executemany("INSERT INTO users (username,password,role,email) VALUES (?,?,?,?)", users)

products = [
    ("Cybersecurity Handbook", 49.99, 20),
    ("Ethical Hacking Tool",           89.50, 5),
    ("React JS Masterclass",           3.25, 100),
    ("Network Cable",    55.00, 8),
    ("SQLi Survival Guide", 19.99, 50),
]
c.executemany("INSERT INTO products (name,price,stock) VALUES (?,?,?)", products)

orders = [
    (1, 1, 1, "Security Audit"),
    (2, 3, 5, "PenTest Report"),
    (3, 4, 2, "Web Development Project"),
    (1, 5, 1, "Lab Practice"),
]
c.executemany("INSERT INTO orders (user_id,product_id,qty,note) VALUES (?,?,?,?)", orders)

secrets = [
    (1, "FLAG_ADMIN", "FLAG{sqli_to_admin_pwn3d}"),
    (2, "DB_BACKUP_KEY", "bkp_9f8e7d6c5b4a3210"),
]
c.executemany("INSERT INTO secrets (id,key,value) VALUES (?,?,?)", secrets)

conn.commit()
conn.close()
print("[+] Database created: sqli_lab.db")