# Osa Golf Course Lead Generation MVP (React + Flask + SQLite)

A complete local MVP for capturing and managing international prospects interested in Osa Golf Course (Costa Rica).

## Stack
- **Frontend:** React (client-side)
- **Backend:** Flask
- **Database:** SQLite

## Features
- Premium landing page with real-estate and golf lifestyle tone.
- Hero, benefits, and conversion-focused lead form sections.
- Lead form with required validation and inline friendly error messages.
- SQLite lead storage with automatic lead classification:
  - Hot Lead: >= 120000 USD
  - Warm Lead: 80000 to 119999 USD
  - Cold Lead: < 80000 USD
- Admin dashboard with:
  - Newest-first table
  - Search by name/email
  - Filter by lead status
- Automatic success message after submission.
- Welcome email template endpoint and queue table for future real email integration.

## Project Structure

```bash
.
├── app.py
├── requirements.txt
├── leads.db                    # auto-created
├── templates/
│   ├── index.html
│   └── admin.html
└── static/
    ├── styles.css
    ├── landing-app.jsx
    └── admin-app.jsx
```

## Local Setup

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python3 app.py
```

4. Open:
- Landing page: `http://127.0.0.1:5000/`
- Admin dashboard: `http://127.0.0.1:5000/admin`

## API Endpoints
- `GET /api/health`
- `POST /api/leads`
- `GET /api/leads?q=<name_or_email>&status=<Hot Lead|Warm Lead|Cold Lead>`
- `GET /api/welcome-template`

## Notes
- `outbound_emails` stores queued welcome email content for future SMTP/provider integration.
- Seed sample leads are inserted automatically the first time if database is empty.
