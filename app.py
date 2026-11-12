
import os
import sqlite3
from functools import wraps

from flask import (
    Flask, render_template, render_template_string,
    request, jsonify, redirect, url_for, session
)

from dotenv import load_dotenv
from database import create_database

# Optional Gemini integration
try:
    from google import genai
except ImportError:
    genai = None


# ==========================================
# APP CONFIGURATION
# ==========================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "development-secret-change-before-production"
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None

if genai and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as error:
        print("Gemini initialization failed:", error)

create_database()


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    connection = sqlite3.connect("incidents.db")
    connection.row_factory = sqlite3.Row
    return connection


# ==========================================
# ADMIN AUTHENTICATION
# ==========================================

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# AUTOMATIC PRIORITY DETECTION
# ==========================================

def detect_priority(title, description):

    text = (title + " " + description).lower()

    critical_keywords = [
        "server down",
        "system down",
        "network outage",
        "data breach",
        "security attack",
        "all users",
        "production down"
    ]

    low_keywords = [
        "password reset",
        "software update",
        "minor issue",
        "small issue",
        "general query"
    ]

    if any(word in text for word in critical_keywords):
        return "Critical"

    if any(word in text for word in low_keywords):
        return "Low"

    return "Medium"


# ==========================================
# AUTOMATIC CATEGORY PREDICTION
# ==========================================

def predict_category(title, description):

    text = (title + " " + description).lower()

    categories = {
        "Network": [
            "wifi", "wi-fi", "internet",
            "network", "router", "connection"
        ],

        "Hardware": [
            "laptop", "computer", "keyboard",
            "mouse", "printer", "screen",
            "monitor", "battery", "speaker",
            "hardware"
        ],

        "Software": [
            "software", "application", "app",
            "crash", "install", "update",
            "program", "browser"
        ],

        "Login Issue": [
            "password", "login", "sign in",
            "username", "account locked",
            "forgot password"
        ]
    }

    for category, keywords in categories.items():

        if any(word in text for word in keywords):
            return category

    return "Other"


# ==========================================
# SOLUTION SUGGESTION
# ==========================================

def suggest_solution(title, description, category):

    if category == "Network":
        return (
            "Check your Wi-Fi connection, restart your router, "
            "and verify your network settings."
        )

    elif category == "Hardware":
        return (
            "Check hardware connections, restart your device, "
            "and verify whether the hardware is damaged."
        )

    elif category == "Software":
        return (
            "Restart the application, check for updates, "
            "and reinstall the software if necessary."
        )

    elif category == "Login Issue":
        return (
            "Check your username and password. Follow your "
            "organization's password reset process if needed."
        )

    return (
        "Restart the affected system, check the error message, "
        "and contact the IT support team if the issue continues."
    )


# ==========================================
# CHATBOT FALLBACK
# ==========================================

def fallback_it_response(message):

    text = message.lower()

    if any(word in text for word in [
        "wifi", "wi-fi", "internet",
        "network", "connection"
    ]):

        return (
            "Wi-Fi Troubleshooting:\n"
            "1. Check whether Wi-Fi is enabled.\n"
            "2. Restart your router.\n"
            "3. Reconnect to the network.\n"
            "4. Verify network settings.\n"
            "5. Contact IT support if the issue continues."
        )

    elif any(word in text for word in [
        "password", "login", "forgot password", "username"
    ]):

        return (
            "Login Troubleshooting:\n"
            "1. Verify your username.\n"
            "2. Check your password.\n"
            "3. Check Caps Lock.\n"
            "4. Follow your organization's password reset process."
        )

    elif any(word in text for word in [
        "laptop", "computer", "not starting",
        "not turning on"
    ]):

        return (
            "Laptop Troubleshooting:\n"
            "1. Check the power connection.\n"
            "2. Connect the charger.\n"
            "3. Hold the power button for a few seconds.\n"
            "4. Contact hardware support if it still does not start."
        )

    elif any(word in text for word in [
        "slow", "hanging", "performance"
    ]):

        return (
            "Performance Troubleshooting:\n"
            "1. Restart your computer.\n"
            "2. Close unnecessary applications.\n"
            "3. Check available storage.\n"
            "4. Scan for unwanted programs."
        )

    elif any(word in text for word in [
        "printer", "printing"
    ]):

        return (
            "Printer Troubleshooting:\n"
            "1. Check printer power.\n"
            "2. Check cable or Wi-Fi connection.\n"
            "3. Check paper and ink levels.\n"
            "4. Restart the printer."
        )

    elif "keyboard" in text or "mouse" in text:

        return (
            "Check the device connection, reconnect it, "
            "and try another USB port or battery if applicable."
        )

    elif "camera" in text or "webcam" in text:

        return (
            "Check camera permissions, close other applications "
            "using the camera, and restart your device."
        )

    elif "email" in text or "mail" in text:

        return (
            "Check your internet connection, verify your email "
            "credentials, and check your mailbox settings."
        )

    return (
        "Welcome to IT Support! I can help with Wi-Fi, "
        "login, laptop, printer, software, keyboard, "
        "camera and email problems. Please describe your issue."
    )


