"""Conversation logic, independent of Telegram (Swati). bot.py only sends what this returns."""
import re
from dataclasses import dataclass

from . import formatters, i18n, intents, sms
from .api_client import ApiError
from .i18n import t

LATLON = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[, ]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


@dataclass
class Reply:
    text: str
    ask_location: bool = False
    ask_language: bool = False
    ask_irrigation: bool = False


class BotLogic:
    def __init__(self, api, store):
        self.api, self.store = api, store

    # ---------------------------------------------------------------- helpers
    def lang(self, chat_id):
        u = self.store.get_user(chat_id)
        return i18n.norm_lang(u["lang"]) if u else "hi"

    def _station(self, chat_id):
        """(user, None) when the user has a usable station, else (None, Reply)."""
        lang = self.lang(chat_id)
        u = self.store.get_user(chat_id)
        if not u or u.get("lat") is None:
            return None, Reply(t(lang, "need_location") + "\n" + t(lang, "ask_location"), ask_location=True)
        if not u.get("node_id"):
            return None, Reply(t(lang, "location_far", name=u.get("node_name") or "-", km=u.get("distance_km") or "?"),
                               ask_location=True)
        return u, None

    def _api_down(self, chat_id):
        return Reply(t(self.lang(chat_id), "api_down"))

    # --------------------------------------------------------------- commands
    def start(self, chat_id):
        if self.store.get_user(chat_id) is None:
            self.store.upsert_user(chat_id, lang="hi")
        return Reply(t("hi", "welcome") + "\n\n" + t("en", "welcome"), ask_language=True)

    def set_language(self, chat_id, lang):
        lang = i18n.norm_lang(lang)
        u = self.store.upsert_user(chat_id, lang=lang)
        text = t(lang, "language_set")
        if u.get("lat") is None:
            return Reply(text + "\n" + t(lang, "ask_location"), ask_location=True)
        return Reply(text)

    def ask_location(self, chat_id):
        return Reply(t(self.lang(chat_id), "ask_location"), ask_location=True)

    def set_location(self, chat_id, lat, lon):
        lang = self.lang(chat_id)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return Reply(t(lang, "ask_location"), ask_location=True)
        try:
            res = self.api.nearest(lat, lon)
        except ApiError as e:
            if e.status == 404:
                self.store.upsert_user(chat_id, lat=lat, lon=lon, node_id=None)
                return Reply(t(lang, "no_stations"))
            return self._api_down(chat_id)
        node, km = res["node"], res["distance_km"]
        name = node.get("name") or node["node_id"]
        if not res["within_range"]:
            self.store.upsert_user(chat_id, lat=lat, lon=lon, node_id=None, node_name=name, distance_km=km, subscribed=0)
            return Reply(t(lang, "location_far", name=name, km=km))
        self.store.upsert_user(chat_id, lat=lat, lon=lon, node_id=node["node_id"], node_name=name, distance_km=km)
        return Reply(t(lang, "location_saved", name=name, km=km))

    def current(self, chat_id):
        u, bad = self._station(chat_id)
        if bad:
            return bad
        try:
            risk = self.api.risk(u["node_id"])
        except ApiError:
            return self._api_down(chat_id)
        return Reply(formatters.format_current(u["lang"], risk, u["node_name"], u["distance_km"]) + "\n\n" + t(u["lang"], "disclaimer"))

    def risk(self, chat_id):
        u, bad = self._station(chat_id)
        if bad:
            return bad
        try:
            risk = self.api.risk(u["node_id"])
        except ApiError:
            return self._api_down(chat_id)
        return Reply(formatters.format_risk(u["lang"], risk, u["node_name"], u["distance_km"]))

    def crop(self, chat_id, irrigated=None):
        u, bad = self._station(chat_id)
        if bad:
            return bad
        if irrigated is None:
            return Reply(t(u["lang"], "crop_ask"), ask_irrigation=True)
        try:
            advice = self.api.crop_advice(u["lat"], u["lon"], irrigated)
        except ApiError as e:
            if e.status == 404:
                return Reply(t(u["lang"], "no_station_crop"))
            return self._api_down(chat_id)
        return Reply(formatters.format_crop(u["lang"], advice))

    def subscribe(self, chat_id):
        u, bad = self._station(chat_id)
        if bad:
            return bad
        self.store.upsert_user(chat_id, subscribed=1)
        return Reply(t(u["lang"], "subscribed", name=u["node_name"]))

    def unsubscribe(self, chat_id):
        self.store.upsert_user(chat_id, subscribed=0)
        return Reply(t(self.lang(chat_id), "unsubscribed"))

    def set_phone(self, chat_id, arg):
        lang = self.lang(chat_id)
        arg = (arg or "").strip().replace(" ", "")
        if arg.lower() in ("remove", "delete", "हटाएँ", "हटाएं"):
            self.store.upsert_user(chat_id, phone=None)
            return Reply(t(lang, "phone_removed"))
        if not sms.valid_phone(arg):
            return Reply(t(lang, "phone_invalid"))
        self.store.upsert_user(chat_id, phone=arg)
        return Reply(t(lang, "phone_saved"))

    def help(self, chat_id):
        return Reply(t(self.lang(chat_id), "help"))

    # ------------------------------------------------------------- free text
    def handle_text(self, chat_id, text):
        m = LATLON.match(text or "")
        if m:
            return self.set_location(chat_id, float(m.group(1)), float(m.group(2)))
        intent = intents.detect_intent(text)
        return {
            "weather": self.current, "flood": self.risk, "heat": self.risk, "crop": self.crop,
            "subscribe": self.subscribe, "unsubscribe": self.unsubscribe, "help": self.help,
            "greeting": self.start,
        }.get(intent, lambda cid: Reply(t(self.lang(cid), "unknown")))(chat_id)
