from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

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


def lead_priority_rank(classification: str) -> int:
    return {"Hot Lead": 1, "Warm Lead": 2, "Cold Lead": 3}.get(classification, 4)


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
            registration_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(leads)").fetchall()}
    if "registration_date" not in columns:
        conn.execute("ALTER TABLE leads ADD COLUMN registration_date TEXT")

    conn.commit()
    conn.close()


def seed_sample_data() -> None:
    sample = [
        ("Michael Turner", "mturner@example.com", "+1 305 555 1987", "United States", 165000, "Lot Purchase", "Ocean View Ridge", "Interested in premium lots near the fairway.", "2026-03-12"),
        ("Sofia Weiss", "sofia.weiss@example.com", "+49 1512 3456789", "Germany", 98000, "Golf Membership", "Clubhouse Zone", "Would like annual membership details for my family.", "2026-03-15"),
        ("Daniela Solano", "dsolano@example.com", "+506 8888 1111", "Costa Rica", 65000, "Golf Visit", "South Green Access", "Planning an on-site visit next month.", "2026-03-20"),
    ]
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) AS total FROM leads").fetchone()["total"]
    if total == 0:
        conn.executemany(
            """
            INSERT INTO leads (
                full_name, email, phone_whatsapp, country, budget,
                interest_type, preferred_lot_area, message, lead_classification, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [row[:-1] + (classify_lead(float(row[4])), row[-1]) for row in sample],
        )
        conn.commit()
    conn.close()


def html_escape(value: str | None) -> str:
    if not value:
        return ""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def fetch_leads(filters: dict[str, str]) -> list[sqlite3.Row]:
    where_parts: list[str] = []
    params: list[str] = []

    country = filters.get("country", "").strip()
    interest_type = filters.get("interest_type", "").strip()
    query = filters.get("q", "").strip()

    if country:
        where_parts.append("country = ?")
        params.append(country)

    if interest_type:
        where_parts.append("interest_type = ?")
        params.append(interest_type)

    if query:
        where_parts.append("(full_name LIKE ? OR email LIKE ?)")
        like_q = f"%{query}%"
        params.extend([like_q, like_q])

    where_clause = ""
    if where_parts:
        where_clause = " WHERE " + " AND ".join(where_parts)

    sql = f"""
        SELECT *
        FROM leads
        {where_clause}
        ORDER BY
            CASE lead_classification
                WHEN 'Hot Lead' THEN 1
                WHEN 'Warm Lead' THEN 2
                WHEN 'Cold Lead' THEN 3
                ELSE 4
            END,
            datetime(created_at) DESC
    """

    conn = get_db_connection()
    leads = conn.execute(sql, params).fetchall()
    conn.close()
    return leads


def get_filter_options() -> tuple[list[str], list[str]]:
    conn = get_db_connection()
    countries = [row[0] for row in conn.execute("SELECT DISTINCT country FROM leads ORDER BY country").fetchall()]
    interests = [row[0] for row in conn.execute("SELECT DISTINCT interest_type FROM leads ORDER BY interest_type").fetchall()]
    conn.close()
    return countries, interests


def render_admin_page(filters: dict[str, str]) -> str:
    template = (TEMPLATES_DIR / "admin.html").read_text(encoding="utf-8")
    leads = fetch_leads(filters)
    countries, interests = get_filter_options()

    rows: list[str] = []
    if not leads:
        rows.append("<tr><td colspan='10'>No prospects found with the selected filters.</td></tr>")

    for lead in leads:
        badge = lead["lead_classification"].split()[0].lower()
        rows.append(
            f"""
            <tr>
              <td>{lead['created_at']}</td>
              <td>{html_escape(lead['registration_date'])}</td>
              <td>{html_escape(lead['full_name'])}</td>
              <td><div>{html_escape(lead['email'])}</div><div>{html_escape(lead['phone_whatsapp'])}</div></td>
              <td>{html_escape(lead['country'])}</td>
              <td>${lead['budget']:.0f}</td>
              <td>{html_escape(lead['interest_type'])}</td>
              <td>{html_escape(lead['preferred_lot_area'])}</td>
              <td><span class='badge {badge}'>{html_escape(lead['lead_classification'])}</span></td>
              <td>{html_escape(lead['message'])}</td>
            </tr>
            """
        )

    country_options = ["<option value=''>All countries</option>"]
    for country in countries:
        selected = "selected" if country == filters.get("country", "") else ""
        country_options.append(f"<option value='{html_escape(country)}' {selected}>{html_escape(country)}</option>")

    interest_options = ["<option value=''>All interests</option>"]
    for interest in interests:
        selected = "selected" if interest == filters.get("interest_type", "") else ""
        interest_options.append(f"<option value='{html_escape(interest)}' {selected}>{html_escape(interest)}</option>")

    query_string = urlencode({k: v for k, v in filters.items() if v})
    export_href = "/export/csv" if not query_string else f"/export/csv?{query_string}"

    return (
        template.replace("{{rows}}", "\n".join(rows))
        .replace("{{country_options}}", "\n".join(country_options))
        .replace("{{interest_options}}", "\n".join(interest_options))
        .replace("{{search_query}}", html_escape(filters.get("q", "")))
        .replace("{{export_href}}", export_href)
    )


def export_leads_csv(filters: dict[str, str]) -> bytes:
    leads = fetch_leads(filters)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID",
            "Created At",
            "Registration Date",
            "Full Name",
            "Email",
            "Phone/WhatsApp",
            "Country",
            "Budget",
            "Interest Type",
            "Preferred Lot/Area",
            "Classification",
            "Message",
        ]
    )
    for lead in leads:
        writer.writerow(
            [
                lead["id"],
                lead["created_at"],
                lead["registration_date"],
                lead["full_name"],
                lead["email"],
                lead["phone_whatsapp"],
                lead["country"],
                lead["budget"],
                lead["interest_type"],
                lead["preferred_lot_area"],
                lead["lead_classification"],
                lead["message"],
            ]
        )
    return output.getvalue().encode("utf-8")


class AppHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8", extra_headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _parse_filters(self) -> dict[str, str]:
        qs = parse_qs(urlparse(self.path).query)
        return {
            "country": (qs.get("country", [""])[0] or "").strip(),
            "interest_type": (qs.get("interest_type", [""])[0] or "").strip(),
            "q": (qs.get("q", [""])[0] or "").strip(),
        }

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            html = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
            self._send(HTTPStatus.OK, html.encode("utf-8"))
            return

        if path == "/admin":
            html = render_admin_page(self._parse_filters())
            self._send(HTTPStatus.OK, html.encode("utf-8"))
            return

        if path == "/export/csv":
            payload = export_leads_csv(self._parse_filters())
            filename = f"osa_leads_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            self._send(
                HTTPStatus.OK,
                payload,
                "text/csv; charset=utf-8",
                extra_headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
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

        registration_date = data.get("registration_date", "").strip() or datetime.utcnow().date().isoformat()
        lead_classification = classify_lead(budget)

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO leads (
                full_name, email, phone_whatsapp, country, budget,
                interest_type, preferred_lot_area, message, lead_classification, registration_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                registration_date,
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
                    "Our advisory team has received your request and will contact you shortly "
                    "with tailored options for premium real estate and golf lifestyle opportunities."
                ),
            }
        )
        self._send(HTTPStatus.OK, payload.encode("utf-8"), "application/json")


def run() -> None:
    init_db()
    seed_sample_data()
    port = int(__import__("os").environ.get("PORT", "5000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), AppHandler)
    print(f"Server running on http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
