from src.schemas import HousingInput
from src.model_loader import load_model_bundle
from streamlit_folium import st_folium
import folium
import streamlit as st
import pandas as pd
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "SwedenHousingPrices.csv"
MODELS_DIR = ROOT / "models"


# =========================
# KOMMUNER
# =========================

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


# =========================
# REVERSE GEOCODING
# =========================

@st.cache_data(ttl=86400)
def get_municipality_from_coordinates(
    latitude: float,
    longitude: float
) -> str | None:

    params = urlencode({
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "sv",
        "zoom": 10,
    })

    url = f"https://nominatim.openstreetmap.org/reverse?{params}"

    request = Request(
        url,
        headers={
            "User-Agent": "Bostadskollen/1.0"
        }
    )

    try:
        with urlopen(request, timeout=5) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        address = data.get("address", {})

        municipality = address.get("municipality")

        if municipality:
            return municipality

        return (
            address.get("city")
            or address.get("town")
            or address.get("village")
        )

    except Exception:
        return None


def match_municipality(
    geocoded_municipality: str | None,
    municipalities: list[str]
) -> str | None:

    if not geocoded_municipality:
        return None

    # Exakt match
    if geocoded_municipality in municipalities:
        return geocoded_municipality

    # Normalisera namn
    geocoded_normalized = (
        geocoded_municipality
        .lower()
        .replace(" kommun", "")
        .replace(" stad", "")
        .strip()
    )

    for municipality in municipalities:

        municipality_normalized = (
            municipality
            .lower()
            .replace(" kommun", "")
            .replace(" stad", "")
            .strip()
        )

        if municipality_normalized == geocoded_normalized:
            return municipality

    return None


# =========================
# MODELLER
# =========================

@st.cache_resource
def load_bundle(path: Path) -> dict:
    return load_model_bundle(path)


model_paths = {
    "APARTMENT": MODELS_DIR / "apartment_model.joblib",
    "HOUSE": MODELS_DIR / "global_model.joblib",
    "ROW_HOUSE": MODELS_DIR / "global_model.joblib",
}


# =========================
# STANDARDKOORDINATER
# =========================

if "latitude" not in st.session_state:
    st.session_state.latitude = 55.610181

if "longitude" not in st.session_state:
    st.session_state.longitude = 12.977890


# =========================
# KOMMUNER
# =========================

municipalities = get_municipalities()

if "selected_municipality" not in st.session_state:
    st.session_state.selected_municipality = municipalities[0]


# =========================
# KOLUMN-LAYOUT
# =========================

form_column, map_column = st.columns([1, 1])


# =========================
# FORMULÄR
# =========================

with form_column:

    with st.form("prediction_form"):

        typology_labels = {
            "APARTMENT": "Lägenhet",
            "HOUSE": "Villa",
            "ROW_HOUSE": "Radhus",
        }

        typology = st.selectbox(
            "Bostadstyp",
            list(typology_labels.keys()),
            format_func=lambda x: typology_labels[x]
        )

        municipality_index = municipalities.index(
            st.session_state.selected_municipality
        )

        municipality = st.selectbox(
            "Kommun",
            municipalities,
            index=municipality_index
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


# Spara manuellt vald kommun
st.session_state.selected_municipality = municipality


# =========================
# KARTA
# =========================

with map_column:

    m = folium.Map(
        location=[
            st.session_state.latitude,
            st.session_state.longitude
        ],
        zoom_start=10,
        min_zoom=4,
        max_bounds=True,
        max_bounds_viscosity=1.0
    )

    # Markör på vald position
    folium.Marker(
        location=[
            st.session_state.latitude,
            st.session_state.longitude
        ],
        tooltip="Vald position",
        icon=folium.Icon(icon="home")
    ).add_to(m)

    map_data = st_folium(
        m,
        width=250,
        height=470,
        returned_objects=["last_clicked"]
    )

    # =========================
    # KARTKLICK
    # =========================

    if map_data["last_clicked"]:

        new_latitude = map_data["last_clicked"]["lat"]
        new_longitude = map_data["last_clicked"]["lng"]

        st.session_state.latitude = new_latitude
        st.session_state.longitude = new_longitude

        # Hämta kommun från koordinaterna
        geocoded_municipality = get_municipality_from_coordinates(
            new_latitude,
            new_longitude
        )

        matched_municipality = match_municipality(
            geocoded_municipality,
            municipalities
        )

        if matched_municipality:

            st.session_state.selected_municipality = (
                matched_municipality
            )

            st.rerun()


# =========================
# PREDIKTION
# =========================

if submitted:

    # Ladda den modell som användaren har valt
    bundle = load_bundle(model_paths[typology])

    # Välj pipeline från modellbundle
    pipeline = bundle["pipeline"]

    # Samla användarens input
    housing_input = HousingInput(
        typology=typology,
        municipality=municipality,
        land_area_sqm=land_area,
        living_area_sqm=living_area,
        number_rooms=number_rooms,
        latitude=st.session_state.latitude,
        longitude=st.session_state.longitude,
    )

    # Omvandla Pydantic-modellen till en dictionary
    user_input = housing_input.model_dump()

    # Samma tomtlogik som användes i modellträningen
    user_input["has_land_area"] = int(land_area > 0)

    if typology == "APARTMENT":
        user_input["land_area_sqm"] = None

    if typology == "HOUSE" and land_area < 50:
        user_input["land_area_sqm"] = None

    # Pipelinen tar hand om imputering och one-hot encoding
    model_input = pd.DataFrame([user_input])

    # Gör prediktion
    prediction = float(
        pipeline.predict(model_input)[0]
    )

    # Hämta MAE från samma modell som gjorde prediktionen
    if typology == "APARTMENT":
        mae = float(bundle["metrics"]["mae"])
    else:
        mae = float(
            bundle["metrics_by_segment"][typology]["mae"]
        )

    # Beräkna prisintervall
    lower_price = max(0, prediction - mae)
    upper_price = prediction + mae

    # =========================
    # RESULTAT
    # =========================

    st.html(
        f"""
        <div id="result" style="
            border-radius: 12px;
            padding: 28px;
            margin-top: 25px;
            text-align: center;
            border: 1px solid #dbe2ea;
        ">

            <div style="
                font-size: 22px;
                font-weight: 600;
                margin-bottom: 10px;
            ">
                🏠 Uppskattat utgångspris
            </div>

            <div style="
                font-size: 42px;
                font-weight: 700;
                margin-bottom: 20px;
            ">
                {prediction:,.0f} kr
            </div>

            <div style="
                font-size: 17px;
                margin-bottom: 6px;
            ">
                Ungefärligt prisintervall
            </div>

            <div style="
                font-size: 25px;
                font-weight: 600;
            ">
                {lower_price:,.0f} – {upper_price:,.0f} kr
            </div>

            <div style="
                font-size: 14px;
                margin-top: 14px;
                opacity: 0.7;
            ">
                Modellens genomsnittliga fel: ± {mae:,.0f} kr
            </div>

        </div>

        <script>
            setTimeout(function() {{
                document.getElementById("result").scrollIntoView({{
                    behavior: "smooth",
                    block: "center"
                }});
            }}, 200);
        </script>
        """,
        unsafe_allow_javascript=True
    )
