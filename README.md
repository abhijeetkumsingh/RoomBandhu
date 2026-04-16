# 🏠 RoomBandhu — Full Stack Student Room Finder

## 📁 Project Structure
```
roombandhu/
├── app.py                  # Main Flask app (routes, models, logic)
├── requirements.txt        # Python dependencies
├── roombandhu.db           # SQLite database (auto-created on first run)
├── templates/
│   ├── base.html           # Base layout (navbar, flash, footer)
│   ├── index.html          # Home page with search, filters, room cards
│   ├── auth.html           # Login + Register (tabbed)
│   ├── add_room.html       # Add room form with image upload + GPS
│   ├── room_detail.html    # Room detail page with gallery + reviews
│   ├── dashboard.html      # User dashboard (my rooms, stats)
│   └── wishlist.html       # Saved rooms page
└── static/
    ├── css/style.css       # All styles (responsive, mobile-first)
    ├── js/main.js          # JS (nav, wishlist AJAX, stars, upload preview, geo)
    └── uploads/            # Uploaded room images (auto-created)
```

## 🚀 Setup & Run

### 1. Install Python (3.9+)
Download from https://python.org

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

The SQLite database (`roombandhu.db`) is created automatically on first run.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 👤 User Auth | Register, Login, Logout with hashed passwords |
| 🔒 Protected Routes | Add Room only works when logged in |
| 📸 Image Upload | Min 4 images, drag & drop, preview before upload |
| 📍 Geolocation | "Near Me" button finds closest rooms via GPS + Nominatim API |
| ❤ Wishlist | Save/unsave rooms via AJAX (no page reload) |
| ⭐ Reviews | Star rating + text reviews per room (one per user) |
| 🔍 Search + Filter | Search by title/location, filter by type/price, sort |
| 📱 Fully Responsive | Works perfectly on mobile, tablet, desktop |
| 🗄 Dashboard | View/delete your listings, toggle availability |
| 💬 WhatsApp | Direct WA link to contact room owner |

---

## 🔮 What to Build Next (Priority Order)

### Phase 2 — Immediate
1. **Email Verification** — Verify email on signup (Flask-Mail)
2. **Password Reset** — "Forgot Password" via email OTP
3. **Edit Room** — Allow owner to edit existing listings
4. **Room Image Carousel** — Swipeable gallery on detail page

### Phase 3 — Growth Features
5. **Advanced Search** — Filter by college name, radius distance
6. **Notifications** — Email/SMS alert when new room posted near a college
7. **Room Enquiry System** — In-app messaging between student and owner
8. **Owner Verification Badge** — Upload Aadhar for verified badge
9. **Admin Panel** — Approve/reject listings, manage users
10. **College Database** — Add "Near [College Name]" tags with real coordinates

### Phase 4 — Scale
11. **PostgreSQL** — Replace SQLite for production (use DATABASE_URL env var)
12. **Cloudinary / AWS S3** — Store images in cloud instead of local disk
13. **Deploy on Railway / Render** — Free hosting for Flask apps
14. **PWA** — Make it installable as a mobile app
15. **Google Maps Embed** — Show room location on embedded map
16. **Payment Integration** — Collect listing fee from owners (Razorpay)

---

## 🏗 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| Database | SQLite (dev) → PostgreSQL (prod) |
| ORM | SQLAlchemy |
| Auth | Werkzeug password hashing + Flask sessions |
| File Upload | Werkzeug + local storage |
| Frontend | Vanilla HTML/CSS/JS (no framework needed) |
| Geo API | Browser Geolocation API + Nominatim (free, no API key) |
| Maps | Google Maps link (no key needed for basic links) |
| Fonts | Google Fonts (Syne + Plus Jakarta Sans) |

---

## 🔑 Environment Variables (for production)

```env
SECRET_KEY=your_very_long_random_secret_key
DATABASE_URL=postgresql://user:pass@host/dbname
UPLOAD_FOLDER=/path/to/uploads
```

---

## 📝 Notes

- **No API key needed** — Geolocation uses browser GPS + Nominatim (OpenStreetMap) for reverse geocoding. Both are completely free.
- **SQLite** is fine for development and small deployments (<1000 users). Upgrade to PostgreSQL for production.
- Change `app.secret_key` in `app.py` before going live!
