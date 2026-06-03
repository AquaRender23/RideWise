from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()
from config import MONGO_URI, SECRET_KEY
import requests
from bson import ObjectId
from datetime import datetime, timedelta
import math
from bson import ObjectId

app = Flask(__name__)
app.secret_key = SECRET_KEY
bcrypt = Bcrypt(app)

# MongoDB
client = MongoClient(MONGO_URI)
db = client["ridewise_db"]
rides_collection = db["rides"]

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

#Check if rider and driver locations are within the matching radius
def is_near(lat1, lon1, lat2, lon2, threshold_km=2):
    R = 6371  
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    a = math.sin(dLat/2)**2 + \
        math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * \
        math.sin(dLon/2)**2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance <= threshold_km

# Check if a location is close to a ride route
def point_near_route(point_lat, point_lon, route_coords, threshold_km=1.5):
    R = 6371  

    for coord in route_coords:
        route_lon, route_lat = coord

        dLat = math.radians(route_lat - point_lat)
        dLon = math.radians(route_lon - point_lon)

        a = math.sin(dLat/2)**2 + \
            math.cos(math.radians(point_lat)) * \
            math.cos(math.radians(route_lat)) * \
            math.sin(dLon/2)**2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c

        if distance <= threshold_km:
            return True

    return False

# Calculate fare, fuel usage, CO₂ savings, and eco score for a ride
def calculate_ride_details(distance, passengers):
    mileage = 15
    petrol_price = 100
    profit_percent = 0.15

    fuel_used = distance / mileage
    fuel_cost = fuel_used * petrol_price

    driver_profit = fuel_cost * profit_percent
    total_amount = fuel_cost + driver_profit

    fare_per_rider = total_amount / passengers

    co2_emitted = fuel_used * 2.3
    co2_without = co2_emitted * passengers
    co2_saved = co2_without - co2_emitted

    trees_saved = co2_saved / 21

    eco_score = (co2_saved / co2_without) * 100 if co2_without != 0 else 0

    return {
        "fare_per_rider": round(fare_per_rider, 2),
        "fuel_cost": round(fuel_cost, 2),
        "fuel_used": round(fuel_used, 2), 
        "driver_profit": round(driver_profit, 2),
        "co2_saved": round(co2_saved, 2),
        "trees_saved": round(trees_saved, 2),
        "eco_score": round(eco_score, 0)
    }

# Update upcoming rides to completed when ride time has passed
def update_ride_status():
    now = datetime.now()

    upcoming_rides = db.booked_rides.find({"status": "upcoming"})

    for ride in upcoming_rides:

        # Skip rides that don't have date or time
        if "date" not in ride or "time" not in ride:
            continue

        try:
            ride_datetime = datetime.strptime(
                ride["date"] + " " + ride["time"],
                "%Y-%m-%d %H:%M"
            )
        except:
            continue

        if ride_datetime < now:
            db.booked_rides.update_one(
                {"_id": ride["_id"]},
                {"$set": {"status": "completed"}}
            )
            
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
            "phone": phone,
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

    update_ride_status()

    rider_id = session["user_id"]

    # Fetch upcoming rides
    upcoming_rides = list(db.booked_rides.find({
        "rider_id": rider_id,
        "status": "upcoming"
    }))

    rides = list(db.booked_rides.find({"rider_id": rider_id}))

    total_co2 = sum(r.get("co2_saved", 0) for r in rides)
    total_fuel = round(sum(r.get("fuel_used", 0) for r in rides), 2)
    total_trees = sum(r.get("trees_saved", 0) for r in rides)

    eco_score = round(
        sum(r.get("eco_score", 0) for r in rides) / len(rides),
        2
    ) if rides else 0

    if len(rides) == 0:
        total_co2 = 0
        total_fuel = 0
        total_trees = 0
        eco_score = 0

    ride_ids = [r["ride_id"] for r in rides]

    all_rides = list(db.booked_rides.find({
        "ride_id": {"$in": ride_ids}
    }))

    ride_map = {}

    for r in all_rides:
        ride_id = r["ride_id"]

        if ride_id not in ride_map:
            ride_map[ride_id] = {
                "fuel": r.get("fuel_used", 0),
                "people": 0
            }

        ride_map[ride_id]["people"] += r.get("people", 0)

    normal_total = 0
    shared_total = 0

    for ride in ride_map.values():
        fuel = ride["fuel"]
        people = ride["people"]

        normal_total += fuel * people
        shared_total += fuel

    fuel_saved = round(normal_total - shared_total, 2)

    percent_saved = round(
        (fuel_saved / normal_total) * 100, 1
    ) if normal_total else 0

    return render_template(
        "rider_dashboard.html",
        name=session.get("name"),
        upcoming_rides=upcoming_rides,
        total_co2=total_co2,
        total_fuel=total_fuel,
        total_trees=total_trees,
        eco_score=eco_score,
        percent_saved=percent_saved   # 🔥 added
    )

