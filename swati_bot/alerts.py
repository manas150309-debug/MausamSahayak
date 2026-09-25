"""Decide who gets which alert (Swati). Pure logic, no network."""
from dataclasses import dataclass
from typing import List, Optional

from . import formatters, sms

LEVEL = {"GREEN": 0, "UNKNOWN": 1, "YELLOW": 2, "ORANGE": 3, "RED": 4}


@dataclass
class Notification:
    chat_id: int
    text: str
    sms_to: Optional[str] = None
    sms_text: Optional[str] = None


def should_notify(alert) -> bool:
    lvl, prev = alert["level"], alert.get("previous_level") or 0
    if alert["kind"] == "heat":
        # heat YELLOW is common in summer - only push ORANGE/RED, and the drop from them
        return (lvl >= LEVEL["ORANGE"] and lvl > prev) or (prev >= LEVEL["ORANGE"] and lvl < prev)
    if lvl > prev:
        return lvl >= LEVEL["UNKNOWN"]
    return prev >= LEVEL["ORANGE"]           # tell people when a serious level is lowered


def plan_notifications(store, alerts, node_names: dict) -> List[Notification]:
    out = []
    for a in alerts:
        if not should_notify(a):
            continue
        name = node_names.get(a["node_id"], a["node_id"])
        for u in store.subscribers_for(a["node_id"]):
            lang = u["lang"]
            n = Notification(u["chat_id"], formatters.format_alert(lang, a, name))
            if a["level_name"] == "RED" and a["level"] > (a.get("previous_level") or 0) and sms.valid_phone(u.get("phone")):
                n.sms_to, n.sms_text = u["phone"], formatters.format_sms(lang, a, name)
            out.append(n)
    return out
