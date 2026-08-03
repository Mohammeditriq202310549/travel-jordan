from sqlalchemy import select, or_, and_
from app.db import engine
from app.models import places


def search_places(search_term=None, place_type=None, country=None, min_rating=None):
    """
    Search and filter places in the database.
    - search_term: Matches keyword in name, location, or type (case-insensitive)
    - place_type: Exact match for type (e.g. 'Historical', 'Nature')
    - country: Exact match for country (e.g. 'Jordan')
    - min_rating: Minimum rating cutoff (e.g. 4.5)
    """
    stmt = select(places)
    conditions = []

    if search_term and search_term.strip():
        keyword = f"%{search_term.strip()}%"
        conditions.append(
            or_(
                places.c.name.ilike(keyword),
                places.c.location.ilike(keyword),
                places.c.type.ilike(keyword),
            )
        )

    if place_type:
        conditions.append(places.c.type == place_type)

    if country:
        conditions.append(places.c.country == country)

    if min_rating is not None:
        conditions.append(places.c.rating >= min_rating)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    with engine.connect() as conn:
        result = conn.execute(stmt)
        return [dict(row._mapping) for row in result]

