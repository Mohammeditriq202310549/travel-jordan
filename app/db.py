from sqlalchemy import create_engine

# Database Connection string
DATABASE_URL = "postgresql://postgres:123456@localhost:5432/travel_db"

# Create SQLAlchemy Engine
engine = create_engine(DATABASE_URL, echo=True)
