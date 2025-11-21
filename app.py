from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types  # for config if needed
import logging

# Load .env
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect("queries.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        user_question = data.get("question")
        logger.debug(f"User: {user_question}")

        # Use the correct method for v1.x of google-genai
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=user_question,
            # optionally, you could configure generation like:
            # config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=512)
        )

        ai_answer = response.text
        logger.debug(f"AI: {ai_answer}")

        # Save to DB
        conn = sqlite3.connect("queries.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO queries (question, answer) VALUES (?, ?)",
                       (user_question, ai_answer))
        conn.commit()
        conn.close()

        return jsonify({"answer": ai_answer})

    except Exception as e:
        logger.exception("Error generating response")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Flask app …")
    app.run(debug=True, port=5000)
