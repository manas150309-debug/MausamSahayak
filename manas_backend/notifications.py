"""Email and SMS delivery with auditable dry-run fallbacks."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from .config import Settings

log = logging.getLogger("notifications")


def _mask(value: str) -> str:
    if "@" in value:
        left, right = value.split("@", 1)
        return (left[:2] + "***@" + right)[:120]
    return ("*" * max(0, len(value) - 4) + value[-4:])[:120]


def send_email(settings: Settings, to: str, subject: str, body: str) -> tuple[str, str]:
    if not (settings.smtp_host and settings.smtp_from):
        log.warning("[EMAIL dry-run] to=%s subject=%s", to, subject)
        return "dry_run", "SMTP credentials not configured"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.smtp_from, to, subject
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return "sent", "SMTP accepted"
    except Exception as exc:
        log.exception("email delivery failed")
        return "failed", type(exc).__name__


def send_sms(settings: Settings, to: str, body: str) -> tuple[str, str]:
    if settings.sms_provider.lower() != "twilio" or not all((settings.twilio_sid, settings.twilio_token, settings.twilio_from)):
        log.warning("[SMS dry-run] to=%s body=%s", to, body)
        return "dry_run", "Twilio credentials not configured"
    from swati_bot.sms import TwilioSender
    ok = TwilioSender(settings.twilio_sid, settings.twilio_token, settings.twilio_from).send(to, body)
    return ("sent", "Twilio accepted") if ok else ("failed", "Twilio rejected request")


def _record(conn, user_id: int, alert_id: int | None, channel: str, destination: str,
            result: tuple[str, str], now: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO notification_deliveries(user_id,alert_id,channel,destination_masked,status,detail,created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (user_id, alert_id, channel, _mask(destination), result[0], result[1], int(now)),
    )
    conn.commit()


def send_welcome(conn, user: dict, settings: Settings, now: int) -> dict:
    subject = "MausamSahayak alerts are active"
    body = (
        f"Hello {user['name']},\n\nYour {user['alert_location']} weather and flood alert subscription is active. "
        "MausamSahayak advisories support awareness; always follow IMD, CWC, NDMA and local authorities."
    )
    email_result = send_email(settings, user["email"], subject, body)
    sms_result = send_sms(settings, user["phone"], f"MausamSahayak: {user['alert_location']} alerts active. Official authority advice takes priority.")
    _record(conn, user["id"], None, "email", user["email"], email_result, now)
    _record(conn, user["id"], None, "sms", user["phone"], sms_result, now)
    return {"email": email_result[0], "sms": sms_result[0]}


def dispatch_alerts(conn, alerts: list[dict], settings: Settings, now: int) -> int:
    sent = 0
    for alert in alerts:
        if alert["level_name"] == "GREEN":
            continue
        node = conn.execute("SELECT name,district,state FROM nodes WHERE node_id=?", (alert["node_id"],)).fetchone()
        if node is None:
            continue
        users = conn.execute(
            "SELECT * FROM users WHERE active=1 AND (alert_location='All NCR' OR alert_location=?)",
            (node["district"],),
        ).fetchall()
        for row in users:
            reasons = ", ".join(r.get("code", "risk signal") for r in alert.get("reasons", [])[:3]) or "risk status changed"
            subject = f"{alert['level_name']} {alert['kind'].title()} Alert — {node['district']}"
            body = (
                f"MausamSahayak alert for {node['name']} ({node['district']}, {node['state']}): "
                f"{alert['kind']} risk is {alert['level_name']}. Reasons: {reasons}. "
                "Avoid risky areas and follow official local-authority guidance."
            )
            if row["email_alerts"]:
                result = send_email(settings, row["email"], subject, body)
                _record(conn, row["id"], alert["id"], "email", row["email"], result, now)
                sent += result[0] in ("sent", "dry_run")
            if row["sms_alerts"]:
                sms_body = f"MausamSahayak {alert['level_name']} {alert['kind']} alert: {node['district']} - {reasons}. Follow authorities."
                result = send_sms(settings, row["phone"], sms_body[:320])
                _record(conn, row["id"], alert["id"], "sms", row["phone"], result, now)
                sent += result[0] in ("sent", "dry_run")
    return sent


def delivery_history(conn, user_id: int, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        "SELECT id,alert_id,channel,destination_masked,status,detail,created_at FROM notification_deliveries "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?", (int(user_id), min(int(limit), 100)),
    ).fetchall()
    return [dict(row) for row in rows]
