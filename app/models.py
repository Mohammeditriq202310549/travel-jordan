from sqlalchemy import (
    MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint, func
)

metadata = MetaData()

# 1. Users Table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("email", String(120), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
)

# 2. Places Table (Includes column 'countries')
places = Table(
    "places",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(150), nullable=False),
    Column("location", String(255)),
    Column("type", String(100)),
    Column("rating", Float),
    Column("image_url", String(1000)),
    Column("country", String(100)),  
)

# 3. Favorites Table
favorites = Table(
    "favorites",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("place_id", Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime, server_default=func.now()),
    UniqueConstraint("user_id", "place_id", name="uq_user_place"),
)
