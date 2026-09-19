"""
Smart Student Career Planner  -  TY BSc CS mini-project
Flask + SQLite

HOW THE APP WORKS (short version, handy for viva)
1. A student registers / logs in.
2. The student ticks the skills they already know.
3. For every career we compare "skills the career needs" with "skills the
   student has":
        match % = matched skills / required skills * 100
4. From that we also show:
        - skill gap        -> the skills that are still missing
        - readiness level  -> a friendly label for the % (Just starting ... Ready to apply)
        - next best skill  -> the missing skill that helps the most careers
        - roadmap          -> ordered steps: done skills, what to learn next, a project
"""

import os
import re
import secrets
import sqlite3
from datetime import datetime
from functools import wraps
from urllib.parse import quote_plus

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# Set a real secret in production:  set SECRET_KEY=something-long-and-random
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, "career_planner.db")


# --------------------------------------------------------------------------
# DATA  (edit this section to add careers / skills - nothing else to change)
# --------------------------------------------------------------------------

# Skill -> category. Categories are only used to group the skills page.
CATEGORIES = [
    ("Programming & Tools", "💻"),
    ("Web", "🌐"),
    ("Data & AI", "📊"),
    ("Systems & Security", "🛡️"),
    ("Cloud & DevOps", "☁️"),
]

SKILLS = {
    "Python": "Programming & Tools", "OOP": "Programming & Tools",
    "Git": "Programming & Tools", "Testing": "Programming & Tools",
    "HTML": "Web", "CSS": "Web", "JavaScript": "Web", "Flask": "Web", "APIs": "Web",
    "Excel": "Data & AI", "SQL": "Data & AI", "Statistics": "Data & AI",
    "Pandas": "Data & AI", "Power BI": "Data & AI",
    "Machine Learning": "Data & AI", "Data Visualization": "Data & AI",
    "Networking": "Systems & Security", "Windows": "Systems & Security",
    "Linux": "Systems & Security", "Troubleshooting": "Systems & Security",
    "Cybersecurity": "Systems & Security", "Cryptography": "Systems & Security",
    "Docker": "Cloud & DevOps", "AWS": "Cloud & DevOps", "CI/CD": "Cloud & DevOps",
}

# hue = colour accent (0-360) used by the cards in the UI
CAREERS = {
    "Data Analyst": {
        "short": "Data Analyst", "icon": "📊", "hue": 215,
        "description": "Works with data to find patterns, create reports and support business decisions.",
        "skills": ["Excel", "SQL", "Python", "Statistics", "Pandas", "Power BI"],
        "project": "Analyse a public sales dataset and build a Power BI dashboard with 3 business insights.",
    },
    "Python Developer": {
        "short": "Python Dev", "icon": "🐍", "hue": 145,
        "description": "Builds applications, automation tools and backend systems using Python.",
        "skills": ["Python", "SQL", "Flask", "Git", "OOP", "APIs"],
        "project": "Build a REST API for an expense tracker and publish the code on GitHub.",
    },
    "Web Developer": {
        "short": "Web Dev", "icon": "🌐", "hue": 265,
        "description": "Builds and maintains websites and web applications.",
        "skills": ["HTML", "CSS", "JavaScript", "SQL", "Git", "Flask"],
        "project": "Create a responsive portfolio website with a contact form that saves messages to a database.",
    },
    "IT Support Engineer": {
        "short": "IT Support", "icon": "🖥️", "hue": 30,
        "description": "Helps users solve computer, software, network and system-related problems.",
        "skills": ["Networking", "Windows", "Linux", "Troubleshooting", "SQL", "Python"],
        "project": "Set up a small home lab (a Linux and a Windows VM) and write a Python script that checks if both are reachable.",
    },
    "Cybersecurity Analyst": {
        "short": "Cyber Security", "icon": "🛡️", "hue": 350,
        "description": "Monitors systems and helps identify and respond to security issues.",
        "skills": ["Networking", "Linux", "Cybersecurity", "Python", "SQL", "Cryptography"],
        "project": "Write a Python script that scans a log file for failed logins and flags suspicious IP addresses.",
    },
    "Data Scientist": {
        "short": "Data Scientist", "icon": "🤖", "hue": 290,
        "description": "Uses statistics and machine learning to build models that predict and explain things.",
        "skills": ["Python", "Statistics", "Pandas", "Machine Learning", "SQL", "Data Visualization"],
        "project": "Predict student marks or house prices with a simple regression model and explain the results with charts.",
    },
    "Software Tester (QA)": {
        "short": "QA Tester", "icon": "🧪", "hue": 175,
        "description": "Finds bugs before users do by writing test cases and automating checks.",
        "skills": ["Testing", "SQL", "Git", "Python", "APIs", "Troubleshooting"],
        "project": "Write test cases and automated tests for a small web app, then report the bugs in a clear format.",
    },
    "Cloud & DevOps Engineer": {
        "short": "Cloud / DevOps", "icon": "☁️", "hue": 200,
        "description": "Deploys and runs applications on the cloud and automates how software is shipped.",
        "skills": ["Linux", "Docker", "Git", "AWS", "CI/CD", "Networking"],
        "project": "Containerise a small Flask app with Docker and build it automatically on every Git push.",
    },
}


