"""Keyword intent detection for English, Hindi and Hinglish (Swati)."""
import re

KEYWORDS = {
    "crop": ["crop", "crops", "sow", "grow", "plant", "farming", "fasal", "fasl", "kheti", "फसल", "फ़सल", "खेती", "बुवाई", "बोना"],
    "flood": ["flood", "baadh", "badh", "bāṛh", "बाढ़", "बाढ", "बाढ़", "river", "water level", "nadi", "नदी", "जलस्तर", "पानी बढ़", "evacuat", "relocat"],
    "heat": ["heat", "hot", "garmi", "loo", "गर्मी", "लू", "heatwave", "heat wave"],
    "weather": ["weather", "temperature", "temp", "humidity", "rain", "mausam", "barish", "baarish", "tapman",
                "मौसम", "तापमान", "बारिश", "बरसात", "नमी", "बारिश"],
    "subscribe": ["subscribe", "alert me", "notify", "अलर्ट चालू", "सूचना चालू"],
    "unsubscribe": ["unsubscribe", "stop alerts", "अलर्ट बंद", "सूचना बंद"],
    "help": ["help", "menu", "मदद", "सहायता", "madad"],
    "greeting": ["hi", "hello", "hey", "namaste", "namaskar", "नमस्ते", "नमस्कार"],
}
ORDER = ["unsubscribe", "subscribe", "crop", "flood", "heat", "weather", "help", "greeting"]


def detect_intent(text: str):
    s = (text or "").lower().strip()
    if not s:
        return None
    words = set(re.findall(r"[\w\u0900-\u097F]+", s))
    for intent in ORDER:
        for kw in KEYWORDS[intent]:
            kw = kw.lower()
            if " " in kw or len(kw) > 3:
                if kw in s:
                    return intent
            elif kw in words:
                return intent
    return None
