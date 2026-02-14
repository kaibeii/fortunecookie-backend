import os
import re
import random
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MOODS = ["hopeful", "cryptic", "playful", "grounding", "bold"]
SYMBOLS = [
    "Key", "Mirror", "Lantern", "Coin", "Feather", "Compass", "Shell",
    "Seed", "Thread", "Candle", "Door", "Bridge", "Cup", "Stone"
]

# ---- If you have Dedelus API details, set these on Render as env vars ----
DEDELUS_API_KEY = os.environ.get("DEDELUS_API_KEY", "")
DEDELUS_API_URL = os.environ.get("DEDELUS_API_URL", "")  # e.g. https://api.dedelus.ai/v1/...
DEDELUS_MODEL = os.environ.get("DEDELUS_MODEL", "")      # optional

# ---- Simple backend logic: input validation + controlled randomness ----
def clean_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def pick_weighted_mood(user_mood: str) -> str:
    if user_mood in MOODS:
        return user_mood
    # weighted pick: hopeful a bit more common
    weighted = ["hopeful"] * 4 + ["cryptic"] * 3 + ["playful"] * 3 + ["grounding"] * 2 + ["bold"] * 2
    return random.choice(weighted)

# ---- Fortune generation: tries Dedelus, falls back to local templates ----
def generate_fortune_with_dedelus(question: str, mood: str, symbol: str) -> dict:
    """
    NOTE: This function is a template because Dedelus API details can vary.
    You will likely only need to change:
    - headers auth format
    - payload shape
    - response parsing
    """
    if not (DEDELUS_API_KEY and DEDELUS_API_URL):
        raise RuntimeError("Missing DEDELUS_API_KEY or DEDELUS_API_URL")

    headers = {
        # Common patterns: "Authorization": f"Bearer {DEDELUS_API_KEY}"
        # If Dedelus uses something else, swap here.
        "Authorization": f"Bearer {DEDELUS_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a digital fortune cookie.
Mood: {mood}
Symbol: {symbol}
User question/thought: {question}

Return EXACT JSON with keys: fortune, suggestion, lucky
Rules:
- fortune: 1–2 sentences, max ~35 words, mysterious-but-kind
- suggestion: 3–10 words, tiny action
- lucky: a color OR number
No medical/legal/financial instructions. PG.
""".strip()

    # Common payload patterns (edit to match Dedelus):
    payload = {
        "model": DEDELUS_MODEL or "default",
        "input": prompt,
        "max_tokens": 120
    }

    r = requests.post(DEDELUS_API_URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    # Common response patterns: data["output"] or data["text"] or data["choices"][0]["text"]
    # Try a few likely ones:
    raw = None
    if isinstance(data, dict):
        raw = (
            data.get("output")
            or data.get("text")
            or (data.get("choices", [{}])[0].get("text") if isinstance(data.get("choices"), list) else None)
        )

    if not raw or not isinstance(raw, str):
        raise RuntimeError("Could not parse Dedelus response text")

    raw = raw.strip()
    parsed = json.loads(raw)  # must be JSON per our prompt

    return {
        "fortune": str(parsed.get("fortune", "")).strip() or "A small shift today opens a quiet door tomorrow.",
        "suggestion": str(parsed.get("suggestion", "")).strip() or "Take one slow breath.",
        "lucky": str(parsed.get("lucky", "")).strip() or "7",
    }

def generate_fortune_fallback(question: str, mood: str, symbol: str) -> dict:
    # Safe, deterministic-ish templates (so the app still works without Dedelus configured)
    fortunes = {
        "hopeful": [
            "Something light is gathering behind the scenes—stay open to it.",
            "A small decision today makes tomorrow feel easier.",
        ],
        "cryptic": [
            "The answer arrives sideways. Notice what repeats.",
            "What you’re seeking is near, but not where you’ve been looking.",
        ],
        "playful": [
            "Your future self is already laughing about this. Keep going.",
            "Plot twist: you’re closer than you think.",
        ],
        "grounding": [
            "Return to what’s simple. You don’t need to rush this.",
            "One calm step is still progress. Take it.",
        ],
        "bold": [
            "Choose the option that scares you a little—in a good way.",
            "Say it plainly. Clarity is your power today.",
        ],
    }
    suggestion_bank = [
        "Drink a glass of water.",
        "Write one honest sentence.",
        "Clean one small corner.",
        "Text one supportive person.",
        "Step outside for 60 seconds.",
        "Do the next tiny task.",
    ]
    lucky_bank = ["7", "11", "blue", "green", "13", "gold", "2"]

    fortune = random.choice(fortunes.get(mood, fortunes["hopeful"]))
    suggestion = random.choice(suggestion_bank)
    lucky = random.choice(lucky_bank)

    # Tiny personalization without AI:
    if question.endswith("?") and mood == "cryptic":
        fortune = fortune + " The question is part of the answer."

    return {"fortune": fortune, "suggestion": suggestion, "lucky": lucky}


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/fortune")
def api_fortune():
    data = request.get_json(silent=True) or {}
    question = clean_text(data.get("question", ""))
    mood_in = clean_text(data.get("mood", ""))

    if not question:
        return jsonify({"error": "Please enter a question or thought."}), 400
    if len(question) > 400:
        return jsonify({"error": "Keep it under 400 characters."}), 400

    mood = pick_weighted_mood(mood_in)
    symbol = random.choice(SYMBOLS)

    # Try Dedelus → fallback if not configured or errors
    try:
        if DEDELUS_API_KEY and DEDELUS_API_URL:
            out = generate_fortune_with_dedelus(question, mood, symbol)
            out.update({"mood": mood, "symbol": symbol, "source": "dedelus"})
            return jsonify(out)
    except Exception as e:
        # Still return something usable; include details for debugging
        fallback = generate_fortune_fallback(question, mood, symbol)
        fallback.update({
            "mood": mood,
            "symbol": symbol,
            "source": "fallback",
            "warning": "Dedelus call failed; returned fallback fortune.",
            "details": str(e)
        })
        return jsonify(fallback), 200

    fallback = generate_fortune_fallback(question, mood, symbol)
    fallback.update({"mood": mood, "symbol": symbol, "source": "fallback"})
    return jsonify(fallback)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)