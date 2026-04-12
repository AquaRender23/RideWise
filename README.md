# 🌿 RideWise

> **Drive Smart. Travel Green.**

RideWise is a full-stack carpooling web application that connects eco-conscious riders and drivers. It calculates real driving distances, matches riders to available driver rides, and tracks environmental impact — CO₂ saved, fuel conserved, and eco points earned — all in real time.

---

## 🌟 Features

✅ **Role-Based Login** – Separate dashboards for Riders, Drivers, and Admins  
✅ **Smart Ride Matching** – Matches riders to drivers based on route, date, time & seats  
✅ **Real Distance Calculation** – Powered by OSRM routing engine + Nominatim geocoding  
✅ **Eco Impact Tracking** – CO₂ saved, fuel saved, fare estimate & eco points per ride  
✅ **Interactive Maps** – Live Leaflet.js maps on booking and ride-adding pages  
✅ **Live Charts** – Chart.js dashboards with CO₂ trends, ride distribution & emission comparison  
✅ **Secure Auth** – Password hashing via Flask-Bcrypt with session management  
✅ **Admin Panel** – Overview of rides, drivers, complaints & green impact stats  

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
source venv/bin/activate      # On Linux/macOS
venv\Scripts\activate         # On Windows
```

### 3. Install Dependencies

```bash
pip install flask pymongo flask-bcrypt requests
```

### 4. Set Up Configuration

Create a `config.py` file in the root directory:

```python
MONGO_URI = "mongodb+srv://your-mongo-uri"
SECRET_KEY = "your-secret-key"
```

### 5. Run the App

```bash
python app.py
```

Then open your browser at:

```
http://localhost:5000
```

---

## 📂 Folder Structure

```
📂 ridewise
├── 📂 templates
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
├── 📂 static
│   ├── 📂 images
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
├── 📄 app.py
├── 📄 config.py
└── 📄 README.md
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
| GET | `/co2-data` | Line chart data (CO₂ by month) |
| GET | `/ride-distribution` | Pie chart data (ride statuses) |
| GET | `/emission-data` | Bar chart data (emission comparison) |

---

## 💡 How It Works

1. **Register & Login** — Users sign up and log in as a Rider, Driver, or Admin.
2. **Driver adds a ride** — Specifies route, date, time, vehicle number & available seats.
3. **Rider books a ride** — Enters matching route, date, time & number of passengers.
4. **Smart matching** — App finds a driver ride that fits all criteria.
5. **Distance & fare calculated** — OSRM computes real driving distance; fare = distance × ₹10/km.
6. **Eco impact saved** — CO₂ saved, fuel saved & eco points stored per booking.
7. **History & dashboards** — Both riders and drivers can view all past rides with eco breakdowns.

---

## 🌍 Eco Impact Calculation

| Metric | Formula |
|---|---|
| 💰 Fare | `distance × ₹10` |
| ⛽ Fuel Saved | `distance × 0.2 L` |
| 🌍 CO₂ Saved | `distance × 0.5 kg` |
| ⭐ Eco Points | `distance × 5 pts` |

---

## 🚀 Future Plans

* ✅ Real-time ride tracking on map
* ✅ Dynamic eco stats pulled from actual ride history
* ✅ Rating system for drivers and riders
* ✅ Push notifications for upcoming rides
* ✅ GitHub OAuth login support
* ✅ Deployment on Render / Railway

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/awesome-feature`)
3. Commit your changes (`git commit -m "Add awesome feature"`)
4. Push to the branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

---

## 🏆 Credits

* Built by the **RideWise Team**
* Maps powered by [OpenStreetMap](https://www.openstreetmap.org/) & [Leaflet.js](https://leafletjs.com/)
* Routing by [OSRM](http://project-osrm.org/)
* Geocoding by [Nominatim](https://nominatim.org/)

---

> 🔥 **RideWise** — Empowering greener commutes, one shared ride at a time. 🌿
