# 🌿 RideWise

> **Drive Smart. Travel Green.**

RideWise is a full-stack carpooling web app that connects eco-conscious riders and drivers. It calculates real driving distances, matches riders to available drivers, and tracks environmental impact — CO₂ saved, fuel conserved, and eco points earned — all in real time.

---

## 🌟 Features

- **Role-Based Login** – Separate dashboards for Riders, Drivers, and Admins
- **Smart Ride Matching** – Matches riders to drivers based on route, date, time & available seats
- **Real Distance Calculation** – Powered by OSRM routing engine + Nominatim geocoding
- **Eco Impact Tracking** – CO₂ saved, fuel saved, fare estimate & eco points per ride
- **Interactive Maps** – Live Leaflet.js maps on booking and ride-adding pages
- **Live Charts** – Chart.js dashboards with CO₂ trends, ride distribution & emission comparison
- **Secure Auth** – Password hashing via Flask-Bcrypt with session management
- **Admin Panel** – Overview of rides, drivers, users & green impact stats

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| Database | MongoDB (via PyMongo) |
| Auth | Flask-Bcrypt + Sessions |
| Maps | Leaflet.js + OpenStreetMap |
| Routing | OSRM (Open Source Routing Machine) |
| Geocoding | Nominatim (OpenStreetMap) |
| Charts | Chart.js |
| Frontend | HTML, CSS, Jinja2 Templates |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ridewise.git
cd ridewise
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install flask pymongo flask-bcrypt requests
```

### 4. Set Up Configuration

Create a `config.py` in the root directory:

```python
MONGO_URI = "your-mongodb-uri"
SECRET_KEY = "your-secret-key"
```

### 5. Run the App

```bash
python app.py
```

Open your browser at `http://localhost:5000`

---

## 📂 Folder Structure

```
ridewise/
├── templates/
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── rider_dashboard.html
│   ├── driver_dashboard.html
│   ├── admin.html
│   ├── book_ride.html
│   ├── add_ride.html
│   ├── rider_history.html
│   ├── driver_history.html
│   └── sorry.html
├── static/
│   ├── images/
│   ├── landing.css
│   ├── login.css
│   ├── register.css
│   ├── rider_dashboard.css
│   ├── driver_dashboard.css
│   ├── book_ride.css
│   ├── add_ride.css
│   ├── rider_history.css
│   ├── driver_history.css
│   ├── admin.css
│   └── sorry.css
├── app.py
├── config.py
└── README.md
```

---

## 🛠️ API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET/POST | `/login` | User login with role selection |
| GET/POST | `/register` | New user registration |
| GET | `/logout` | Clear session and logout |
| GET/POST | `/book_ride` | Rider books an available ride |
| GET/POST | `/add_ride` | Driver lists a new ride |
| GET | `/rider/dashboard` | Rider dashboard with eco stats |
| GET | `/driver/dashboard` | Driver dashboard with eco stats |
| GET | `/admin/dashboard` | Admin overview panel |
| GET | `/rider_history` | Rider's booked ride history |
| GET | `/driver_history` | Driver's ride & booking history |
| GET | `/co2-data` | Line chart data (CO₂ by ride) |
| GET | `/ride-distribution` | Pie chart data (ride statuses) |
| GET | `/emission-data` | Bar chart data (fuel comparison) |

---

## 💡 How It Works

1. **Register & Login** — Users sign up and log in as a Rider, Driver, or Admin
2. **Driver adds a ride** — Specifies route, date, time, vehicle number & available seats
3. **Rider books a ride** — Enters matching route, date, time & number of passengers
4. **Smart matching** — App finds a driver whose route covers the rider's start and end points (within a 1.5 km radius), with a matching date and a departure time within 5 minutes
5. **Distance & fare calculated** — OSRM computes real driving distance; fare is split based on total passengers and includes fuel cost + driver profit
6. **Eco impact saved** — CO₂ saved, fuel used & eco points stored per booking, and updated dynamically as more riders join the same ride
7. **History & dashboards** — Riders and drivers can view all past rides with full eco breakdowns

---

## 🌍 Eco Impact Calculation

| Metric | Formula |
|---|---|
| ⛽ Fuel Used | `distance ÷ 15 (mileage)` |
| 💰 Fare per Rider | `(fuel cost + 15% driver profit) ÷ passengers` |
| 🌍 CO₂ Saved | `fuel used × 2.3 kg × (passengers − 1)` |
| 🌳 Trees Equivalent | `CO₂ saved ÷ 21` |
| ⭐ Eco Score | `(CO₂ saved ÷ CO₂ without sharing) × 100` |

---

## 🚀 Future Plans

- Real-time ride tracking on map
- Rating system for drivers and riders
- Push notifications for upcoming rides
- GitHub OAuth login support
- Deployment on Render / Railway

---

> 🔥 **RideWise** — Empowering greener commutes, one shared ride at a time. 🌿
