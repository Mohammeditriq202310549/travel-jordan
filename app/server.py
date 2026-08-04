import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import engine
from models import places
from main import load_places_from_json
from search import search_places
from auth import register_user, login_user
from favorites import add_favorite, remove_favorite, get_user_favorites

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "super-secret-jordan-travel-key-12345"


@app.before_request
def ensure_database_seeded():
    try:
        load_places_from_json()
    except Exception as e:
        print("Database seed check:", e)


# View Routes (Renders Individual Templates)
@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("view_search"))
    return redirect(url_for("view_login"))


@app.route("/login")
def view_login():
    if session.get("user"):
        return redirect(url_for("view_search"))
    return render_template("login.html")


@app.route("/register")
def view_register():
    if session.get("user"):
        return redirect(url_for("view_search"))
    return render_template("register.html")


@app.route("/search")
def view_search():
    return render_template("search.html")


@app.route("/profile")
def view_profile():
    return render_template("profile.html")


# API Routes
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required."}), 400

    result = register_user(name, email, password)
    return jsonify(result)


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    result = login_user(email, password)
    if result["success"]:
        session["user"] = result["user"]
    return jsonify(result)


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"success": True, "message": "Logged out successfully."})


@app.route("/api/me", methods=["GET"])
def api_me():
    user = session.get("user")
    if user:
        return jsonify({"logged_in": True, "user": user})
    return jsonify({"logged_in": False, "user": None})


@app.route("/api/places", methods=["GET"])
def api_get_places():
    search_term = request.args.get("search", "")
    place_type = request.args.get("type", "")
    location = request.args.get("location", "")
    min_rating = request.args.get("min_rating", type=float)

    results = search_places(
        search_term=search_term if search_term else None,
        place_type=place_type if place_type and place_type != "All" else None,
        country=None,
        min_rating=min_rating
    )

    if location and location != "All":
        results = [p for p in results if p.get("location") and location.lower() in p["location"].lower()]

    user = session.get("user")
    if user:
        user_favs = get_user_favorites(user["id"])
        fav_ids = {f["id"] for f in user_favs}
        for r in results:
            r["is_favorite"] = r["id"] in fav_ids
    else:
        for r in results:
            r["is_favorite"] = False

    return jsonify(results)


@app.route("/api/favorites", methods=["GET"])
def api_get_favorites():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    favs = get_user_favorites(user["id"])
    return jsonify(favs)


@app.route("/api/favorites/toggle", methods=["POST"])
def api_toggle_favorite():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "message": "Please login to save favorites."}), 401 #Unauthorized

    data = request.get_json() or {}
    place_id = data.get("place_id")

    if not place_id:
        return jsonify({"success": False, "message": "Place ID required."}), 400  # Bad Request


    user_favs = get_user_favorites(user["id"])
    fav_ids = {f["id"] for f in user_favs}

    if place_id in fav_ids:
        res = remove_favorite(user["id"], place_id)
        res["action"] = "removed"
    else:
        res = add_favorite(user["id"], place_id)
        res["action"] = "added"

    return jsonify(res)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
