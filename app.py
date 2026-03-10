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


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def classify_lead(budget: float) -> str:
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
            phone_whatsapp TEXT NOT NULL,
            country TEXT NOT NULL,
            budget REAL NOT NULL,
            interest_type TEXT NOT NULL,
            preferred_lot_area TEXT,
            message TEXT,
            lead_classification TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def seed_sample_data() -> None:
    sample = [
        ("Michael Turner", "mturner@example.com", "+1 305 555 1987", "United States", 165000, "Lot Purchase", "Ocean View Ridge", "Interested in premium lots near the fairway."),
        ("Sofia Weiss", "sofia.weiss@example.com", "+49 1512 3456789", "Germany", 98000, "Golf Membership", "Clubhouse Zone", "Would like annual membership details for my family."),
        ("Daniela Solano", "dsolano@example.com", "+506 8888 1111", "Costa Rica", 65000, "Golf Visit", "South Green Access", "Planning an on-site visit next month."),
    ]
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]
    if total == 0:
        conn.executemany(
            """
            INSERT INTO leads (
                full_name, email, phone_whatsapp, country, budget,
                interest_type, preferred_lot_area, message, lead_classification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [row + (classify_lead(float(row[4])),) for row in sample],
        )
        conn.commit()
    conn.close()


def render_admin_rows() -> str:
    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM leads ORDER BY datetime(created_at) DESC").fetchall()
    conn.close()
    if not leads:
        return "<tr><td colspan='9'>No prospects yet.</td></tr>"

    rows = []
    for lead in leads:
        badge = lead["lead_classification"].split()[0].lower()
        rows.append(
            f"""
            <tr>
              <td>{lead['created_at']}</td>
              <td>{lead['full_name']}</td>
              <td><div>{lead['email']}</div><div>{lead['phone_whatsapp']}</div></td>
              <td>{lead['country']}</td>
              <td>${lead['budget']:.0f}</td>
              <td>{lead['interest_type']}</td>
              <td>{lead['preferred_lot_area'] or ''}</td>
              <td><span class='badge {badge}'>{lead['lead_classification']}</span></td>
              <td>{lead['message'] or ''}</td>
            </tr>
            """
        )
    return "\n".join(rows)


class AppHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_template(self, name: str) -> str:
        return (TEMPLATES_DIR / name).read_text(encoding="utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            html = self._read_template("index.html")
            self._send(HTTPStatus.OK, html.encode("utf-8"))
            return

        if path == "/admin":
            html = self._read_template("admin.html").replace("{{rows}}", render_admin_rows())
            self._send(HTTPStatus.OK, html.encode("utf-8"))
            return

        if path == "/health":
            self._send(HTTPStatus.OK, b'{"status":"ok"}', "application/json")
            return

        if path.startswith("/static/"):
            file_path = STATIC_DIR / path.replace("/static/", "", 1)
            if file_path.exists() and file_path.is_file():
                ctype = "text/plain"
                if file_path.suffix == ".css":
                    ctype = "text/css"
                elif file_path.suffix == ".js":
                    ctype = "application/javascript"
                self._send(HTTPStatus.OK, file_path.read_bytes(), ctype)
                return

        self._send(HTTPStatus.NOT_FOUND, b"Not Found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/submit":
            self._send(HTTPStatus.NOT_FOUND, b"Not Found", "text/plain")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length).decode("utf-8")
        content_type = self.headers.get("Content-Type", "")

        data: dict[str, str]
        if "application/json" in content_type:
            data = json.loads(raw or "{}")
        else:
            parsed = parse_qs(raw)
            data = {k: v[0] for k, v in parsed.items()}

        required = ["full_name", "email", "phone_whatsapp", "country", "budget", "interest_type"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            payload = json.dumps({"success": False, "message": f"Missing required fields: {', '.join(missing)}"})
            self._send(HTTPStatus.BAD_REQUEST, payload.encode("utf-8"), "application/json")
            return

        try:
            budget = float(data.get("budget", 0))
        except ValueError:
            payload = json.dumps({"success": False, "message": "Budget must be a valid number."})
            self._send(HTTPStatus.BAD_REQUEST, payload.encode("utf-8"), "application/json")
            return

        lead_classification = classify_lead(budget)
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO leads (
                full_name, email, phone_whatsapp, country, budget,
                interest_type, preferred_lot_area, message, lead_classification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("full_name"),
                data.get("email"),
                data.get("phone_whatsapp"),
                data.get("country"),
                budget,
                data.get("interest_type"),
                data.get("preferred_lot_area", ""),
                data.get("message", ""),
                lead_classification,
            ),
        )
        conn.commit()
        conn.close()

        payload = json.dumps(
            {
                "success": True,
                "classification": lead_classification,
                "message": (
                    "Thank you for your interest in Osa Golf Course, Costa Rica. "
                    "Our team has received your request and will contact you soon "
                    "with tailored options for real estate and golf lifestyle opportunities."
                ),
            }
        )
        self._send(HTTPStatus.OK, payload.encode("utf-8"), "application/json")


def run() -> None:
    init_db()
    seed_sample_data()
    server = ThreadingHTTPServer(("0.0.0.0", 5000), AppHandler)
    print("Server running on http://127.0.0.1:5000")
    server.serve_forever()


if __name__ == "__main__":
    run()
