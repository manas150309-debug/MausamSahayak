"""Bounded AI explanation layer; never used to calculate risk levels."""
from __future__ import annotations

import json

import requests


SYSTEM_INSTRUCTIONS = (
    "You explain an educational weather-monitoring dashboard. Use only the supplied JSON. "
    "Never change the risk level, invent measurements, issue evacuation orders, or claim official authority. "
    "Answer in simple Hindi when language=hi, otherwise concise English. Mention that IMD/CWC/NDMA and local "
    "authorities override this prototype. Maximum 120 words."
)


def verified_fallback(assessment: dict, language: str = "en") -> str:
    flood = assessment.get("flood") or {}
    level = flood.get("level_name", "UNKNOWN")
    codes = [str(r.get("code", "signal")).replace("_", " ") for r in flood.get("reasons", [])]
    reason = ", ".join(codes) if codes else "no active warning threshold"
    if language == "hi":
        return f"स्थिति {level} है। मुख्य सत्यापित कारण: {reason}। स्थानीय प्रशासन और आधिकारिक मौसम चेतावनियों को प्राथमिकता दें।"
    return f"Status is {level}. Verified trigger reasons: {reason}. Prioritise official weather alerts and local authority guidance."


def _gemini_explanation(assessment: dict, question: str, language: str, api_key: str, model: str) -> dict:
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
        json={
            "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTIONS}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps({
                "language": language,
                "question": question[:300],
                "assessment": assessment,
            }, default=str)}]}],
            "generationConfig": {
                "maxOutputTokens": 220,
                "temperature": 0.2,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        timeout=18,
    )
    response.raise_for_status()
    payload = response.json()
    text = "".join(
        part.get("text", "")
        for candidate in payload.get("candidates", [])[:1]
        for part in candidate.get("content", {}).get("parts", [])
    ).strip()
    if not text:
        raise ValueError("Gemini returned no text")
    return {"mode": "gemini", "model": model, "text": text}


def explain_assessment(assessment: dict, question: str, language: str, api_key: str, model: str,
                       gemini_api_key: str = "", gemini_model: str = "gemini-2.5-flash") -> dict:
    if gemini_api_key:
        try:
            return _gemini_explanation(assessment, question, language, gemini_api_key, gemini_model)
        except Exception:
            pass
    if not api_key:
        return {"mode": "verified_fallback", "text": verified_fallback(assessment, language)}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            reasoning={"effort": "none"},
            instructions=SYSTEM_INSTRUCTIONS,
            input=json.dumps({"language": language, "question": question[:300], "assessment": assessment}, default=str),
            max_output_tokens=220,
        )
        return {"mode": "openai", "model": model, "text": response.output_text.strip()}
    except Exception:
        return {"mode": "verified_fallback", "text": verified_fallback(assessment, language)}
