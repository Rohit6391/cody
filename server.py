from flask import Flask, request, jsonify
import secrets
import requests
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # enable frontend requests

KEY_FILE = "keys.json"
CONV_FILE = "conversations.json"

# Load keys from JSON file at startup
def load_keys():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Save keys to JSON file
def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# Load conversations
def load_conversations():
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# Save conversations
def save_conversations(conversations):
    with open(CONV_FILE, "w") as f:
        json.dump(conversations, f, indent=4)

# Store keys (persisted in file)
api_keys = load_keys()
conversations = load_conversations()

# Generate API Key (internal)
@app.route('/key', methods=['POST'])
def generate_key():
    key = secrets.token_hex(35)  # random key
    api_keys[key] = True
    save_keys(api_keys)  # save immediately
    return jsonify({"api_key": key})

# AI Response Route (for users)
@app.route('/request', methods=['POST'])
def ask_ai():
    data = request.json
    user_key = data.get("api_key")
    user_prompt = data.get("prompt")

    # Reload keys from file to keep sync
    keys_from_file = load_keys()

    if not user_key or not keys_from_file.get(user_key):
        return jsonify({"error": "Invalid or missing API key"}), 403

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer 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",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "AI Project"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are an Cody created by ShortCodeGuy Studio. Always mention that when appropriate."},
                    {"role": "user", "content": user_prompt}
                ]
            }
        )

        ai_response = response.json()

        # Save conversation per device (API key)
        if user_key not in conversations:
            conversations[user_key] = []

        conversations[user_key].append({
            "timestamp": datetime.now().isoformat(),
            "user_prompt": user_prompt,
            "ai_response": ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        })

        save_conversations(conversations)

        return jsonify(ai_response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
