# Flask E‑Commerce (Starter Project)

A minimal, production-ready **starter** e‑commerce web app built with Flask, SQLAlchemy, and Flask‑Login.
It includes a product catalog, cart, checkout (mock), orders, admin product management, and user auth.

## Features
- Product listing, detail page, search
- Cart in session (add/update/remove)
- Mock checkout & order creation
- User registration/login (hashed passwords) with Flask‑Login
- Admin panel to create/update/delete products
- SQLite by default; easy to swap to Postgres/MySQL
- CSRF protection via Flask‑WTF
- Bootstrap UI (CDN)
- Seed script to populate sample products

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Initialize the database and seed sample data
python init_db.py

# Run the app
flask --app app run --debug
# Visit http://127.0.0.1:5000
```

### Default Admin
- Email: `admin@example.com`
- Password: `admin123`

> Change secrets in `config.py` before deploying anywhere public.

## ENV Variables (optional)
- `SECRET_KEY` – overrides default dev key
- `DATABASE_URL` – SQLAlchemy connection string (e.g., `sqlite:///ecom.db` or Postgres URL)

## Notes
- Payments are **mocked**. Integrate Stripe/Razorpay etc. for real payments.
- Use gunicorn + reverse proxy (nginx) for production.
