from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import mysql.connector
import os

# =========================
# LOAD ENV
# =========================

load_dotenv()

app = Flask(__name__)

# =========================
# OPENROUTER API
# =========================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# =========================
# MYSQL DATABASE
# =========================

def get_db_connection():

    return mysql.connector.connect(
        host="sql8.freesqldatabase.com",
        user="sql8826317",
        password="u6E8wQd2Sf",
        database="sql8826317",
        port=3306
    )

# =========================
# CREATE TABLE
# =========================

try:

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_message TEXT,
        bot_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()

    cursor.close()
    db.close()

    print("Database connected")

except Exception as e:

    print("Database error:", e)

# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    return render_template("index.html")

# =========================
# CHAT API
# =========================

@app.route("/api/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_message = data.get("message", "").strip()

    if user_message == "":

        return jsonify({
            "error": "Message cannot be empty"
        })

    try:

        completion = client.chat.completions.create(

            model="openai/gpt-oss-120b:free",

            messages=[

                {
                    "role": "system",
                    "content": """
You are MindAnchor AI.

You are a warm and emotionally supportive mental health companion.

Your job:
- Listen carefully
- Make users feel heard
- Help reduce stress and anxiety through calm conversation
- Support users struggling with sadness, loneliness, overthinking, anxiety, or emotional pressure

Response style:
- Talk like a caring human friend
- Keep replies short and natural
- Usually 2-5 lines only
- Avoid long essays or too many bullet points
- First comfort the user, then ask one gentle follow-up question
- Occasionally suggest breathing, grounding, journaling, sleep, hydration, or talking to trusted people

Important:
- Never judge
- Never shame
- Never give medical advice
- Never encourage self-harm
- If user mentions suicide or self-harm, encourage contacting a trusted adult or mental health professional immediately

Tone:
Warm, calm, understanding, emotionally safe.
"""
                },

                {
                    "role": "user",
                    "content": user_message
                }

            ]

        )

        reply = completion.choices[0].message.content

        # =========================
        # SAVE CHAT TO MYSQL
        # =========================

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO chats (user_message, bot_reply) VALUES (%s, %s)",
            (user_message, reply)
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "reply": reply
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })

# =========================
# LOAD CHAT HISTORY
# =========================

@app.route("/api/history")
def history():

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT user_message, bot_reply
            FROM chats
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

        cursor.close()
        db.close()

        history = []

        for row in rows:

            history.append({
                "user": row[0],
                "bot": row[1]
            })

        return jsonify(history)

    except Exception as e:

        return jsonify({
            "error": str(e)
        })

# =========================
# CLEAR CHAT HISTORY
# =========================

@app.route("/api/clear", methods=["POST"])
def clear_chat():

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("DELETE FROM chats")

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "message": "Chat history cleared"
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    print("MindAnchor AI running...")
    print("http://127.0.0.1:5000")

    app.run(debug=True)