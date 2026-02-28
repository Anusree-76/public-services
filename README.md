# 🔧 SmartLocal — Local Service Finder

A full-stack web application that connects customers with verified local service providers (plumbers, electricians, carpenters, cleaners, and more) in their area.

---

## 🌐 Live Demo

> Deployed on Render: *(link will appear here after deployment)*

---

## ✨ Features

### For Customers
- 🔍 **Search Workers by Service** — Filter by service type (Carpenter, Cleaner, Plumber, etc.)
- 📍 **GPS-based Distance** — Find workers nearest to your live location
- 📅 **Slot Booking** — Pick from the worker's available time slots
- 💬 **WhatsApp Integration** — Booking confirmation sent with live location via WhatsApp
- ⭐ **Reviews & Ratings** — Leave feedback after service completion

### For Workers
- 📝 **Easy Registration** — Register with service type, price, location, and available slots
- 📊 **Worker Dashboard** — View total earnings, bookings, and ratings
- 🟢 **Availability Toggle** — Go online/offline for bookings
- 🆔 **AI Aadhaar Verification** — Aadhaar QR + OCR-based ID verification

### For Admin
- 👥 **User & Worker Management** — View, manage, and delete users/workers
- 📈 **Dashboard Stats** — Total users, workers, bookings, and earnings at a glance

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML, CSS, Vanilla JavaScript |
| **Backend** | Python, Flask |
| **Database** | SQLite (local) |
| **Hosting** | Render |
| **WSGI Server** | Gunicorn |

---

## 📁 Project Structure

```
service-finder/
├── app.py              # Flask backend (all API routes)
├── requirements.txt    # Python dependencies
├── Procfile            # Gunicorn start command for Render
├── render.yaml         # Render deployment config
├── .gitignore          # Files excluded from Git
└── public/
    └── indexx.html     # Main frontend (single-page app)
```

---

## 🚀 Run Locally

### Prerequisites
- Python 3.11+
- pip

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Anusree-76/public-services.git
cd public-services

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Flask app
python app.py
```

Then open your browser at: **http://localhost** (port 80)

---

## ☁️ Deploy to Render

1. Fork or push this repo to your GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Render auto-detects settings from `render.yaml`
5. Click **"Create Web Service"** — done! ✅

---

## 🔑 Default Admin Login

| Field | Value |
|-------|-------|
| Role | Administrator |
| Username | `admin` |
| Password | `Admin@123` |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/services` | List all service types |
| POST | `/api/auth/login` | User/Worker/Admin login |
| POST | `/api/workers/register` | Register a new worker |
| GET | `/api/workers` | Search workers by service + location |
| GET | `/api/workers/:id` | Get single worker profile |
| POST | `/api/bookings` | Create a new booking |
| GET | `/api/bookings/user` | Get bookings for a user |
| GET | `/api/bookings/worker/:id` | Get bookings for a worker |
| PATCH | `/api/bookings/:id/status` | Update booking status |
| GET | `/api/admin/stats` | Admin dashboard stats |

---

## 📝 License

This project is open-source and free to use.