def slugify(text):
    """'Cloud & DevOps Engineer' -> 'cloud-devops-engineer' (clean URLs)."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


for _name, _data in CAREERS.items():
    _data["slug"] = slugify(_name)
SLUG_TO_NAME = {d["slug"]: n for n, d in CAREERS.items()}


# --------------------------------------------------------------------------
# DATABASE  (one connection per request, closed automatically)
# --------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        course TEXT DEFAULT 'BSc Computer Science',
        year TEXT DEFAULT 'TY'
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS user_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill TEXT NOT NULL,
        UNIQUE(user_id, skill),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()


init_db()  # runs on import, so `flask run` works as well as `python app.py`


# --------------------------------------------------------------------------
# CAREER LOGIC
# --------------------------------------------------------------------------

def readiness(score):
    """Turn a percentage into a friendly label. Returns (index 0-4, label)."""
    if score >= 100:
        return 4, "Ready to apply"
    if score >= 75:
        return 3, "Almost there"
    if score >= 50:
        return 2, "Getting there"
    if score >= 25:
        return 1, "Building basics"
    return 0, "Just starting"


def recommendations(skills):
    """Score every career against the student's skills, best match first."""
    selected = {s.lower() for s in skills}
    results = []
    for name, data in CAREERS.items():
        required = data["skills"]
        matched = [s for s in required if s.lower() in selected]
        missing = [s for s in required if s.lower() not in selected]
        score = round(len(matched) / len(required) * 100)
        level_index, level = readiness(score)
        results.append({
            "name": name, "slug": data["slug"], "short": data["short"],
            "icon": data["icon"], "hue": data["hue"],
            "description": data["description"], "project": data["project"],
            "skills": required, "total": len(required),
            "matched": matched, "missing": missing,
            "score": score, "level": level, "level_index": level_index,
        })
    return sorted(results, key=lambda r: (-r["score"], r["name"]))


def next_skills(skills, recs, limit=3):
    """
    'Learn next' suggestions - one simple rule:
      1. look at the careers the student is CLOSEST to (highest match %),
      2. suggest the skills those careers are still missing,
      3. if two skills tie, prefer the one that also helps more other careers.
    """
    owned = {s.lower() for s in skills}
    board = {}
    for r in recs:                                   # recs is already best-match first
        for skill in r["missing"]:
            if skill.lower() in owned:
                continue
            item = board.setdefault(skill, {"skill": skill, "best": r["score"], "careers": []})
            item["best"] = max(item["best"], r["score"])
            item["careers"].append(r["name"])
    ranked = sorted(board.values(), key=lambda i: (-i["best"], -len(i["careers"]), i["skill"]))
    return ranked[:limit]


def category_coverage(skills):
    """How many skills the student has in each category."""
    owned = set(skills)
    out = []
    for cat, icon in CATEGORIES:
        members = [s for s, c in SKILLS.items() if c == cat]
        have = [s for s in members if s in owned]
        out.append({"name": cat, "icon": icon, "have": len(have), "total": len(members),
                    "pct": round(len(have) / len(members) * 100)})
    return out


def related_careers(name, limit=3):
    """Other careers that share the most skills with this one."""
    mine = set(CAREERS[name]["skills"])
    out = []
    for other, data in CAREERS.items():
        shared = mine & set(data["skills"])
        if other != name and shared:
            out.append({"name": other, "slug": data["slug"], "icon": data["icon"],
                        "hue": data["hue"], "shared": sorted(shared)})
    out.sort(key=lambda o: (-len(o["shared"]), o["name"]))
    return out[:limit]


def get_user_skills(user_id):
    rows = get_db().execute(
        "SELECT skill FROM user_skills WHERE user_id=? ORDER BY skill", (user_id,)
    ).fetchall()
    return [row["skill"] for row in rows]


def greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    return "Good afternoon" if hour < 17 else "Good evening"


@app.template_global()
def learn_url(skill):
    """A YouTube search for the skill - never goes out of date."""
    return "https://www.youtube.com/results?search_query=" + quote_plus(f"{skill} tutorial for beginners")


# --------------------------------------------------------------------------
# LOGIN + CSRF HELPERS
# --------------------------------------------------------------------------

@app.before_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id:
        g.user = get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if g.user is None:            # account no longer exists
            session.pop("user_id", None)


