"""SMS fallback for RED alerts (Swati). Default is a dry-run logger so nothing is sent by accident."""
import logging
import os
import re

import requests

log = logging.getLogger("sms")
INDIAN_MOBILE = re.compile(r"^\+91[6-9]\d{9}$")


def valid_phone(p):
    return bool(p and INDIAN_MOBILE.match(p))


class DryRunSender:
    def __init__(self):
        self.sent = []

    def send(self, to, body):
        log.warning("[SMS dry-run] to=%s body=%s", to, body)
        self.sent.append((to, body))
        return True


class TwilioSender:
    def __init__(self, sid, token, from_number, session=requests):
        self.sid, self.token, self.from_, self.s = sid, token, from_number, session

    def send(self, to, body):
        try:
            r = self.s.post(f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json",
                            data={"To": to, "From": self.from_, "Body": body}, auth=(self.sid, self.token), timeout=15)
            ok = r.status_code in (200, 201)
            if not ok:
                log.error("twilio error %s", r.status_code)
            return ok
        except Exception:
            log.exception("sms send failed")
            return False


def make_sender_from_env():
    provider = os.environ.get("SMS_PROVIDER", "dryrun").lower()
    if provider == "twilio":
        return TwilioSender(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"], os.environ["TWILIO_FROM"])
    return DryRunSender()
