# Osa Golf Course Lead Generation MVP (Local, Reliable)

Fully working local web app to capture, classify, and review leads for Osa Golf Course.

## 1) Project structure (frontend vs backend)

- **Backend:** `app.py` (Python HTTP server + API + SQLite logic)
- **Frontend:**
  - Pages: `templates/index.html` and `templates/admin.html`
  - Client JS: `static/landing-app.js` and `static/admin-app.js`
  - Styles: `static/styles.css`
- **Database:** `leads.db` (auto-created on first run)

## 2) What this MVP includes

- Landing page with required copy and premium style.
- Lead form with inline validation and friendly errors.
- API endpoint for lead submission (`POST /api/leads`).
- SQLite storage of leads with required fields.
- Automatic lead classification:
  - Hot Lead: `>= 120000`
  - Warm Lead: `80000 - 119999`
  - Cold Lead: `< 80000`
- Admin dashboard (`/admin`) with:
  - Newest-first list
  - Search by name or email
  - Filter by lead status
- Welcome email template endpoint (`GET /api/welcome-template`)
- Queue table `outbound_emails` for future email sending integration.

## 3) Exact local run steps

```bash
cd /workspace/codex-test
python3 app.py
```

Then open:
- Landing page: `http://127.0.0.1:5000/`
- Admin dashboard: `http://127.0.0.1:5000/admin`

## 4) API endpoints

- `GET /api/health`
- `POST /api/leads`
- `GET /api/leads?q=<name_or_email>&status=<Hot Lead|Warm Lead|Cold Lead>`
- `GET /api/welcome-template`

## 5) Quick verification checklist

1. Open `/` and confirm no 404.
2. Submit lead form.
3. Confirm success message appears.
4. Open `/admin` and confirm new lead appears.
5. Confirm `leads.db` exists in project root.
6. Optionally inspect DB quickly:

```bash
sqlite3 leads.db "SELECT id, full_name, email, lead_status, created_at FROM leads ORDER BY id DESC LIMIT 5;"
```

## 6) Notes

- Architecture was simplified to avoid broken dependency/CDN startup issues and ensure reliable local preview.
- No external pip/npm install is required for this local MVP.