def csrf_token():
    """One random token per session, placed in every form."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        sent = request.form.get("_csrf", "")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# --------------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------------

@app.route("/")
def index():
    if g.user:
        return redirect(url_for("dashboard"))
    return render_template("index.html", career_count=len(CAREERS), skill_count=len(SKILLS))


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        error = None

        if not name or not email or not password:
            error = "Please fill all required fields."
        elif len(name) > 60:
            error = "Name is too long (max 60 characters)."
        elif "@" not in email or "." not in email.split("@")[-1]:
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm:
            error = "Passwords do not match."

        if error:
            flash(error, "error")
            return render_template("register.html", form=request.form)

        db = get_db()
        try:
            cur = db.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                             (name, email, generate_password_hash(password)))
            db.commit()
        except sqlite3.IntegrityError:
            flash("An account with this email already exists.", "error")
            return render_template("register.html", form=request.form)

        session["user_id"] = cur.lastrowid
        flash(f"Welcome, {name.split()[0]}! Pick the skills you already have to get started.", "success")
        return redirect(url_for("skills"))          # onboarding: skills first

    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user["password"], password):
            csrf = session.get("_csrf")
            session.clear()                          # fresh session after login
            session["_csrf"] = csrf or secrets.token_hex(16)
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
        return render_template("login.html", form=request.form)

    return render_template("login.html", form={})


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    skills = get_user_skills(g.user["id"])
    recs = recommendations(skills)
    return render_template(
        "dashboard.html",
        skills=skills,
        recommendations=recs,
        top=recs[0],
        strong_count=sum(1 for r in recs if r["score"] >= 50),
        next_up=next_skills(skills, recs),
        coverage=category_coverage(skills),
        radar=[{"label": r["short"], "score": r["score"]} for r in sorted(recs, key=lambda r: r["name"])],
        greeting=greeting(),
    )


@app.route("/skills", methods=["GET", "POST"])
@login_required
def skills():
    db = get_db()

    if request.method == "POST":
        # only accept skills that really exist in our list
        chosen = sorted({s for s in request.form.getlist("skills") if s in SKILLS})
        db.execute("DELETE FROM user_skills WHERE user_id=?", (g.user["id"],))
        db.executemany("INSERT INTO user_skills (user_id, skill) VALUES (?,?)",
                       [(g.user["id"], s) for s in chosen])
        db.commit()
        flash(f"Skills updated - {len(chosen)} saved.", "success")
        return redirect(url_for("dashboard"))

    groups = [{"name": cat, "icon": icon,
               "skills": sorted(s for s, c in SKILLS.items() if c == cat)}
              for cat, icon in CATEGORIES]
    careers_json = [{"name": n, "icon": d["icon"], "skills": d["skills"]} for n, d in CAREERS.items()]
    return render_template("skills.html", groups=groups,
                           selected=set(get_user_skills(g.user["id"])),
                           careers_json=careers_json)


@app.route("/careers")
@login_required
def careers():
    recs = recommendations(get_user_skills(g.user["id"]))
    return render_template("careers.html", recommendations=recs)


@app.route("/career/<slug>")
@login_required
def career_detail(slug):
    name = SLUG_TO_NAME.get(slug)
    if name is None:
        abort(404)

    recs = recommendations(get_user_skills(g.user["id"]))
    career = next(r for r in recs if r["name"] == name)

    # Roadmap = skills you already have, then skills to learn (first one is "start here")
    steps = [{"skill": s, "state": "done"} for s in career["matched"]]
    steps += [{"skill": s, "state": "current" if i == 0 else "todo"}
              for i, s in enumerate(career["missing"])]

    return render_template("career_detail.html", career=career, steps=steps,
                           related=related_careers(name))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        course = request.form.get("course", "").strip()[:60]
        year = request.form.get("year", "").strip()

        if not name:
            flash("Name cannot be empty.", "error")
            return redirect(url_for("profile"))
        if year not in ("FY", "SY", "TY"):
            year = "TY"

        db = get_db()
        db.execute("UPDATE users SET name=?, course=?, year=? WHERE id=?",
                   (name[:60], course, year, g.user["id"]))
        db.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    skills_list = get_user_skills(g.user["id"])
    recs = recommendations(skills_list)
    return render_template("profile.html", skill_count=len(skills_list), top=recs[0])


# --------------------------------------------------------------------------
# ERROR PAGES
# --------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, title="Page not found",
                           message="The page you are looking for doesn't exist or was moved."), 404


@app.errorhandler(400)
def bad_request(_e):
    return render_template("error.html", code=400, title="That form has expired",
                           message="For your safety the form session timed out. Go back, refresh the page and try again."), 400


if __name__ == "__main__":
    app.run(debug=True)