# ==========================================
# EMPLOYEE DASHBOARD
# ==========================================

@app.route("/")
def index():

    connection = get_db_connection()

    total = connection.execute(
        "SELECT COUNT(*) FROM incidents"
    ).fetchone()[0]

    open_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'Open'"
    ).fetchone()[0]

    in_progress_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'Resolved'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        total=total,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count
    )


# ==========================================
# SUBMIT INCIDENT
# ==========================================

@app.route("/report", methods=["POST"])
def report_incident():

    employee_name = request.form.get(
        "employee_name", ""
    ).strip()

    title = request.form.get(
        "title", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    if not employee_name or not title or not description:
        return "Please fill in all required fields.", 400

    category = predict_category(title, description)

    priority = detect_priority(title, description)

    solution = suggest_solution(title, description, category)

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO incidents
        (employee_name, title, category, description, priority, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        employee_name,
        title,
        category,
        description,
        priority,
        "Open"
    ))

    incident_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Incident Submitted</title>
            <style>
                body {
                    font-family: Arial;
                    background: #eef2f7;
                    padding: 40px;
                }
                .container {
                    background: white;
                    max-width: 550px;
                    margin: auto;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 3px 12px rgba(0,0,0,0.1);
                }
                h2 { color: #263b80; }
                a {
                    display: inline-block;
                    margin: 10px 10px 0 0;
                    padding: 10px 15px;
                    background: #263b80;
                    color: white;
                    text-decoration: none;
                    border-radius: 6px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Incident Submitted Successfully!</h2>
                <p>Incident ID: INC{{ incident_id }}</p>
                <p>Employee: {{ employee_name }}</p>
                <p>Title: {{ title }}</p>
                <p>Category: {{ category }}</p>
                <p>Priority: {{ priority }}</p>
                <p>Status: {{ status }}</p>
                <h3>Suggested Solution</h3>
                <p>{{ solution }}</p>
                <a href="/">Back to Dashboard</a>
            </div>
        </body>
        </html>
    """,
        incident_id=incident_id,
        employee_name=employee_name,
        title=title,
        category=category,
        priority=priority,
        status="Open",
        solution=solution
    )


# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session.clear()
            session["admin_logged_in"] = True

            return redirect(url_for("admin_dashboard"))

        error = "Invalid username or password."

    return render_template(
        "admin_login.html",
        error=error
    )


# ==========================================
# ADMIN DASHBOARD WITH ANALYTICS
# ==========================================

@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():

    connection = get_db_connection()

    # Status statistics
    total = connection.execute(
        "SELECT COUNT(*) FROM incidents"
    ).fetchone()[0]

    open_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'Open'"
    ).fetchone()[0]

    in_progress_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE status = 'Resolved'"
    ).fetchone()[0]

    # Priority statistics
    critical_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE priority = 'Critical'"
    ).fetchone()[0]

    medium_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE priority = 'Medium'"
    ).fetchone()[0]

    low_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE priority = 'Low'"
    ).fetchone()[0]

    # Category statistics
    network_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE category = 'Network'"
    ).fetchone()[0]

    hardware_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE category = 'Hardware'"
    ).fetchone()[0]

    software_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE category = 'Software'"
    ).fetchone()[0]

    login_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE category = 'Login Issue'"
    ).fetchone()[0]

    other_count = connection.execute(
        "SELECT COUNT(*) FROM incidents WHERE category = 'Other'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",

        total=total,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,

        critical_count=critical_count,
        medium_count=medium_count,
        low_count=low_count,

        network_count=network_count,
        hardware_count=hardware_count,
        software_count=software_count,
        login_count=login_count,
        other_count=other_count
    )


# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.route("/admin_logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))


# ==========================================
# VIEW ALL INCIDENTS
# ==========================================

@app.route("/incidents")
@admin_required
def view_incidents():

    connection = get_db_connection()

    incidents = connection.execute(
        "SELECT * FROM incidents ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "incidents.html",
        incidents=incidents
    )


# ==========================================
# UPDATE INCIDENT STATUS
# ==========================================

@app.route("/update_status/<int:incident_id>", methods=["POST"])
@admin_required
def update_status(incident_id):

    status = request.form.get("status")

    allowed_statuses = [
        "Open",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        return "Invalid status.", 400

    connection = get_db_connection()

    connection.execute(
        "UPDATE incidents SET status = ? WHERE id = ?",
        (status, incident_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("view_incidents"))


# ==========================================
# CHATBOT PAGE
# ==========================================

@app.route("/chatbot")
def chatbot():

    return render_template("chatbot.html")


# ==========================================
# CHATBOT API
# ==========================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "reply": "Please enter your IT problem."
        }), 400

    if gemini_client:

        try:

            response = gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=(
                    "You are an IT support assistant. "
                    "Give simple and safe step-by-step troubleshooting "
                    "for common workplace IT issues. Never ask users "
                    "to share passwords or secret credentials.\n\n"
                    + message
                )
            )

            if response.text:
                return jsonify({
                    "reply": response.text
                })

        except Exception as error:
            print("Gemini API unavailable:", error)

    return jsonify({
        "reply": fallback_it_response(message)
    })


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
