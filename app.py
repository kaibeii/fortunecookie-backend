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

# Dedalus (OpenAI-compatible)
# Base URL documented as https://api.dedaluslabs.ai :contentReference[oaicite:4]{index=4}
DEDELUS_API_KEY = os.environ.get("DEDELUS_API_KEY", "")
DEDELUS_BASE_URL = os.environ.get("DEDELUS_BASE_URL", "https://api.dedaluslabs.ai")  # :contentReference[oaicite:5]{index=5}
DEDELUS_MODEL = os.environ.get("DEDELUS_MODEL", "openai/gpt-4o-mini")  # good default for testing

CHAT_COMPLETIONS_URL = f"{DEDELUS_BASE_URL.rstrip('/')}/v1/chat/completions"  # :contentReference[oaicite:6]{index=6}


def clean_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s

def pick_weighted_mood(user_mood: str) -> str:
    if user_mood in MOODS:
        return user_mood
    weighted = ["hopeful"] * 4 + ["cryptic"] * 3 + ["playful"] * 3 + ["grounding"] * 2 + ["bold"] * 2
    return random.choice(weighted)


def generate_fortune_with_dedelus(question: str, mood: str, symbol: str) -> dict:
    if not DEDELUS_API_KEY:
        raise RuntimeError("Missing DEDELUS_API_KEY")

    headers = {
        "Authorization": f"Bearer {DEDELUS_API_KEY}",
        "Content-Type": "application/json",
    }

    system = (
        "You are a digital fortune cookie. "
        "Return a short fortune that is mysterious-but-kind. "
        "No medical/legal/financial instructions. PG-rated. "
        "Return EXACTLY valid JSON."
    )

    user_prompt = f"""
Mood: {mood}
Symbol: {symbol}
User question/thought: {question}

Return EXACT JSON with keys: fortune, suggestion, lucky
Rules:
- fortune: 1–2 sentences, max ~35 words, mysterious-but-kind
- suggestion: 3–10 words, tiny action
- lucky: a color OR number
""".strip()

    payload = {
        "model": DEDELUS_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 180,
        "stream": False
    }

    r = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()

    # OpenAI-compatible: choices[0].message.content :contentReference[oaicite:7]{index=7}
    content = data["choices"][0]["message"]["content"].strip()

    # Expecting JSON string in content
    parsed = json.loads(content)

    fortune_text = str(parsed.get("fortune", "")).strip() or "A small shift today opens a quiet door tomorrow."
    suggestion = str(parsed.get("suggestion", "")).strip() or "Take one slow breath."
    lucky = str(parsed.get("lucky", "")).strip() or "7"

    return {"fortune": fortune_text, "suggestion": suggestion, "lucky": lucky}


def generate_fortune_fallback(question: str, mood: str, symbol: str) -> dict:
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

    # Try Dedalus → fallback
    try:
        out = generate_fortune_with_dedelus(question, mood, symbol)
        out.update({"mood": mood, "symbol": symbol, "source": "dedalus"})
        return jsonify(out)
    except Exception as e:
        fb = generate_fortune_fallback(question, mood, symbol)
        fb.update({
            "mood": mood,
            "symbol": symbol,
            "source": "fallback",
            "warning": "Dedalus call failed; returned fallback fortune.",
            "details": str(e)
        })
        return jsonify(fb), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)