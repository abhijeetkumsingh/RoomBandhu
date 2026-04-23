# 🏠 RoomBandhu

Find affordable single rooms, shared rooms, and PGs near your college.

---

## 📦 Project Structure

```
RoomBandhu/
├── app.py                   ← Main Flask application
├── requirements.txt         ← Python dependencies
├── Procfile                 ← Gunicorn startup for Render
├── render.yaml              ← One-click Render deployment config
├── .env.example             ← Environment variable template
├── .gitignore
├── static/
│   ├── css/style.css        ← All styles (mobile-first)
│   ├── js/main.js           ← All JavaScript (CSRF-safe)
│   └── uploads/             ← User-uploaded room images
└── templates/
    ├── base.html            ← Base layout with navbar & footer
    ├── index.html           ← Home / room listing page
    ├── auth.html            ← Login & Register (+ Google)
    ├── forgot_password.html ← Step 1: Enter email
    ├── verify_otp.html      ← Step 2: Enter OTP
    ├── reset_password.html  ← Step 3: New password
    ├── dashboard.html       ← User dashboard
    ├── edit_profile.html    ← Edit profile & change password
    ├── add_room.html        ← List a new room
    ├── room_detail.html     ← Room detail + reviews
    ├── wishlist.html        ← Saved rooms
    ├── errors/
    │   ├── 404.html
    │   └── 500.html
    └── admin/
        ├── base.html        ← Admin sidebar layout
        ├── login.html       ← Admin login
        ├── dashboard.html   ← Stats overview
        ├── users.html       ← User management
        └── rooms.html       ← Listing management
```

---

## 🚀 How to Run Locally

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Setup

```bash

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env — at minimum set a SECRET_KEY

# Run the app
python app.py
```

Open → **http://localhost:5000**


---

## ☁️ Deploy on Render (Recommended)

### Option A — render.yaml (Easiest)

1. Push this project to a **GitHub repository**.
2. Go to [render.com](https://render.com) → **New → Blueprint**.
3. Connect your repo — Render reads `render.yaml` automatically.
4. It creates a **web service** + **PostgreSQL database** together.
5. Set the secret environment variables in the Render dashboard:
   - `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`
   - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD`
6. Deploy. Done.

### Option B — Manual

1. **New Web Service** → connect GitHub repo
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120`
4. Add a **PostgreSQL** database service, copy its **Internal Database URL** as `DATABASE_URL`
5. Add all env vars listed in `.env.example`

---

## 🔐 Default Admin Login

| Field    | Value                  |
|----------|------------------------|
| URL      | `/admin/login`         |
| Email    | `admin@roombandhu.com` |
| Password | `Admin@Secure123`      |

---

## 🗄️ Database Notes

- **Local**: SQLite (`roombandhu.db`) created automatically on first run — no setup needed.
- **Production**: PostgreSQL — `DATABASE_URL` is set by Render automatically.
- Tables are created automatically via `db.create_all()` on startup.
- **Existing data is safe** — `db.create_all()` only creates missing tables, never drops data.
- If you need to add a new column after deployment, use Flask-Migrate or alter the table manually.

### Migrate existing SQLite data to PostgreSQL

```bash
# Install pgloader
# Then:
pgloader sqlite:///roombandhu.db postgresql://user:pass@host/dbname
---

*Built with ❤️ by Abhijeet Kumar Singh — RoomBandhu © 2026*
