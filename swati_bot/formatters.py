"""Turn API JSON into user-facing messages (Swati)."""
from . import i18n
from .i18n import CROP_REASONS, FLOOD_ADVICE, HEAT_ADVICE, LEVEL_EMOJI, LEVEL_NAME, REASONS, SEASON, t


def level_label(lang, level_name):
    return f"{LEVEL_EMOJI[level_name]} {LEVEL_NAME[i18n.norm_lang(lang)][level_name]}"


def reason_text(lang, reason):
    lang = i18n.norm_lang(lang)
    code, params = reason["code"], dict(reason.get("params") or {})
    if code == "sensor_offline" and params.get("minutes") is None:
        code = "sensor_offline_none"
    tpl = REASONS[lang].get(code) or REASONS["en"].get(code)
    if tpl is None:
        return code.replace("_", " ")
    try:
        return tpl.format(**params)
    except (KeyError, IndexError):
        return tpl


def _v(x, unit="", nd=1):
    if x is None:
        return "-"
    return f"{round(x, nd):g}{unit}"


def format_current(lang, risk, node_name, distance_km):
    """`risk` is the /api/nodes/<id>/risk response."""
    reading = risk.get("reading")
    lines = [t(lang, "current_title", name=node_name, km=distance_km)]
    if not reading:
        lines.append(t(lang, "no_data_yet"))
    else:
        m = risk["flood"]["metrics"]
        lines += [f"{t(lang, 'temperature')}: {_v(reading['temperature_c'], ' °C')}",
                  f"{t(lang, 'humidity')}: {_v(reading['humidity_pct'], ' %', 0)}",
                  f"{t(lang, 'rain24')}: {_v(m.get('rain_24h_mm'), ' mm')}",
                  f"{t(lang, 'water')}: {_v(reading['water_level_cm'], ' cm', 0)}",
                  f"{t(lang, 'soil')}: {_v(reading['soil_moisture_pct'], ' %', 0)}"]
        if risk.get("minutes_since_last") is not None:
            lines.append(t(lang, "updated", age=round(risk["minutes_since_last"])))
    if risk["flood"]["stale"]:
        age = risk.get("minutes_since_last")
        lines.append(t(lang, "stale_line", age="?" if age is None else round(age)))
    lines.append("")
    lines.append(t(lang, "flood_line", emoji=LEVEL_EMOJI[risk["flood"]["level_name"]],
                   label=LEVEL_NAME[i18n.norm_lang(lang)][risk["flood"]["level_name"]]))
    if not risk["heat"]["stale"]:
        lines.append(t(lang, "heat_line", emoji=LEVEL_EMOJI[risk["heat"]["level_name"]],
                       label=LEVEL_NAME[i18n.norm_lang(lang)][risk["heat"]["level_name"]]))
    return "\n".join(lines)


def format_risk(lang, risk, node_name, distance_km):
    lang = i18n.norm_lang(lang)
    out = [t(lang, "current_title", name=node_name, km=distance_km), ""]
    for kind, advice in (("flood", FLOOD_ADVICE), ("heat", HEAT_ADVICE)):
        res = risk[kind]
        if kind == "heat" and res["stale"]:
            continue                       # the flood block already says the station is silent
        label = t(lang, f"{kind}_word")
        out.append(f"{label}: {level_label(lang, res['level_name'])}")
        out.append(advice[lang][res["level_name"]])
        if res["reasons"] and res["level_name"] != "GREEN":
            out.append(t(lang, "why"))
            out += [f"• {reason_text(lang, r)}" for r in res["reasons"]]
        out.append("")
    out.append(t(lang, "disclaimer"))
    return "\n".join(out).strip()


def format_crop(lang, advice):
    lang = i18n.norm_lang(lang)
    mode = t(lang, "mode_irrigated" if advice.get("irrigated") else "mode_rainfed")
    out = [t(lang, "crop_title", season=SEASON[lang][advice["season"]], mode=mode), ""]
    recs = advice.get("recommendations") or []
    if not recs:
        out.append(t(lang, "crop_none"))
    for i, r in enumerate(recs, 1):
        name = r["name_hi"] if lang == "hi" else r["name_en"]
        out.append(f"{i}. {name} ({round(r['score'] * 100)}%)")
        for reason in r["reasons"]:
            tpl = CROP_REASONS[lang].get(reason["code"])
            if tpl:
                out.append("   - " + tpl.format(**reason["params"]))
    out += ["", t(lang, "crop_footer")]
    return "\n".join(out)


def format_alert(lang, alert, node_name):
    lang = i18n.norm_lang(lang)
    kind = alert["kind"]
    advice = FLOOD_ADVICE if kind == "flood" else HEAT_ADVICE
    up = alert["level"] > (alert.get("previous_level") or 0)
    head = t(lang, "alert_up" if up else "alert_down", name=node_name)
    out = [f"{LEVEL_EMOJI[alert['level_name']]} {head}",
           f"{t(lang, kind + '_word')}: {level_label(lang, alert['level_name'])}",
           advice[lang][alert["level_name"]]]
    if alert["reasons"] and alert["level_name"] != "GREEN":
        out.append(t(lang, "why"))
        out += [f"• {reason_text(lang, r)}" for r in alert["reasons"][:4]]
    out += ["", t(lang, "disclaimer")]
    return "\n".join(out)


def format_sms(lang, alert, node_name):
    return t(lang, "sms_flood" if alert["kind"] == "flood" else "sms_heat", name=node_name)
