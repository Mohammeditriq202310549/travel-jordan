import re
from sqlalchemy import select, insert
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import engine
from app.models import users


def validate_password(password):
    """
    Validates password complexity:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    if not re.search(r"[^a-zA-Z0-9]", password):
        return False, "Password must contain at least one special symbol (e.g., !, @, #, $, %). "
    return True, "Password is valid."


def register_user(name, email, password):
    """
    Registers a new user into the database with password validation.
    """
    # 1. Validate password strength
    is_valid, val_msg = validate_password(password)
    if not is_valid:
        return {"success": False, "message": val_msg}

    with engine.connect() as conn:
        # 2. Check if user already exists by email
        existing_user = conn.execute(
            select(users).where(users.c.email == email)
        ).fetchone()

        if existing_user:
            return {"success": False, "message": "Email is already registered."}

        # 3. Hash password securely
        hashed_pw = generate_password_hash(password)

        # 4. Insert new user into database
        stmt = insert(users).values(
            name=name,
            email=email,
            password_hash=hashed_pw
        )
        conn.execute(stmt)
        conn.commit()

        return {"success": True, "message": "User registered successfully!"}


def login_user(email, password):
    """
    Authenticates a user against stored email and hashed password.
    """
    with engine.connect() as conn:
        # 1. Fetch user by email
        user_row = conn.execute(
            select(users).where(users.c.email == email)
        ).fetchone()

        if not user_row:
            return {"success": False, "message": "Invalid email or password."}

        user = dict(user_row._mapping)

        # 2. Verify hashed password
        if not check_password_hash(user["password_hash"], password):
            return {"success": False, "message": "Invalid email or password."}

        # 3. Authentication successful (return user dict without password)
        return {
            "success": True,
            "message": "Login successful!",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }


if __name__ == "__main__":
    # Test password validation rules without inserting into database
    test_passwords = ["Ab1!", "pass1234!", "PASS1234!", "PassWord123", "StrongP@ss123"]
    for pw in test_passwords:
        is_valid, msg = validate_password(pw)
        print(f"Password: {pw:<15} -> Valid: {is_valid:<5} ({msg})")

