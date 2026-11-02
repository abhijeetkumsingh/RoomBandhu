# 🏠 RoomBandhu
### Find Your Perfect Room Near College

**RoomBandhu** is a student-focused accommodation platform designed to make finding affordable rooms near colleges easier and more convenient.

The platform helps students explore available room listings, compare rental prices, view property details, and save their favourite accommodation options.

<p align="center">
  <strong>Find a Room. Find Your Comfort. Find Your Bandhu.</strong>
</p>

---

## 🌐 Live Project

**Live Website:** https://roombandhu.onrender.com

**GitHub Repository:** https://github.com/abhijeetkumsingh/RoomBandhu

---

## ✨ Key Features

- 🔐 **User Authentication** – Secure registration, login and logout.
- 🌐 **Google Authentication** – Google OAuth integration.
- 🏘️ **Room Listings** – Explore available rooms and accommodation.
- 🔍 **Search & Filters** – Search and filter rooms according to preferences.
- 💰 **Price Sorting** – Sort room listings by rental price.
- 🖼️ **Room Details** – View room information and photographs.
- ❤️ **Wishlist** – Save favourite room listings.
- ⭐ **Reviews** – Share feedback on room listings.
- 📊 **User Dashboard** – Manage user activities and profile.
- 🛠️ **Admin Panel** – Administrative management functionality.
- 📍 **Nearby Search** – Location-based room discovery support.
- 📱 **Responsive Design** – User-friendly interface for desktop and mobile.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, Flask |
| Database | PostgreSQL, SQLite |
| ORM | Flask-SQLAlchemy, SQLAlchemy |
| Authentication | Firebase Authentication, Google OAuth |
| Security | Flask-WTF, Werkzeug |
| Email Service | Flask-Mail |
| Testing | Pytest |
| Deployment | Render |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
RoomBandhu/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Development and testing dependencies
├── pytest.ini                       # Pytest configuration
├── Procfile                         # Gunicorn startup configuration
├── render.yaml                      # Render deployment configuration
├── .gitignore                       # Git ignored files configuration
│
├── scripts/
│   └── seed_demo_rooms.py           # Demo room data seeder
│
├── static/
│   ├── css/
│   │   └── style.css                # Application styles
│   │
│   ├── js/
│   │   └── main.js                  # Frontend JavaScript
│   │
│   ├── images/
│   │   ├── room-01.png
│   │   ├── room-02.png
│   │   ├── room-03.png
│   │   └── room-04.png
│   │
│   └── uploads/                     # User-uploaded room images
│
├── templates/
│   ├── base.html                    # Base layout
│   ├── index.html                   # Homepage and room listings
│   ├── auth.html                    # Login and registration
│   ├── room_detail.html             # Room details and reviews
│   ├── wishlist.html                # Saved rooms
│   ├── dashboard.html               # User dashboard
│   ├── edit_profile.html            # Profile management
│   ├── add_room.html                # Add new room listing
│   ├── forgot_password.html         # Password recovery
│   ├── verify_otp.html              # OTP verification
│   ├── reset_password.html          # Password reset
│   │
│   ├── errors/
│   │   ├── 404.html                 # Page not found
│   │   └── 500.html                 # Server error
│   │
│   └── admin/
│       ├── base.html                # Admin layout
│       ├── login.html               # Admin login
│       ├── dashboard.html           # Admin dashboard
│       ├── users.html               # User management
│       └── rooms.html               # Room management
│
└── tests/
    ├── conftest.py                  # Test configuration and fixtures
    ├── test_auth.py                 # Authentication tests
    ├── test_rooms.py                # Room functionality tests
    ├── test_public_routes.py        # Public route tests
    └── test_admin_and_external_auth.py
```

---

## 🎯 Project Objective

Finding affordable accommodation near educational institutions can be challenging for students, especially those moving away from home for higher education.

RoomBandhu aims to simplify this process by providing a centralized platform where students can discover suitable rooms, explore rental information, and manage their accommodation preferences.

---

## 🧪 Quality & Testing

RoomBandhu includes an automated testing suite built with Pytest.

The tests cover:
- Authentication functionality
- Public application routes
- Room listing and detail functionality
- Wishlist and user-related features
- Administrative functionality
- External authentication flows

**Latest verified test result:** 39 tests passed.

---

## 🚀 Deployment

RoomBandhu is deployed on **Render**.

- Application hosting: Render Web Service
- Production database: PostgreSQL
- Application server: Gunicorn
- Source code management: GitHub

**Live Website:** https://roombandhu.onrender.com

---

## 🔮 Future Scope

- Advanced location-based room recommendations.
- Interactive map-based room discovery.
- Online room booking and payment integration.
- Real-time communication between students and property owners.
- Verified property listings.
- Enhanced room recommendation system.

---

## 👨‍💻 Developer

**Abhijeet Kumar Singh**

B.Tech – Computer Science Engineering (AI)

Government Engineering College, Lakhisarai, Bihar

**GitHub:** https://github.com/abhijeetkumsingh

---

## 🔒 Copyright & Usage Notice

© 2026 Abhijeet Kumar Singh. All Rights Reserved.

RoomBandhu is a proprietary project developed and maintained by its author.

This repository is published for portfolio, demonstration, and project showcase purposes only.

No permission is granted to copy, reproduce, modify, distribute, reuse, or commercially exploit the project's source code, UI/UX design, branding, graphics, or other assets without prior written permission from the author.

**This project is not open source. No open-source license is granted. All rights are reserved.**

---

<p align="center">
  <strong>RoomBandhu – Making Student Accommodation Easier! 🏠</strong>
