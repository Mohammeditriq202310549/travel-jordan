from sqlalchemy import select, insert, delete
from app.db import engine
from app.models import favorites, places


def add_favorite(user_id, place_id):
    """
    Adds a place to user's favorites list.
    """
    with engine.connect() as conn:
        existing = conn.execute(
            select(favorites).where(
                favorites.c.user_id == user_id,
                favorites.c.place_id == place_id
            )
        ).fetchone() #one  first match in db  , .fetchall() : grab every single matching row in db  

        if existing:
            return {"success": False, "message": "Place already in favorites."}

        stmt = insert(favorites).values(user_id=user_id, place_id=place_id)
        conn.execute(stmt)
        conn.commit()
        return {"success": True, "message": "Added to favorites!"}


def remove_favorite(user_id, place_id):
    """
    Removes a place from user's favorites list.
    """
    with engine.connect() as conn:
        stmt = delete(favorites).where(
            favorites.c.user_id == user_id,
            favorites.c.place_id == place_id
        )
        result = conn.execute(stmt)
        conn.commit()

        if result.rowcount > 0:
            return {"success": True, "message": "Removed from favorites."}
        return {"success": False, "message": "Favorite not found."}


def get_user_favorites(user_id):
    """
    Retrieves all favorited places for a specific user.
    """
    with engine.connect() as conn:
        stmt = (
            select(places)
            .join(favorites, places.c.id == favorites.c.place_id)
            .where(favorites.c.user_id == user_id)
        )
        result = conn.execute(stmt)
        return [dict(row._mapping) for row in result]
