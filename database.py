
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "carepoint.db"


def get_conn():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as c:

        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT DEFAULT '',
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK(role IN ('patient','doctor','admin')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            fee REAL NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS appointments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY(patient_id) REFERENCES users(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        );
        """)

        c.commit()


def seed_data():

    # Import here to avoid circular imports
    from auth import hash_password

    with get_conn() as c:

        # ADMIN ACCOUNT
        admin = c.execute(
            "SELECT id FROM users WHERE email=?",
            ("admin@carepoint.demo",)
        ).fetchone()

        if not admin:
            c.execute(
                """
                INSERT INTO users
                (name,email,phone,password_hash,role)
                VALUES(?,?,?,?,?)
                """,
                (
                    "CarePoint Admin",
                    "admin@carepoint.demo",
                    "",
                    hash_password("Admin123!"),
                    "admin"
                )
            )

        # DOCTOR ACCOUNT
        doctor = c.execute(
            "SELECT id FROM users WHERE email=?",
            ("doctor@carepoint.demo",)
        ).fetchone()

        if not doctor:

            c.execute(
                """
                INSERT INTO users
                (name,email,phone,password_hash,role)
                VALUES(?,?,?,?,?)
                """,
                (
                    "Aarav Sharma",
                    "doctor@carepoint.demo",
                    "9876543210",
                    hash_password("Doctor123!"),
                    "doctor"
                )
            )

            doctor_id = c.execute(
                "SELECT id FROM users WHERE email=?",
                ("doctor@carepoint.demo",)
            ).fetchone()["id"]

            c.execute(
                """
                INSERT INTO doctors
                (user_id,name,specialty,fee,active)
                VALUES(?,?,?,?,?)
                """,
                (
                    doctor_id,
                    "Aarav Sharma",
                    "General Physician",
                    500,
                    1
                )
            )

        # PATIENT ACCOUNT
        patient = c.execute(
            "SELECT id FROM users WHERE email=?",
            ("patient@carepoint.demo",)
        ).fetchone()

        if not patient:
            c.execute(
                """
                INSERT INTO users
                (name,email,phone,password_hash,role)
                VALUES(?,?,?,?,?)
                """,
                (
                    "Demo Patient",
                    "patient@carepoint.demo",
                    "9876501234",
                    hash_password("Patient123!"),
                    "patient"
                )
            )

        c.commit()
