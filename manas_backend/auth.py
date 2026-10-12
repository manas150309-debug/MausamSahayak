"""Local account storage and validation for the hosted dashboard."""
from __future__ import annotations

import re
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE = re.compile(r"^\+91[6-9]\d{9}$")
LOCATIONS = ("All NCR", "Faridabad", "Delhi", "Greater Noida")


class ValidationError(ValueError):
    pass


def normalise_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10:
        digits = "91" + digits
    phone = "+" + digits
    if not PHONE.fullmatch(phone):
        raise ValidationError("Enter a valid Indian mobile number")
    return phone


def create_user(conn, payload: dict, now: int) -> dict:
    name = " ".join(str(payload.get("name", "")).split())
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    location = str(payload.get("alert_location", "All NCR"))
    language = "hi" if payload.get("language") == "hi" else "en"
    if len(name) < 2 or len(name) > 80:
        raise ValidationError("Name must be 2 to 80 characters")
    if len(email) > 254 or not EMAIL.fullmatch(email):
        raise ValidationError("Enter a valid email address")
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        raise ValidationError("Password needs at least 8 characters, one letter and one number")
    if location not in LOCATIONS:
        raise ValidationError("Choose a supported alert location")
    phone = normalise_phone(str(payload.get("phone", "")))
    try:
        cur = conn.execute(
            "INSERT INTO users(name,email,phone,password_hash,alert_location,language,created_at) VALUES (?,?,?,?,?,?,?)",
            (name, email, phone, generate_password_hash(password), location, language, int(now)),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValidationError("An account with this email already exists") from exc
    return public_user(conn.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone())


def authenticate(conn, email: str, password: str, now: int) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE email=? COLLATE NOCASE AND active=1", (email.strip(),)).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        return None
    conn.execute("UPDATE users SET last_login_at=? WHERE id=?", (int(now), row["id"]))
    conn.commit()
    return public_user(row)


def get_user(conn, user_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM users WHERE id=? AND active=1", (int(user_id),)).fetchone()
    return public_user(row) if row else None


def public_user(row) -> dict:
    return {key: row[key] for key in (
        "id", "name", "email", "phone", "alert_location", "language",
        "email_alerts", "sms_alerts", "created_at", "last_login_at",
    )}


def update_preferences(conn, user_id: int, payload: dict) -> dict:
    location = str(payload.get("alert_location", "All NCR"))
    if location not in LOCATIONS:
        raise ValidationError("Choose a supported alert location")
    language = "hi" if payload.get("language") == "hi" else "en"
    conn.execute(
        "UPDATE users SET alert_location=?,language=?,email_alerts=?,sms_alerts=? WHERE id=?",
        (location, language, int(bool(payload.get("email_alerts", True))),
         int(bool(payload.get("sms_alerts", True))), int(user_id)),
    )
    conn.commit()
    return get_user(conn, user_id)
