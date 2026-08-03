import json
import os
from sqlalchemy import insert, select
from app.db import engine
from app.models import places


def load_places_from_json():
    # 1. Get the path to places.json
    json_path = os.path.join(os.path.dirname(__file__), "places.json")

    # 2. Open and read the JSON file
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # 3. Insert or Update records in PostgreSQL database
    with engine.connect() as conn:
        for item in data:
            query_exist = conn.execute(
                select(places).where(places.c.name == item["name"])
            ).fetchone()

            if not query_exist:
                stmt = insert(places).values(**item)
                conn.execute(stmt)
                print(f"Inserted: {item['name']}")
            else:
                from sqlalchemy import update
                stmt = update(places).where(places.c.name == item["name"]).values(**item)
                conn.execute(stmt)

        conn.commit()


if __name__ == "__main__":
    load_places_from_json()
