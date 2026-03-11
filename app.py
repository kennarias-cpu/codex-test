from __future__ import annotations

import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leads.db"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

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

INTEREST_OPTIONS = {
    "Residential Lot Purchase",
    "Golf Membership",
    "Property Investment",
    "Schedule a Visit",
}


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
            (
                "Michael Turner",
                "michael@example.com",
                "+1 305 555 1987",
                "USA",
                160000,
                "Residential Lot Purchase",
                "Ocean View Ridge",
                "Interested in premium lots.",
                classify_lead_status(160000),
            ),
            (
                "Andrea Lopez",
                "andrea@example.com",
                "+506 8888 1000",
                "Costa Rica",
                92000,
                "Schedule a Visit",
                "Clubhouse Area",
                "Looking for a private tour.",
                classify_lead_status(92000),
            ),
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


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/admin":
            self._send_file(TEMPLATES_DIR / "admin.html", "text/html; charset=utf-8")
            return
        if path == "/api/health":
            json_response(self, HTTPStatus.OK, {"status": "ok"})
            return
        if path == "/api/welcome-template":
            json_response(self, HTTPStatus.OK, {"subject": WELCOME_EMAIL_SUBJECT, "body": WELCOME_EMAIL_BODY})
            return
        if path == "/api/leads":
            self._handle_list_leads(parsed.query)
            return
        if path.startswith("/static/"):
            fp = STATIC_DIR / path.removeprefix("/static/")
            if fp.exists() and fp.is_file():
                content_type = "text/plain"
                if fp.suffix == ".css":
                    content_type = "text/css"
                elif fp.suffix == ".js":
                    content_type = "application/javascript"
                self._send_file(fp, content_type)
                return

        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/leads":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            json_response(self, HTTPStatus.BAD_REQUEST, {"success": False, "message": "Invalid JSON body."})
            return

        required = ["full_name", "email", "phone", "country", "budget", "interest_type"]
        missing = [f for f in required if not str(data.get(f, "")).strip()]
        if missing:
            json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {"success": False, "message": f"Missing required fields: {', '.join(missing)}"},
            )
            return

        try:
            budget = float(data["budget"])
        except (TypeError, ValueError):
            json_response(self, HTTPStatus.BAD_REQUEST, {"success": False, "message": "Estimated budget must be a valid number."})
            return

        interest = str(data.get("interest_type", "")).strip()
        if interest not in INTEREST_OPTIONS:
            json_response(self, HTTPStatus.BAD_REQUEST, {"success": False, "message": "Invalid interest type selected."})
            return

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
                interest,
                data.get("preferred_lot_or_area", "").strip(),
                data.get("message", "").strip(),
                lead_status,
            ),
        )
        lead_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO outbound_emails (lead_id, recipient_email, subject, body, status) VALUES (?, ?, ?, ?, 'queued')",
            (lead_id, data.get("email", "").strip(), WELCOME_EMAIL_SUBJECT, WELCOME_EMAIL_BODY),
        )
        conn.commit()
        conn.close()

        json_response(self, HTTPStatus.OK, {"success": True, "message": SUCCESS_MESSAGE, "lead_status": lead_status})

    def _handle_list_leads(self, query: str) -> None:
        parsed = parse_qs(query)
        q = (parsed.get("q", [""])[0] or "").strip()
        status = (parsed.get("status", [""])[0] or "").strip()

        filters = []
        params = []
        if q:
            filters.append("(full_name LIKE ? OR email LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])
        if status:
            filters.append("lead_status = ?")
            params.append(status)

        where = f" WHERE {' AND '.join(filters)}" if filters else ""
        sql = (
            "SELECT id, full_name, email, phone, country, budget, interest_type, "
            "preferred_lot_or_area, message, lead_status, created_at "
            f"FROM leads{where} ORDER BY datetime(created_at) DESC"
        )
        conn = get_db_connection()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        json_response(self, HTTPStatus.OK, {"leads": [dict(r) for r in rows]})

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    init_db()
    seed_data()
    server = ThreadingHTTPServer(("0.0.0.0", 5000), AppHandler)
    print("Server running on http://127.0.0.1:5000")
    server.serve_forever()


if __name__ == "__main__":
    run()
