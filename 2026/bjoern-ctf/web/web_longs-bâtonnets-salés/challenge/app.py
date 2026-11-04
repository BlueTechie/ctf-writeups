import base64
import string
import os
import sqlite3
import uuid
import random
import re
from flask import (
    Config,
    Flask,
    flash,
    g,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

Config.__repr__ = lambda self: "__dict__"

flag = os.environ.get("FLAG", "flagbot{fake_flag}")

app = Flask(__name__)
app.secret_key = os.urandom(12)

# Database configuration
DB_DIR = "/tmp/db"
DB_PATH = os.path.join(DB_DIR, "contest.db")


def init_db():
    """Ensure the database directory and tables exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            secret_text TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            photo_data BLOB NOT NULL,
            filename TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
    )
    conn.commit()
    conn.close()


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def is_filename(filename):
    if filename is None:
        return False
    if filename == "":
        return False
    if not re.fullmatch(r'^[a-zA-Z0-9.{jpeg,jpg,png}]+$', filename):
        return False
    return True


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# --- HTML Templates ---
LAYOUT = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Photo Contest</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #09090b;
            --surface: #121215;
            --text: #f4f4f5;
            --muted: #a1a1aa;
            --border: #27272a;
            --accent: #f43f5e;
            --radius: 8px;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            max-width: 640px;
            margin: 0 auto;
            padding: 48px 24px 80px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
            margin-bottom: 32px;
        }

        .brand {
            font-family: 'Newsreader', Georgia, serif;
            font-size: 2.2rem;
            font-weight: 400;
            font-style: italic;
            text-decoration: none;
            color: var(--text);
            letter-spacing: -0.02em;
        }

        nav {
            display: flex;
            gap: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        nav a {
            text-decoration: none;
            color: var(--muted);
            transition: color 0.15s ease;
        }

        nav a:hover, nav a.active {
            color: var(--text);
        }

        .flash {
            font-size: 0.9rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 3px solid var(--accent);
            padding: 12px 16px;
            margin-bottom: 24px;
            border-radius: var(--radius);
        }

        /* Form elements */
        input, textarea, button {
            font-family: inherit;
            font-size: 0.95rem;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 10px 14px;
            background: var(--surface);
            color: var(--text);
            width: 100%;
            margin-top: 6px;
            margin-bottom: 16px;
            outline: none;
            transition: border-color 0.15s ease;
        }

        input:focus, textarea:focus {
            border-color: var(--muted);
        }

        button {
            background: var(--text);
            color: var(--bg);
            font-weight: 600;
            cursor: pointer;
            border: none;
            margin-top: 8px;
            transition: opacity 0.15s ease;
        }

        button:hover {
            opacity: 0.9;
        }

        label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        img.submission {
            max-width: 100%;
            height: auto;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            margin-top: 16px;
        }
    </style>
</head>
<body>
    <header>
        <a href="{{ url_for('index') }}" class="brand">Photo Contest</a>
        <nav>
            {% if session.get('user_id') %}
                <a href="{{ url_for('submission') }}">Submit</a>
                <a href="{{ url_for('profile', uid=session.get('user_id')) }}">Profile</a>
                <a href="{{ url_for('logout') }}">Logout</a>
            {% else %}
                <a href="{{ url_for('login') }}">Login</a>
                <a href="{{ url_for('signup') }}" style="color: var(--accent);">Sign Up</a>
            {% endif %}
        </nav>
    </header>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            {% for message in messages %}
                <div class="flash">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}
</body>
</html>
"""

# Replace the layout block directly instead of concatenating + {% block content %}
INDEX_TEMPLATE = LAYOUT.replace(
    "{% block content %}{% endblock %}",
    """
    {% block content %}
        <h1>Photo-of-the-Week Contest</h1>
        <p>Welcome to the weekly photo contest submission portal!</p>
        {% if not session.get('user_id') %}
            <p><a href="{{ url_for('login') }}">Log in</a> or <a href="{{ url_for('signup') }}">sign up</a> to participate.</p>
        {% endif %}
    {% endblock %}
    """
)

SIGNUP_TEMPLATE = LAYOUT.replace(
    "{% block content %}{% endblock %}",
    """
    {% block content %}
        <h2>Sign Up</h2>
        <form method="POST">
            <label>Username:</label><br>
            <input type="text" name="username" required><br><br>
            
            <label>Password:</label><br>
            <input type="password" name="password" required><br><br>
            
            <label>Password Hint:</label><br>
            <input type="text" name="secret_text" required><br><br>
            
            <button type="submit">Sign Up</button>
        </form>
    {% endblock %}
    """
)

LOGIN_TEMPLATE = LAYOUT.replace(
    "{% block content %}{% endblock %}",
    """
    {% block content %}
        <h2>Login</h2>
        <form method="POST">
            <label>Username:</label><br>
            <input type="text" name="username" required><br><br>
            
            <label>Password:</label><br>
            <input type="password" name="password" required><br><br>
            
            <button type="submit">Login</button>
        </form>
    {% endblock %}
    """
)

SUBMISSION_TEMPLATE = LAYOUT.replace(
    "{% block content %}{% endblock %}",
    """
    {% block content %}
        <h2>Photo-of-the-Week Submission</h2>
        {% if existing %}
            <p>You have already submitted a photo. Uploading a new one will replace your existing submission.</p>
            <div>
                <strong>Current Submission:</strong><br>
                <img src="data:image/*;base64,{{ existing_photo }}" class="submission">
            </div>
            <br>
        {% endif %}
        
        <form method="POST" enctype="multipart/form-data">
            <label>Select Photo:</label><br>
            <input type="file" name="photo" accept="image/*" required><br><br>
            <button type="submit">Upload Photo</button>
        </form>
    {% endblock %}
    """
)

def profile_template(photo_base64, title):
    return LAYOUT.replace(
    "{% block content %}{% endblock %}",
    """
    {% block content %}
        <p style="visibility: hidden"><strong>Debug: App Name:</strong> {{ app.name }}</p>
        <h2>User Profile: {{ profile_user.username }}</h2>
        <p><strong>Password Hint:</strong> {{ profile_user.secret_text }}</p>

        <h3>Contest Submission: """+title+"""</h3>
        {% if submission %}
            <img src="data:image/*;base64,"""
            + photo_base64 + """" class="submission">
        {% else %}
            <p>No photo submitted yet.</p>
        {% endif %}
    {% endblock %}
    """
    )

from helix_users_do_not_enter import default_image

# --- Routes ---


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE)