# Get ride status data for the rider dashboard
@app.route("/ride-distribution")
def ride_distribution():

    if session.get("role") != "rider":
        return jsonify({"labels": [], "values": []})

    rider_id = session["user_id"]

    completed = db.booked_rides.count_documents({
        "rider_id": rider_id,
        "status": "completed"
    })

    pending = db.booked_rides.count_documents({
        "rider_id": rider_id,
        "status": "upcoming"
    })

    cancelled = db.booked_rides.count_documents({
        "rider_id": rider_id,
        "status": "cancelled"
    })

    return jsonify({
        "labels": ["Completed", "Pending", "Cancelled"],
        "values": [completed, pending, cancelled]
    })


# Driver Dashboard
@app.route("/driver/dashboard")
def driver_dashboard():

    if session.get("role") != "driver":
        return "Access Denied"

    update_ride_status()
    driver_id = session["user_id"]
    
    # Get all rides of this driver
    rides = list(db.booked_rides.find({
        "driver_id": driver_id
    }))

    total_co2 = round(sum(r.get("co2_saved", 0) for r in rides), 2)
    total_fuel = round(sum(r.get("fuel_used", 0) for r in rides), 2)
    total_trees = sum(r.get("trees_saved", 0) for r in rides)
    eco_score = sum(r.get("eco_score", 0) for r in rides)

    # Upcoming rides
    bookings = list(db.booked_rides.find({
        "driver_id": driver_id
    }))

    return render_template(
    "driver_dashboard.html",
    name=session.get("name"),
    total_co2=total_co2,
    total_fuel=total_fuel,
    total_trees=total_trees,
    eco_score=eco_score,     
    bookings=bookings
)

# Get ride status data for the driver dashboard
@app.route("/driver-distribution")
def driver_distribution():

    if session.get("role") != "driver":
        return jsonify({"labels": [], "values": []})

    driver_id = session["user_id"]

    completed = db.booked_rides.count_documents({
        "driver_id": driver_id,
        "status": "completed"
    })

    pending = db.booked_rides.count_documents({
        "driver_id": driver_id,
        "status": "upcoming"
    })

    cancelled = db.booked_rides.count_documents({
        "driver_id": driver_id,
        "status": "cancelled"
    })

    return jsonify({
        "labels": ["Completed", "Pending", "Cancelled"],
        "values": [completed, pending, cancelled]
    })

# Get fuel savings data for shared rides vs individual rides
@app.route("/driver-emission-data")
def driver_emission_data():

    if session.get("role") != "driver":
        return jsonify({"labels": [], "values": []})

    driver_id = session["user_id"]
    
    driver_bookings = list(db.booked_rides.find({
        "driver_id": driver_id
    }))

    ride_map = {}

    for r in driver_bookings:
        ride_id = r.get("ride_id")

        if not ride_id:
            continue  

        if ride_id not in ride_map:
            ride_map[ride_id] = {
                "fuel": r.get("fuel_used", 0),
                "people": 0
            }

        ride_map[ride_id]["people"] += r.get("people", 0)

    normal_total = 0
    shared_total = 0

    for ride in ride_map.values():
        fuel = ride["fuel"]
        people = ride["people"]

        if people == 0:
            continue  

        normal_total += fuel * people   
        shared_total += fuel         

    return jsonify({
        "labels": ["Without Sharing", "With Sharing"],
        "values": [
            round(normal_total, 2),
            round(shared_total, 2)
        ]
    })

# Get driver's CO₂ savings progress over completed rides
@app.route("/driver-co2-data")
def driver_co2_data():

    if session.get("role") != "driver":
        return jsonify({"months": [], "values": []})

    driver_id = session["user_id"]

    rides = list(db.booked_rides.find({
        "driver_id": driver_id
    }).sort("date", 1))

    labels = []
    values = []
    cumulative = 0

    for r in rides:
        co2 = r.get("co2_saved", 0)
        cumulative += co2

        label = f"{r.get('date', '')} {r.get('time', '')}"

        labels.append(label)
        values.append(round(cumulative, 2))

    return jsonify({
        "months": labels,
        "values": values
    })

# Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return "Access Denied"
    
    search = request.args.get("search", "")
    status_filter = request.args.get("status", "")

    # Main Stats
    total_rides = db.booked_rides.count_documents({})

    active_drivers = len(
        db.driver_rides.distinct("driver_id")
    )

    active_users = len(
        db.booked_rides.distinct("rider_id")
    )

    # Get all rides
    all_rides = list(db.booked_rides.find())

    total_fuel = round(
        sum(r.get("fuel_used", 0) for r in all_rides),
        2
    )

    total_points = sum(
        r.get("eco_score", 0)
        for r in all_rides
    )

    total_co2 = round(
        sum(r.get("co2_saved", 0) for r in all_rides),
        2
    )

    if total_rides > 0:
        eco_score = min(100, int(total_points / total_rides))
    else:
        eco_score = 0

    total_revenue = round(
        sum(r.get("fare", 0) for r in all_rides),
        2
    )

    total_revenue = "{:,.2f}".format(
        total_revenue
    )

    # Platform Overview
    completed_rides = db.booked_rides.count_documents({
        "status": "completed"
    })

    upcoming_rides = db.booked_rides.count_documents({
        "status": "upcoming"
    })

    cancelled_rides = db.booked_rides.count_documents({
        "status": "cancelled"
    })

    total_users = db.users.count_documents({})

    total_drivers = len(
        db.driver_rides.distinct("driver_id")
    )

    total_riders = len(
        db.booked_rides.distinct("rider_id")
    )

    # Recent Rides
    ride_query = {}

    if status_filter:
        ride_query["status"] = status_filter

    rides = list(
        db.booked_rides.find(ride_query)
        .sort("_id", -1)
        .limit(20)
    )

    for r in rides:
        try:
            rider = db.users.find_one({
                "_id": ObjectId(
                    r.get("rider_id")
                )
            })

            r["rider_name"] = (
                rider.get("name", "Unknown")
                if rider else "Unknown"
            )

        except:
            r["rider_name"] = "Unknown"

        try:
            driver_ride = db.driver_rides.find_one({
                "driver_id": r.get("driver_id")
            })

            if driver_ride:
                driver = db.users.find_one({
                    "_id": ObjectId(
                        driver_ride.get("driver_id")
                    )
                })

                r["driver_name"] = (
                    driver.get("name", "Unknown")
                    if driver else "Unknown"
                )

                r["vehicle"] = driver_ride.get(
                    "vehicle_info",
                    "N/A"
                )

            else:
                r["driver_name"] = "Not Assigned"
                r["vehicle"] = "N/A"

        except:
            r["driver_name"] = "Unknown"
            r["vehicle"] = "N/A"

    # Top Eco Rider
    top_eco_rider = "No Data"
    top_eco_score = 0

    rider_stats = {}

    for ride in all_rides:
        rider_id = ride.get("rider_id")

        rider_stats[rider_id] = (
            rider_stats.get(rider_id, 0)
            + ride.get("co2_saved", 0)
        )

    if rider_stats:
        best_rider_id = max(
            rider_stats,
            key=rider_stats.get
        )

        try:
            rider = db.users.find_one({
                "_id": ObjectId(best_rider_id)
            })

            if rider:
                top_eco_rider = rider.get(
                    "name",
                    "No Data"
                )

                top_eco_score = round(
                    rider_stats[best_rider_id],
                    2
                )
        except:
            pass

    # Top Driver
    top_driver = "No Data"
    top_driver_rides = 0

    driver_stats = {}

    for ride in all_rides:
        driver_id = ride.get("driver_id")

        driver_stats[driver_id] = (
            driver_stats.get(driver_id, 0)
            + 1
        )

    if driver_stats:
        best_driver_id = max(
            driver_stats,
            key=driver_stats.get
        )

        try:
            driver = db.users.find_one({
                "_id": ObjectId(best_driver_id)
            })

            if driver:
                top_driver = driver.get(
                    "name",
                    "No Data"
                )

                top_driver_rides = driver_stats[
                    best_driver_id
                ]
        except:
            pass

    # User Management
    if search:
        users = list(
            db.users.find({
                "$or": [
                    {
                        "name": {
                            "$regex": search,
                            "$options": "i"
                        }
                    },
                    {
                        "email": {
                            "$regex": search,
                            "$options": "i"
                        }
                    }
                ]
            })
        )

    else:
        users = list(
            db.users.find()
        )
        
    for user in users:
        user["booking_count"] = db.booked_rides.count_documents({
            "rider_id": str(user["_id"])
        })

    # Driver Management
    drivers = []

    driver_ids = db.driver_rides.distinct(
        "driver_id"
    )

    for driver_id in driver_ids:
        try:
            driver = db.users.find_one({
                "_id": ObjectId(driver_id)
            })

            if driver:
                driver["ride_count"] = db.booked_rides.count_documents({
                    "driver_id": str(driver["_id"])
                })

                drivers.append(driver)
        except:
            pass

    # Recent Registrations
    recent_users = list(
        db.users.find()
        .sort("_id", -1)
        .limit(5)
    )

    # Recent Driver Listings
    recent_driver_rides = list(
        db.driver_rides.find()
        .sort("_id", -1)
        .limit(5)
    )

    return render_template(
        "admin.html",

        name=session.get("name"),

        total_rides=total_rides,
        active_drivers=active_drivers,
        active_users=active_users,

        total_revenue=total_revenue,
        total_co2=total_co2,
        total_fuel=total_fuel,
        total_points=total_points,
        eco_score=eco_score,

        rides=rides,
        users=users,
        drivers=drivers,

        completed_rides=completed_rides,
        upcoming_rides=upcoming_rides,
        cancelled_rides=cancelled_rides,

        total_users=total_users,
        total_drivers=total_drivers,
        total_riders=total_riders,

        top_eco_rider=top_eco_rider,
        top_eco_score=top_eco_score,

        top_driver=top_driver,
        top_driver_rides=top_driver_rides,

        recent_users=recent_users,
        recent_driver_rides=recent_driver_rides
    )

