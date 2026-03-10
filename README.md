# Osa Golf Course Lead Generation App

Minimal full-stack web app to capture prospects interested in lot sales, golf memberships, project visits, and investment opportunities at **Osa Golf Course, Costa Rica**.

## Features
- Premium, responsive landing page in English for international audiences.
- Prospect form with all required fields.
- SQLite persistence for every submitted lead.
- Automatic lead scoring:
  - **Hot Lead**: budget >= 120000 USD
  - **Warm Lead**: budget 80000 to 119999 USD
  - **Cold Lead**: budget < 80000 USD
- Internal admin dashboard to view saved prospects and classification.
- Automatic professional thank-you message after form submission.
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
├── requirements.txt
├── static/
│   ├── script.js
│   └── styles.css
└── templates/
    ├── admin.html
    └── index.html
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

## Testing the MVP Quickly

- On first run, the app inserts sample leads automatically when the table is empty.
- Submit a new lead from the landing page and check it appears in the dashboard.
- Try these budgets to verify classification:
  - `150000` -> Hot Lead
  - `90000` -> Warm Lead
  - `50000` -> Cold Lead