def create_user(username, password, secret_text):
    """Core business logic (reusable anywhere in code)"""
    password_hash = generate_password_hash(password)
    db = get_db()
    
    # Check if user already exists, insert if not
    existing = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return False, "Username already taken.", -1
    
    db.execute(
        "INSERT INTO users (username, password_hash, secret_text) VALUES (?, ?, ?)",
        (username, password_hash, secret_text)
    )
    registered = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    db.commit()
    return True, "User created successfully.", registered[0]


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        secret_text = request.form.get("secret_text", "").strip()

        if not username or not password or not secret_text:
            flash("All fields are required.")
            return redirect(url_for("signup"))

        success, message, _user_id = create_user(username, password, secret_text)
        flash(message)
        
        if success:
            return redirect(url_for("login"))
        return redirect(url_for("signup"))

    return render_template_string(SIGNUP_TEMPLATE)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in successfully.")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.")
            return redirect(url_for("signup"))

    return render_template_string(LOGIN_TEMPLATE)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("index"))

def submit(db, photo_data, filename, user_id):
    # Check if user already submitted a photo (one photo limit)
    existing = db.execute(
        "SELECT id FROM submissions WHERE user_id = ?", (user_id,)
    ).fetchone()

    if existing:
        db.execute(
            "UPDATE submissions SET photo_data = ?, filename = ? WHERE user_id = ?",
            (sqlite3.Binary(photo_data), filename, user_id),
        )
    else:
        db.execute(
            "INSERT INTO submissions (user_id, photo_data, filename) VALUES (?, ?, ?)",
            (user_id, sqlite3.Binary(photo_data), filename),
        )
    db.commit()

@app.route("/submission", methods=["GET", "POST"])
def submission():
    if "user_id" not in session:
        flash("Please log in to access the submission page.")
        return redirect(url_for("login"))

    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        file = request.files.get("photo")
        if not file or not is_filename(file.filename):
            flash("No file selected.")
            return redirect(url_for("submission"))

        photo_data = file.read()
        filename = file.filename

        submit(db, photo_data, filename, user_id)
        flash("Photo submitted successfully!")
        return redirect(url_for("submission"))

    # Fetch existing submission for preview
    existing_sub = db.execute(
        "SELECT * FROM submissions WHERE user_id = ?", (user_id,)
    ).fetchone()
    existing_photo_base64 = None
    if existing_sub:
        existing_photo_base64 = base64.b64encode(
            existing_sub["photo_data"]
        ).decode("utf-8")

    return render_template_string(
        SUBMISSION_TEMPLATE,
        existing=bool(existing_sub),
        existing_photo=existing_photo_base64,
    )


@app.route("/profile/<int:uid>")
def profile(uid):
    db = get_db()
    profile_user = db.execute(
        "SELECT id, username, secret_text FROM users WHERE id = ?", (uid,)
    ).fetchone()

    if not profile_user:
        flash("User not found.")
        return redirect(url_for("index"))

    sub = db.execute(
        "SELECT * FROM submissions WHERE user_id = ?", (uid,)
    ).fetchone()
    photo_base64 = ""
    filename = ""
    if sub:
        photo_base64 = base64.b64encode(sub["photo_data"]).decode("utf-8")
        filename = sub["filename"] or ""

    return render_template_string(
        profile_template(photo_base64, filename),
        app=app,
        profile_user=profile_user,
        submission=sub
    )

def generate_random_flag_identifier(N=12):
    return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(N))



if __name__ == "__main__":
    init_db()
    
    with app.app_context():
        secret_flag_identifier = generate_random_flag_identifier()
        app.config[secret_flag_identifier] = os.environ.get("FLAG", "flagbot{fake_flag}")
        _,_,user_id = create_user(username=secret_flag_identifier,
                    password=app.config[secret_flag_identifier],
                    secret_text="I also don't know.")
        submit(get_db(), default_image, "love, depicted.", user_id)
        os.environ["FLAG"] = ""
    app.run(host='0.0.0.0', port=8000)