#Book ride
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

        rider_time = datetime.strptime(time, "%H:%M")

        start_lat, start_lon = get_coordinates(start)
        end_lat, end_lon = get_coordinates(end)

        if not start_lat or not end_lat:
            return "Invalid location entered"

        distance = get_distance(start_lat, start_lon, end_lat, end_lon)

        if distance == 0:
            return "Unable to calculate distance"

        driver_rides = list(db.driver_rides.find({
            "date": date,
            "available_seats": {"$gte": people}
        }))

        ride = None

        for d in driver_rides:
            if isinstance(d["time"], str):
                driver_time = datetime.strptime(d["time"], "%H:%M")
            else:
                driver_time = d["time"]

            time_difference = abs((driver_time - rider_time).total_seconds())

            if time_difference <= 300:
                driver_start_lat, driver_start_lon = get_coordinates(d["start_location"])
                driver_end_lat, driver_end_lon = get_coordinates(d["end_location"])

                route_url = f"http://router.project-osrm.org/route/v1/driving/{driver_start_lon},{driver_start_lat};{driver_end_lon},{driver_end_lat}?overview=full&geometries=geojson"
                route_response = requests.get(route_url)
                route_data = route_response.json()

                if not route_data.get("routes"):
                    continue

                route_coords = route_data["routes"][0]["geometry"]["coordinates"]

                start_on_route = point_near_route(start_lat, start_lon, route_coords)
                end_on_route = point_near_route(end_lat, end_lon, route_coords)

                if start_on_route and end_on_route:
                    ride = d
                    break

        if not ride:
            return render_template("sorry.html")

        driver = db.users.find_one({
            "_id": ObjectId(ride["driver_id"])
        })

        # 🔹 Calculate total passengers
        existing_bookings = list(db.booked_rides.find({
            "ride_id": str(ride["_id"])
        }))
        existing_people = sum(b.get("people", 0) for b in existing_bookings)
        total_people = existing_people + people

        ride_details = calculate_ride_details(distance, total_people)

        fare = ride_details["fare_per_rider"]
        co2_saved = ride_details["co2_saved"]
        trees_saved = ride_details["trees_saved"]
        eco_score = ride_details["eco_score"]
        fuel_cost = ride_details["fuel_cost"]
        driver_profit = ride_details["driver_profit"]
        fuel_used = ride_details["fuel_used"]

        db.booked_rides.insert_one({
            "ride_id": str(ride["_id"]),
            "driver_id": str(ride["driver_id"]),
            "rider_id": session["user_id"],
            "driver_name": driver["name"] if driver else "N/A",
            "driver_phone": driver["phone"] if driver else "N/A",
            "vehicle_number": ride.get("vehicle_info", "N/A"),
            "start_location": start,
            "end_location": end,
            "distance_km": round(distance, 2),
            "people": people,
            "date": date,
            "time": time,
            "fare": fare,
            "fuel_used": fuel_used,
            "fuel_cost": fuel_cost,
            "driver_profit": driver_profit,
            "co2_saved": co2_saved,
            "trees_saved": trees_saved,
            "eco_score": eco_score,
            "status": "upcoming"
        })

        # Update eco score for ALL riders in this ride
        all_bookings = list(db.booked_rides.find({
            "ride_id": str(ride["_id"])
        }))
        total_people_updated = sum(b.get("people", 0) for b in all_bookings)

        for b in all_bookings:
            updated_details = calculate_ride_details(distance, total_people_updated)
            db.booked_rides.update_one(
                {"_id": b["_id"]},
                {
                    "$set": {
                        "co2_saved": updated_details["co2_saved"],
                        "trees_saved": updated_details["trees_saved"],
                        "eco_score": updated_details["eco_score"]
                    }
                }
            )

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

