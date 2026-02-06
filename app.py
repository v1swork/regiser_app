import sqlite3
from unicodedata import category
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.secret_key = "G!Q=f17NBeBU6CEG`i8-e6w{AUN[!rhFLkkRhIt`jg}?:b!{j$\wR2B{q6Q`uy5\`w[v}Q5'RAJx/l+glM[P8Sh37z$M#:>#l3"

logged_in = 0

def get_db_connection(): 
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()

    # таблица пользователи
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        userId INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )""")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS notes(
        noteId INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        category TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (userId))
    """)

    # conn.execute("DELETE FROM users WHERE userId = 2")
    conn.commit()
    conn.close()

# информация о текущем пользователе(контекст для шаблонов)
@app.context_processor
def inject_user():
    return {
        "logged_in": "user_id" in session,
        "current_user": session.get("username")
    }



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if len(username) < 3:
            error = "Имя пользователя должно быть не короче 3 символов"
        elif len(password) < 4:
            error = "Пароль должен быть не короче 4 символов"
        else:
            conn = get_db_connection()
            existing = conn.execute(
                "SELECT userId FROM users WHERE username = ?",
                (username,)
            ).fetchone()

            if existing:
                error = "Пользователь с таким именем уже существует"
                conn.close()
            else:
                password_hash = generate_password_hash(password)
                conn.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, password_hash)
                )
                conn.commit()
                conn.close()
            # здесь сделаем что бы пользователь сразу логинился
            conn = get_db_connection()
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            conn.close()

            session["user_id"] = user["userId"]
            session["username"] = user["username"]

            return redirect("/profile")

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET","POST" ])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user is None:
            error = "Пользователь не найден"
        elif not check_password_hash(user["password_hash"], password):
            error = "Неверный пароль"
        else:
            session["user_id"] = user["userId"] 
            session["username"] = user["username"]
            return redirect("/profile")
    return render_template("login.html", error=error)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    
    username = session.get("username")
    return render_template("profile.html", username=username)

@app.route("/notes")
def notes():
    if "user_id" not in session:
        return redirect("/login")
    
    user_id = session["user_id"]
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    conn = get_db_connection()

    sql = "SELECT * FROM notes WHERE user_id = ?"
    params = [user_id]

    if q:
        sql += "SELECT * FROM notes WHERE user_id = ? AND (title ? OR content LIKE ?)"
        like = f"%q%" #q = кот     like = %кот%
        params.extend([like, like])

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY created_at DESC"

    notes = conn.execute(sql, params).fetchone()

    conn.close()
    return render_template(
        "notes.html",
        notes=notes,
        q=q,
        current_category=category
        )

@app.route("/notes/create", methods=("GET", "POST"))
def create_note():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        category = request.form["title"].strip()
        

        if not title:
            flash("Заголовок не может быть пустым")
        else:
            created_at = datetime.now()
            user_id = session["user_id"]
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO notes (user_id, title, content, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, title, content, category, created_at))
            conn.commit()
            conn.close()
        
        return redirect("/notes")
    
    return render_template("cnotes.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

