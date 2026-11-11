
import hashlib
import hmac
import os

from database import get_conn


def hash_password(password):

    salt = os.urandom(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        200000
    )

    return salt.hex() + ":" + digest.hex()


def verify_password(password, stored):

    try:
        salt_hex, digest_hex = stored.split(":")

        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            200000
        )

        return hmac.compare_digest(
            digest.hex(),
            digest_hex
        )

    except Exception:
        return False


def login_user(email, password):

    with get_conn() as c:

        row = c.execute(
            """
            SELECT * FROM users
            WHERE lower(email)=lower(?)
            """,
            (email.strip(),)
        ).fetchone()

    if row and verify_password(
        password,
        row["password_hash"]
    ):
        return dict(row)

    return None


def register_user(name, email, phone, password):

    try:

        with get_conn() as c:

            c.execute(
                """
                INSERT INTO users
                (name,email,phone,password_hash,role)
                VALUES(?,?,?,?,?)
                """,
                (
                    name.strip(),
                    email.strip().lower(),
                    phone.strip(),
                    hash_password(password),
                    "patient"
                )
            )

            c.commit()

        return True, "Account created. You can now sign in."

    except Exception:

        return False, "An account with that email may already exist."


def logout_user():

    import streamlit as st

    st.session_state.pop("user", None)

    st.rerun()