#Rider-history
@app.route("/rider_history")
def rider_history():
    if session.get("role") != "rider":
        return "Access Denied"
    
    update_ride_status()

    rider_id = session["user_id"]

    rides = list(db.booked_rides.find({
        "rider_id": rider_id
    }))

    for ride in rides:
        if "eco_score" not in ride:
            distance = ride.get("distance_km", 0)
            people = ride.get("people", 1)

            details = calculate_ride_details(distance, people)
            ride["eco_score"] = details["eco_score"]

    print("ALL BOOKINGS:", list(db.booked_rides.find()))
    print("SESSION USER ID:", rider_id)
    print("FILTERED RIDES FOR THIS USER:", rides)
    
    return render_template("rider_history.html", rides=rides)

#driver-history
@app.route("/driver_history")
def driver_history():
    if session.get("role") != "driver":
        return "Access Denied"
    
    update_ride_status()

    driver_id = session["user_id"]

    bookings = list(db.booked_rides.find({
        "driver_id": driver_id
    }))

    for booking in bookings:
        rider = db.users.find_one({
            "_id": ObjectId(booking["rider_id"])
        })

        booking["rider_name"] = rider["name"] if rider else "N/A"
        booking["rider_phone"] = rider["phone"] if rider else "N/A"

    return render_template("driver_history.html", bookings=bookings)


#Line Chart Data
@app.route("/co2-data")
def co2_data():
    if session.get("role") != "rider":
        return jsonify({"months": [], "values": []})

    rider_id = session["user_id"]

    rides = list(db.booked_rides.find({
        "rider_id": rider_id
    }).sort("date", 1))  #

    labels = []
    values = []

    cumulative = 0

    for i, r in enumerate(rides, start=1):
        co2 = r.get("co2_saved", 0)
        cumulative += co2

        labels.append(f"{r.get('date', '')[-2:]} {r.get('time', '')}")  
        values.append(round(cumulative, 2))

    return jsonify({
        "months": labels,
        "values": values
    })

#Bar Chart Data
@app.route("/emission-data")
def emission_data():
    if session.get("role") != "rider":
        return jsonify({"labels": [], "values": []})

    rider_id = session["user_id"]

    #Get rides booked by this user
    user_bookings = list(db.booked_rides.find({
        "rider_id": rider_id
    }))

    # Get all ride_ids user participated in
    ride_ids = [b["ride_id"] for b in user_bookings]

    # Fetch ALL bookings for those rides 
    all_rides = list(db.booked_rides.find({
        "ride_id": {"$in": ride_ids}
    }))

    # Group by ride_id
    ride_map = {}

    for r in all_rides:
        ride_id = r["ride_id"]

        if ride_id not in ride_map:
            ride_map[ride_id] = {
                "fuel": r.get("fuel_used", 0),
                "people": 0
            }

        ride_map[ride_id]["people"] += r.get("people", 0)

    # Calculate totals
    normal_total = 0
    shared_total = 0

    for ride in ride_map.values():
        fuel = ride["fuel"]
        people = ride["people"]

        normal_total += fuel * people
        shared_total += fuel

    return jsonify({
        "labels": ["Without Sharing", "With Sharing"],
        "values": [round(normal_total, 2), round(shared_total, 2)]
    })
  
if __name__ == "__main__":
    app.run(debug=True)