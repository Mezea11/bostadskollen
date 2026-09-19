import sqlite3
from pathlib import Path
from datetime import datetime


ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "boprisindikatorn.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_database():
    connection = get_connection()

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
            model_name TEXT
        )
    """)

    connection.commit()
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
):
    connection = get_connection()

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
            model_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(),
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
        ),
    )

    connection.commit()
    connection.close()


def get_predictions(limit=100):
    connection = get_connection()

    rows = connection.execute("""
        SELECT *
        FROM predictions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

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
    ]

    connection.close()

    return rows, columns