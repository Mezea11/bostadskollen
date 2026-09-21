import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "boprisindikatorn.db"


def get_connection():
    # Se till att datakatalogen finns.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def init_database():
    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                address TEXT,
                latitude REAL,
                longitude REAL,
                municipality TEXT,
                property_type TEXT,
                living_area REAL,
                land_area REAL,
                predicted_price REAL,
                lower_price REAL,
                upper_price REAL,
                model_name TEXT,
                number_rooms INTEGER
            )
        """)

        # Kontrollera om number_rooms redan finns.
        # Detta uppdaterar även databaser som skapades
        # innan kolumnen number_rooms infördes.
        existing_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(predictions)"
            ).fetchall()
        }

        if "number_rooms" not in existing_columns:
            connection.execute("""
                ALTER TABLE predictions
                ADD COLUMN number_rooms INTEGER
            """)

        connection.commit()

    finally:
        connection.close()


def log_prediction(
    address,
    latitude,
    longitude,
    municipality,
    property_type,
    living_area,
    land_area,
    predicted_price,
    lower_price,
    upper_price,
    model_name,
    number_rooms=None,
):
    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO predictions (
                timestamp,
                address,
                latitude,
                longitude,
                municipality,
                property_type,
                living_area,
                land_area,
                predicted_price,
                lower_price,
                upper_price,
                model_name,
                number_rooms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(ZoneInfo("Europe/Stockholm")).replace(tzinfo=None).isoformat(),
                address,
                latitude,
                longitude,
                municipality,
                property_type,
                living_area,
                land_area,
                predicted_price,
                lower_price,
                upper_price,
                model_name,
                number_rooms,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def get_predictions(limit=100):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                timestamp,
                address,
                latitude,
                longitude,
                municipality,
                property_type,
                living_area,
                land_area,
                predicted_price,
                lower_price,
                upper_price,
                model_name,
                number_rooms
            FROM predictions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    finally:
        connection.close()

    columns = [
        "id",
        "timestamp",
        "address",
        "latitude",
        "longitude",
        "municipality",
        "property_type",
        "living_area",
        "land_area",
        "predicted_price",
        "lower_price",
        "upper_price",
        "model_name",
        "number_rooms",
    ]

    return rows, columns