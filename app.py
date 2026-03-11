from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leads.db"

app = Flask(__name__)

SUCCESS_MESSAGE = (
    "Thank you for contacting Osa Golf Course.\n\n"
    "We have received your request and will send you detailed information about available lots, pricing, "
    "and opportunities at the project shortly.\n\n"
    "Our team will contact you soon to answer your questions and help you explore the possibilities of owning "
    "property in this unique golf community in Costa Rica.\n\n"
    "We appreciate your interest.\n\n"
    "Best regards,\n"
    "Osa Golf Course Team"
)

WELCOME_EMAIL_SUBJECT = "Information about Osa Golf Course – Costa Rica"
WELCOME_EMAIL_BODY = (
    "Hello,\n\n"
    "Thank you for your interest in Osa Golf Course.\n\n"
    "Our project offers residential lots inside a peaceful golf community located in the beautiful South Pacific region "
    "of Costa Rica. It is an ideal place for nature lovers, golf enthusiasts, retirement living, or investment opportunities.\n\n"
    "We will be happy to share with you:\n"
    "- Available lots and pricing\n"
    "- Project information and location\n"
    "- Golf course details\n"
    "- Investment opportunities\n"
    "- Visit arrangements\n\n"
    "If you have any questions or would like to schedule a call or visit, please feel free to reply to this email.\n\n"
    "We look forward to helping you discover Osa Golf Course.\n\n"
    "Best regards,\n"
    "Osa Golf Course Team"
)

INTEREST_OPTIONS = [
    "Residential Lot Purchase",
    "Golf Membership",
    "Property Investment",
    "Schedule a Visit",
]


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def classify_lead_status(budget: float) -> str:
    if budget >= 120000:
        return "Hot Lead"
    if 80000 <= budget <= 119999:
        return "Warm Lead"
    return "Cold Lead"


def init_db() -> None:
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            country TEXT NOT NULL,
            budget REAL NOT NULL,
            interest_type TEXT NOT NULL,
            preferred_lot_or_area TEXT,
            message TEXT,
            lead_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS outbound_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            recipient_email TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads (id)
        )
        """
    )

    conn.commit()
    conn.close()


def seed_data() -> None:
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]
    if total == 0:
        sample = [
            ("Michael Turner", "michael@example.com", "+1 305 555 1987", "USA", 160000, "Residential Lot Purchase", "Ocean View Ridge", "Interested in premium lots.", classify_lead_status(160000)),
            ("Andrea Lopez", "andrea@example.com", "+506 8888 1000", "Costa Rica", 92000, "Schedule a Visit", "Clubhouse Area", "Looking for a private tour.", classify_lead_status(92000)),
            ("Sven Meyer", "sven@example.com", "+49 1512 990000", "Germany", 65000, "Golf Membership", "", "Please send membership details.", classify_lead_status(65000)),
        ]
        conn.executemany(
            """
            INSERT INTO leads (
                full_name, email, phone, country, budget, interest_type,
                preferred_lot_or_area, message, lead_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            sample,
        )
        conn.commit()
    conn.close()


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.route("/admin")
def admin() -> str:
    return render_template("admin.html")


@app.route("/api/health")
def health() -> Any:
    return jsonify({"status": "ok"})


@app.route("/api/welcome-template")
def welcome_template() -> Any:
    return jsonify({"subject": WELCOME_EMAIL_SUBJECT, "body": WELCOME_EMAIL_BODY})


@app.route("/api/leads", methods=["POST"])
def create_lead() -> Any:
    data = request.get_json(silent=True) or {}
    required = ["full_name", "email", "phone", "country", "budget", "interest_type"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        budget = float(data["budget"])
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Estimated budget must be a valid number."}), 400

    if data["interest_type"] not in INTEREST_OPTIONS:
        return jsonify({"success": False, "message": "Invalid interest type selected."}), 400

    lead_status = classify_lead_status(budget)

    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO leads (
            full_name, email, phone, country, budget, interest_type,
            preferred_lot_or_area, message, lead_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("full_name", "").strip(),
            data.get("email", "").strip(),
            data.get("phone", "").strip(),
            data.get("country", "").strip(),
            budget,
            data.get("interest_type", "").strip(),
            data.get("preferred_lot_or_area", "").strip(),
            data.get("message", "").strip(),
            lead_status,
        ),
    )
    lead_id = cursor.lastrowid

    conn.execute(
        """
        INSERT INTO outbound_emails (lead_id, recipient_email, subject, body, status)
        VALUES (?, ?, ?, ?, 'queued')
        """,
        (lead_id, data.get("email", "").strip(), WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY),
    )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "message": SUCCESS_MESSAGE,
            "lead_status": lead_status,
        }
    )


@app.route("/api/leads", methods=["GET"])
def list_leads() -> Any:
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    filters = []
    params: list[Any] = []

    if q:
        filters.append("(full_name LIKE ? OR email LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    if status:
        filters.append("lead_status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    sql = f"""
        SELECT id, full_name, email, phone, country, budget, interest_type,
               preferred_lot_or_area, message, lead_status, created_at
        FROM leads
        {where}
        ORDER BY datetime(created_at) DESC
    """

    conn = get_db_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    leads = [dict(row) for row in rows]
    return jsonify({"leads": leads})


if __name__ == "__main__":
    init_db()
    seed_data()
    app.run(debug=True)
else:
    init_db()
    seed_data()
