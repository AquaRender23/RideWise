from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from config import MONGO_URI, SECRET_KEY
import requests
from bson import ObjectId

app = Flask(__name__)
app.secret_key = SECRET_KEY
bcrypt = Bcrypt(app)

# MongoDB
client = MongoClient(MONGO_URI)
db = client["ridewise_db"]

# Convert address to coordinates using Nominatim
def get_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json"
    }
    headers = {
        "User-Agent": "RideWiseApp"
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if data:
        return float(data[0]["lat"]), float(data[0]["lon"])
    return None, None


# Get driving distance using OSRM
def get_distance(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    response = requests.get(url)
    data = response.json()

    if data.get("routes"):
        distance_meters = data["routes"][0]["distance"]
        return distance_meters / 1000  # km
    return 0

@app.route("/")
def home():
    return render_template("landing.html")


# Register page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        existing_user = db.users.find_one({"email": email})
        if existing_user:
            return "User already exists!"

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "phone": phone
        })

        return redirect(url_for("login"))

    return render_template("register.html")


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        selected_role = request.form["role"]

        user = db.users.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):

            session["user_id"] = str(user["_id"])
            session["role"] = selected_role
            session["name"] = user["name"]

            if selected_role == "rider":
                return redirect(url_for("rider_dashboard"))

            elif selected_role == "driver":
                return redirect(url_for("driver_dashboard"))

            elif selected_role == "admin":
                return redirect(url_for("admin_dashboard"))

        return "Invalid Credentials"

    return render_template("login.html")


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# Rider Dashboard
@app.route("/rider/dashboard")
def rider_dashboard():
    if session.get("role") != "rider":
        return "Access Denied"

    return render_template("rider_dashboard.html", name=session.get("name"))


# Driver Dashboard
@app.route("/driver/dashboard")
def driver_dashboard():
    if session.get("role") != "driver":
        return "Access Denied"

    return render_template("driver_dashboard.html", name=session.get("name"))

# Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return "Access Denied"

    return render_template("admin.html", name=session.get("name"))


# Rider - book ride
@app.route("/book_ride", methods=["GET", "POST"])
def book_ride():
    if session.get("role") != "rider":
        return "Access Denied"

    if request.method == "POST":
        start = request.form["start"]
        end = request.form["end"]
        date = request.form["date"]
        time = request.form["time"]
        people = int(request.form["people"])

        # 🔹 Convert addresses to coordinates
        start_lat, start_lon = get_coordinates(start)
        end_lat, end_lon = get_coordinates(end)

        if not start_lat or not end_lat:
            return "Invalid location entered"

        # 🔹 Get real driving distance (km)
        distance = get_distance(start_lat, start_lon, end_lat, end_lon)

        if distance == 0:
            return "Unable to calculate distance"

        # 🔹 Find matching driver ride
        ride = db.driver_rides.find_one({
            "start_location": start,
            "end_location": end,
            "date": date,
            "time": time,
            "available_seats": {"$gte": people}
        })

        if not ride:
            return render_template("sorry.html")
        
        try:
            driver_object_id = ObjectId(ride["driver_id"])
            driver = db.users.find_one({"_id": driver_object_id})
        except:
            driver = None

        print("Driver fetched:", driver)
        
        driver = db.users.find_one({
            "_id": ObjectId(ride["driver_id"])
        })

        # 🔹 Calculate eco values based on REAL distance
        fare = round(distance * 10, 2)
        fuel_saved = round(distance * 0.2, 2)
        co2_saved = round(distance * 0.5, 2)
        eco_points = int(distance * 5)

        # 🔹 Store booking
        db.booked_rides.insert_one({
            "ride_id": str(ride["_id"]),
            "driver_id": ride["driver_id"],
            "rider_id": session["user_id"],

            "driver_name": driver["name"] if driver else "N/A",
            "driver_phone": driver["phone"] if driver else "N/A",
            "vehicle_number": ride.get("vehicle_info", "N/A"),

            "start_location": start,
            "end_location": end,
            "distance_km": distance,
            "people": people,
            "fare": fare,
            "fuel_saved": fuel_saved,
            "co2_saved": co2_saved,
            "eco_points": eco_points,
            "status": "upcoming"
        })

        # 🔹 Reduce available seats
        db.driver_rides.update_one(
            {"_id": ride["_id"]},
            {"$inc": {"available_seats": -people}}
        )

        return redirect(url_for("rider_history"))

    return render_template("book_ride.html")

# Driver - add ride
@app.route("/add_ride", methods=["GET", "POST"])
def add_ride():

    print("SESSION ROLE:", session.get("role"))
    if session.get("role") != "driver":
        return "Access Denied"

    if request.method == "POST":
        vehicle = request.form["vehicle"]
        start = request.form["start"]
        end = request.form["end"]
        date = request.form["date"]
        time = request.form["time"]
        capacity = int(request.form["capacity"])

        db.driver_rides.insert_one({
            "driver_id": session["user_id"],
            "vehicle_info": vehicle,
            "start_location": start,
            "end_location": end,
            "date": date,
            "time": time,
            "capacity": capacity,
            "available_seats": capacity
        })

        return redirect(url_for("driver_history"))

    return render_template("add_ride.html")

@app.route("/rider_history")
def rider_history():
    if session.get("role") != "rider":
        return "Access Denied"

    rider_id = session["user_id"]

    rides = list(db.booked_rides.find({
        "rider_id": rider_id
    }))

    print("ALL BOOKINGS:", list(db.booked_rides.find()))
    print("SESSION USER ID:", rider_id)
    print("FILTERED RIDES FOR THIS USER:", rides)
    
    return render_template("rider_history.html", rides=rides)


@app.route("/driver_history")
def driver_history():
    if session.get("role") != "driver":
        return "Access Denied"

    driver_id = session["user_id"]

    # 🔥 FIRST define bookings
    bookings = list(db.booked_rides.find({
        "driver_id": driver_id
    }))

    # 🔥 THEN loop
    for booking in bookings:
        rider = db.users.find_one({
            "_id": ObjectId(booking["rider_id"])
        })

        booking["rider_name"] = rider["name"] if rider else "N/A"
        booking["rider_phone"] = rider["phone"] if rider else "N/A"

    return render_template("driver_history.html", bookings=bookings)


# 🔹 Line Chart Data
@app.route("/co2-data")
def co2_data():
    data = {
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "values": [12, 18, 10, 25, 30, 22]
    }
    return jsonify(data)


# 🔹 Pie Chart Data
@app.route("/ride-distribution")
def ride_distribution():
    data = {
        "labels": ["Completed", "Pending", "Cancelled"],
        "values": [65, 20, 15]
    }
    return jsonify(data)


# 🔹 Bar Chart Data
@app.route("/emission-data")
def emission_data():
    data = {
        "labels": ["Normal Ride", "Shared Ride"],
        "values": [180, 110]
    }
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)