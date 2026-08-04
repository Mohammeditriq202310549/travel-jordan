import os
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db import engine
from models import places
from main import load_places_from_json
from search import search_places
from auth import register_user, login_user
from favorites import add_favorite, remove_favorite, get_user_favorites

# Path for error log file
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
LOG_FILE_PATH = os.path.join(LOG_DIR, "errors.log")


def ensure_log_dir_exists():
    """Creates logs directory if it does not exist."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def log_exception(error, context="General"):
    """
    Logs exceptions into app/logs/errors.log with formatted timestamps and stack trace.
    Returns the formatted log string.
    """
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_type = type(error).__name__
    error_msg = str(error)
    stack_trace = traceback.format_exc()

    log_entry = (
        f"==================================================\n"
        f"TIMESTAMP  : [{timestamp}]\n"
        f"CONTEXT    : [{context}]\n"
        f"ERROR TYPE : {error_type}\n"
        f"MESSAGE    : {error_msg}\n"
        f"TRACEBACK  :\n{stack_trace}"
        f"==================================================\n\n"
    )

    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print("Failed to write to error log file:", e)

    return log_entry


# Custom Application Exception Classes
class AppBaseException(Exception):
    """Base class for custom application exceptions."""
    def __init__(self, message="An application error occurred.", status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DatabaseException(AppBaseException):
    """Raised when database query or connection fails."""
    def __init__(self, message="Database operation failed.", status_code=500):
        super().__init__(message, status_code)


class AuthenticationException(AppBaseException):
    """Raised when user authentication or permission fails."""
    def __init__(self, message="Authentication failed.", status_code=401):
        super().__init__(message, status_code)


class ValidationException(AppBaseException):
    """Raised when user input validation fails."""
    def __init__(self, message="Invalid input data.", status_code=400):
        super().__init__(message, status_code)


class ResourceNotFoundException(AppBaseException):
    """Raised when a requested resource is not found."""
    def __init__(self, message="Resource not found.", status_code=404):
        super().__init__(message, status_code)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "super-secret-jordan-travel-key-12345"


@app.before_request
def ensure_database_seeded():
    try:
        load_places_from_json()
    except Exception as e:
        log_exception(e, context="DatabaseSeeding")


# Global Exception Handlers
@app.errorhandler(AppBaseException)
def handle_app_exception(error):
    log_exception(error, context=request.path)
    return jsonify({"success": False, "message": error.message}), error.status_code


@app.errorhandler(Exception)
def handle_generic_exception(error):
    log_exception(error, context=request.path)
    return jsonify({"success": False, "message": "An unexpected error occurred. Please try again later."}), 500


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
