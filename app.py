from flask import Flask, render_template, request, jsonify, redirect, session
from dotenv import load_dotenv
from openai import OpenAI
import mysql.connector
import bcrypt
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mindanchor_secret_123")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

def get_db_connection():
    return mysql.connector.connect(
        host="sql8.freesqldatabase.com",
        user="sql8826317",
        password="u6E8wQd2Sf",
        database="sql8826317",
        port=3306
    )

try:
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
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

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, hashed))
            db.commit()
            cursor.close()
            db.close()
            return redirect("/login")
        except Exception as e:
            return render_template("signup.html", error="Email already exists!")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            cursor.close()
            db.close()
            if user and bcrypt.checkpw(password.encode(), user[3].encode()):
                session["user_id"] = user[0]
                session["user_name"] = user[1]
                return redirect("/")
            else:
                return render_template("login.html", error="Invalid email or password!")
        except Exception as e:
            return render_template("login.html", error=str(e))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/api/chat", methods=["POST"])
def chat():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if user_message == "":
        return jsonify({"error": "Message cannot be empty"})
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are MindAnchor AI. You are a warm and emotionally supportive mental health companion. Listen carefully, make users feel heard, help reduce stress and anxiety. Talk like a caring human friend. Keep replies short and natural, 2-5 lines only. Never judge, never shame, never give medical advice. If user mentions suicide or self-harm, encourage contacting a trusted adult or mental health professional immediately."
                },
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO chats (user_id, user_message, bot_reply) VALUES (%s, %s, %s)",
            (session["user_id"], user_message, reply)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/history")
def history():
    if "user_id" not in session:
        return jsonify([])
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT user_message, bot_reply FROM chats WHERE user_id=%s ORDER BY id ASC", (session["user_id"],))
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify([{"user": r[0], "bot": r[1]} for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/clear", methods=["POST"])
def clear_chat():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"})
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM chats WHERE user_id=%s", (session["user_id"],))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"message": "Cleared"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)