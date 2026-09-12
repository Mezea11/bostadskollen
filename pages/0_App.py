from pathlib import Path

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.model_loader import load_model_bundle
from src.preprocessing import prepare_input


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "SwedenHousingPrices.csv"
MODELS_DIR = ROOT / "models"


@st.cache_data
def get_municipalities() -> list[str]:
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    return sorted(
        df["location"]
        .str.split(", ")
        .str[1]
        .dropna()
        .unique()
    )


@st.cache_resource
def load_bundle(path: Path) -> dict:
    return load_model_bundle(path)


# =========================
# MODELLER
# =========================

model_paths = {
    "APARTMENT": MODELS_DIR / "apartment_random_forest.joblib",
    "HOUSE": MODELS_DIR / "house_random_forest.joblib",
    "ROW_HOUSE": MODELS_DIR / "row_house_random_forest.joblib",
}


# Ladda alla modeller när appen startar
models = {
    typology: load_bundle(path)
    for typology, path in model_paths.items()
}

# MAE för respektive modell
mae_values = {
    "APARTMENT": 451436,
    "HOUSE": 1125795,
    "ROW_HOUSE": 758833,
}


# =========================
# STANDARDKOORDINATER
# =========================

if "latitude" not in st.session_state:
    st.session_state.latitude = 55.610181

if "longitude" not in st.session_state:
    st.session_state.longitude = 12.977890


# =========================
# KOLUMN-LAYOUT
# =========================

form_column, map_column = st.columns([1, 1])


# =========================
# FORMULÄR
# =========================

with form_column:

    with st.form("prediction_form"):

        typology = st.selectbox(
            "Bostadstyp",
            ["APARTMENT", "HOUSE", "ROW_HOUSE"]
        )

        municipality = st.selectbox(
            "Kommun",
            get_municipalities()
        )

        living_area = st.number_input(
            "Boarea (m²)",
            min_value=1,
            value=80,
            step=1
        )

        land_area = st.number_input(
            "Tomtarea (m²)",
            min_value=0,
            value=0,
            step=10
        )

        number_rooms = st.number_input(
            "Antal rum",
            min_value=1,
            value=3,
            step=1
        )

        submitted = st.form_submit_button(
            "Beräkna pris"
        )


# =========================
# KARTA
# =========================

with map_column:

    m = folium.Map(
        location=[
            st.session_state.latitude,
            st.session_state.longitude
        ],
        zoom_start=5,
        min_zoom=4,
        max_bounds=True,
        max_bounds_viscosity=1.0
    )

    m.fit_bounds([
        [55.0, 10.5],
        [69.1, 24.2]
    ])

    # Markör på vald position
    folium.Marker(
        location=[
            st.session_state.latitude,
            st.session_state.longitude
        ],
        tooltip="Vald position"
    ).add_to(m)

    map_data = st_folium(
        m,
        width=250,
        height=470,
        returned_objects=["last_clicked"]
    )

    if map_data["last_clicked"]:
        st.session_state.latitude = map_data["last_clicked"]["lat"]
        st.session_state.longitude = map_data["last_clicked"]["lng"]



# =========================
# PREDIKTION
# =========================

if submitted:

    # Välj redan laddad modell
    bundle = models[typology]

    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    # Samla användarens input
    user_input = {
        "typology": typology,
        "municipality": municipality,
        "land_area_sqm": land_area,
        "living_area_sqm": living_area,
        "number_rooms": number_rooms,
        "latitude": st.session_state.latitude,
        "longitude": st.session_state.longitude,
    }

    # Förbered input för modellen
    model_input = prepare_input(
        user_input,
        feature_columns
    )

    # Gör prediktion
    prediction = float(
        model.predict(model_input)[0]
    )

    # Hämta MAE för vald modell
    mae = mae_values[typology]

    # Beräkna prisintervall
    lower_price = max(0, prediction - mae)
    upper_price = prediction + mae

    # Visa resultat
    st.markdown(
        f"""
        <div style="font-size: 32px; font-weight: bold;">
            🏠 Uppskattat utgångspris
        </div>

        <div style="font-size: 36px; font-weight: bold; margin-top: 8px;">
            {prediction:,.0f} kr
        </div>

        <div style="font-size: 20px; margin-top: 16px;">
            Ungefärligt intervall:
        </div>

        <div style="font-size: 24px; font-weight: bold;">
            {lower_price:,.0f} – {upper_price:,.0f} kr
        </div>

        <div style="font-size: 16px; margin-top: 8px;">
            Modellens genomsnittliga fel: ± {mae:,.0f} kr
        </div>
        """.replace(",", " "),
        unsafe_allow_html=True
    )