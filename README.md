# Osa Golf Course Lead Generation App

Minimal full-stack web app to capture prospects interested in lot sales, golf memberships, project visits, and investment opportunities at **Osa Golf Course, Costa Rica**.

## Features
- Premium, responsive landing page in English for international audiences.
- Sales-focused messaging aligned to exclusivity, nature, golf lifestyle, and investment opportunity.
- Prospect form with all required fields plus **Registration Date**.
- SQLite persistence for every submitted lead.
- Automatic lead scoring:
  - **Hot Lead**: budget >= 120000 USD
  - **Warm Lead**: budget 80000 to 119999 USD
  - **Cold Lead**: budget < 80000 USD
- Internal admin dashboard to view saved prospects and classification.
- Admin tools:
  - Filter by country
  - Filter by interest type
  - Search by name or email
  - Export filtered leads to CSV
- Leads sorted by priority (Hot → Warm → Cold) and then newest date.
- Automatic professional thank-you message after form submission.
- Automatic follow-up email content generation and queueing for each new prospect.
- Sample data seeding for testing.
- Runs with Python standard library only (no external packages).

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python (`http.server`)
- **Database:** SQLite

## Project Structure

```bash
.
├── app.py
├── leads.db                  # created automatically after first run
├── static/
│   ├── script.js
│   └── styles.css
├── templates/
│   ├── admin.html
│   └── index.html
├── Procfile                  # hosting-ready (platforms like Render/Heroku-style)
└── Dockerfile                # container-ready deployment option
```

## Local Setup

1. (Optional) Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Run the application:

```bash
python3 app.py
```

3. Open in your browser:
- Landing page: `http://127.0.0.1:5000/`
- Dashboard: `http://127.0.0.1:5000/admin`

## Dashboard Query Parameters
You can share filtered admin views using query params:

- `country` (exact country)
- `interest_type` (exact interest type)
- `q` (search text over full name/email)

Example:

```text
/admin?country=United+States&interest_type=Lot+Purchase&q=michael
```

## CSV Export
From the dashboard, click **Export CSV**.

If filters/search are active, export preserves the same filtered dataset.

## Hosting Preparation
This project is prepared for future deployment:

- `PORT` env var supported (used by many hosting providers).
- `Procfile` included for web process declaration.
- `Dockerfile` included for container deployment.

## Testing the MVP Quickly

- On first run, the app inserts sample leads automatically when the table is empty.
- Submit a new lead from the landing page and check it appears in the dashboard.
- Try these budgets to verify classification:
  - `150000` -> Hot Lead
  - `90000` -> Warm Lead
  - `50000` -> Cold Lead
