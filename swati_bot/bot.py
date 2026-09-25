"""Telegram front-end for MausamSahayak (Swati).

Run:  TELEGRAM_TOKEN=... API_BASE_URL=http://localhost:8000 python -m swati_bot.bot
Needs: pip install "python-telegram-bot[job-queue]>=21"

STATUS: all conversation logic is in logic.py/formatters.py and is unit-tested. THIS FILE (the
Telegram glue) could not be run in the build environment - test it with a real bot token
(create one with @BotFather) and fix any small API differences for your installed version.
"""
import asyncio
import logging
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from . import alerts as alerts_mod
from . import sms
from .api_client import ApiClient, ApiError
from .i18n import t
from .logic import BotLogic, Reply
from .store import Store

log = logging.getLogger("bot")


def markup_for(reply: Reply, lang: str):
    if reply.ask_location:
        return ReplyKeyboardMarkup([[KeyboardButton(t(lang, "share_location_button"), request_location=True)]],
                                   resize_keyboard=True, one_time_keyboard=True)
    if reply.ask_language:
        return InlineKeyboardMarkup([[InlineKeyboardButton("हिन्दी", callback_data="lang:hi"),
                                      InlineKeyboardButton("English", callback_data="lang:en")]])
    if reply.ask_irrigation:
        return InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "yes"), callback_data="crop:1"),
                                      InlineKeyboardButton(t(lang, "no"), callback_data="crop:0")]])
    return None


def build_app(token, logic: BotLogic, store: Store, api: ApiClient, sender, poll_s=60):
    async def send(update: Update, reply: Reply):
        chat_id = update.effective_chat.id
        await update.effective_chat.send_message(reply.text, reply_markup=markup_for(reply, logic.lang(chat_id)))

    def cmd(fn_name):
        async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            cid = update.effective_chat.id
            await send(update, await asyncio.to_thread(getattr(logic, fn_name), cid))
        return handler

    async def phone(update, context):
        await send(update, logic.set_phone(update.effective_chat.id, " ".join(context.args)))

    async def on_location(update, context):
        loc = update.message.location
        await send(update, await asyncio.to_thread(logic.set_location, update.effective_chat.id, loc.latitude, loc.longitude))

    async def on_text(update, context):
        await send(update, await asyncio.to_thread(logic.handle_text, update.effective_chat.id, update.message.text))

    async def on_button(update, context):
        q = update.callback_query
        await q.answer()
        kind, _, val = q.data.partition(":")
        cid = update.effective_chat.id
        if kind == "lang":
            await send(update, logic.set_language(cid, val))
        elif kind == "crop":
            await send(update, await asyncio.to_thread(logic.crop, cid, val == "1"))

    async def alert_job(context: ContextTypes.DEFAULT_TYPE):
        try:
            if store.get_meta("last_alert_id") is None:              # first run: do not replay history
                existing = await asyncio.to_thread(api.alerts, 0)
                store.set_meta("last_alert_id", max([a["id"] for a in existing], default=0))
                return
            since = int(store.get_meta("last_alert_id", "0"))
            new = await asyncio.to_thread(api.alerts, since)
        except ApiError as e:
            log.warning("alert poll failed: %s", e)
            return
        if not new:
            return
        for n in alerts_mod.plan_notifications(store, new, store.node_names()):
            try:
                await context.bot.send_message(n.chat_id, n.text)
            except Exception:
                log.exception("telegram send failed for %s", n.chat_id)
            if n.sms_to:
                await asyncio.to_thread(sender.send, n.sms_to, n.sms_text)   # SMS fallback for RED
        store.set_meta("last_alert_id", max(a["id"] for a in new))

    app = Application.builder().token(token).build()
    for name, fn in (("start", "start"), ("language", "start"), ("location", "ask_location"), ("now", "current"),
                     ("risk", "risk"), ("crop", "crop"), ("subscribe", "subscribe"), ("unsubscribe", "unsubscribe"),
                     ("help", "help")):
        app.add_handler(CommandHandler(name, cmd(fn)))
    app.add_handler(CommandHandler("phone", phone))
    app.add_handler(MessageHandler(filters.LOCATION, on_location))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.job_queue.run_repeating(alert_job, interval=poll_s, first=10)
    return app


def main():
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    api = ApiClient(os.environ.get("API_BASE_URL", "http://localhost:8000"))
    store = Store(os.environ.get("BOT_DB", "bot.db"))
    logic = BotLogic(api, store)

    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if "--cli" in sys.argv or not token:
        if not token:
            print("\n" + "=" * 65)
            print("ℹ️  TELEGRAM_TOKEN environment variable not set.")
            print("   To connect a live Telegram bot:")
            print("   1. Message @BotFather on Telegram to create a bot & get a token.")
            print("   2. Run: TELEGRAM_TOKEN='your-token' python -m swati_bot.bot")
            print("=" * 65)
            print("Starting interactive Terminal Simulation Mode instead...\n")
        print("MausamSahayak Bot CLI (type '/start', '/now', '/risk', '/crop', or 'exit'):")
        chat_id = 9999
        logic.set_language(chat_id, "en")
        logic.set_location(chat_id, 28.4089, 77.3178)
        while True:
            try:
                line = input("You > ").strip()
                if not line or line.lower() in ("exit", "quit"):
                    break
                if line == "/start":
                    rep = logic.start(chat_id)
                elif line == "/now":
                    rep = logic.current(chat_id)
                elif line == "/risk":
                    rep = logic.risk(chat_id)
                elif line == "/crop":
                    rep = logic.crop(chat_id)
                elif line == "/help":
                    rep = logic.help(chat_id)
                elif line.startswith("/lang"):
                    lang = "hi" if "hi" in line else "en"
                    rep = logic.set_language(chat_id, lang)
                else:
                    rep = logic.handle_text(chat_id, line)
                print(f"\nBot >\n{rep.text}\n")
            except (KeyboardInterrupt, EOFError):
                break
        return

    app = build_app(token, logic, store, api, sms.make_sender_from_env(),
                    int(os.environ.get("ALERT_POLL_S", "60")))
    app.run_polling()


if __name__ == "__main__":
    main()
