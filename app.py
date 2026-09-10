from pathlib import Path

import pandas as pd
import streamlit as st

from src.model_loader import load_model_bundle
from src.preprocessing import prepare_input

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "SwedenHousingPrices.csv"
MODELS_DIR = ROOT / "models"

st.set_page_config(page_title="Bostadskollen", page_icon="🏠")


@st.cache_data
def get_municipalities() -> list[str]:
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
    return sorted(df["location"].str.split(", ").str[1].dropna().unique())


@st.cache_resource
def load_bundle(path: Path) -> dict:
    return load_model_bundle(path)


st.title("🏠 Bostadskollen")
st.write("Uppskatta en bostads utgångspris med en modell tränad i notebooken.")

model_files = sorted(MODELS_DIR.glob("*.joblib"))

if not model_files:
    st.info("Spara först en tränad modell från notebooken i mappen `models/`.")
    st.stop()

selected_file = st.selectbox(
    "Modell",
    model_files,
    format_func=lambda path: path.stem.replace("_", " ").title(),
)

bundle = load_bundle(selected_file)
model = bundle["model"]
feature_columns = bundle["feature_columns"]

with st.form("prediction_form"):
    typology = st.selectbox("Bostadstyp", ["APARTMENT", "HOUSE", "ROW_HOUSE"])
    municipality = st.selectbox("Kommun", get_municipalities())
    living_area = st.number_input("Boarea (m²)", min_value=1.0, value=80.0)
    land_area = st.number_input("Tomtarea (m²)", min_value=0.0, value=0.0)
    number_rooms = st.number_input(
        "Antal rum", min_value=1.0, value=3.0, step=0.5)
    latitude = st.number_input("Latitud", value=55.605)
    longitude = st.number_input("Longitud", value=13.003)
    month = st.slider("Månad", 1, 12, 6)
    submitted = st.form_submit_button("Beräkna pris")

if submitted:
    user_input = {
        "typology": typology,
        "municipality": municipality,
        "land_area_sqm": land_area,
        "living_area_sqm": living_area,
        "number_rooms": number_rooms,
        "latitude": latitude,
        "longitude": longitude,
        "month": month,
    }

    model_input = prepare_input(user_input, feature_columns)
    prediction = float(model.predict(model_input)[0])

    st.success(
        f"Uppskattat utgångspris: {prediction:,.0f} kr".replace(",", " "))
