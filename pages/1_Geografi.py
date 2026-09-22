import json
from pathlib import Path

import plotly.express as px
import streamlit as st

from src.geography import compare_municipalities
from src.geography import get_available_municipalities
from src.geography import load_municipality_profiles
from src.model_loader import load_model_bundle


# =========================
# SÖKVÄGAR
# =========================

ROOT = Path(__file__).resolve().parent.parent

PROFILES_PATH = ROOT / "data" / "municipality_profiles.csv"
METRICS_PATH = ROOT / "data" / "geography_metrics.json"
MODELS_DIR = ROOT / "models"


# =========================
# INSTÄLLNINGAR
# =========================

TYPOLOGY_LABELS = {
    "APARTMENT": "Lägenhet",
    "HOUSE": "Villa",
    "ROW_HOUSE": "Radhus",
}

MODEL_PATHS = {
    "APARTMENT": MODELS_DIR / "apartment_model.joblib",
    "HOUSE": MODELS_DIR / "global_model.joblib",
    "ROW_HOUSE": MODELS_DIR / "global_model.joblib",
}


# =========================
# LADDA DATA OCH MODELLER
# =========================

@st.cache_data
def load_profiles():
    """Ladda kommunprofiler med minst tio observationer."""

    return load_municipality_profiles(PROFILES_PATH)


@st.cache_data
def load_geography_metrics():
    """Ladda resultatet från geografihypotesen."""

    with METRICS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_resource
def load_bundle(path: Path):
    """Ladda och cacha en sparad modellbundle."""

    return load_model_bundle(path)


def format_price(value: float) -> str:
    """Formatera ett pris med svenska tusentalsmellanrum."""

    return f"{value:,.0f} kr".replace(",", " ")


def default_municipalities(
    available_municipalities: list[str],
) -> list[str]:
    """Välj begripliga standardkommuner om de finns i datan."""

    preferred = [
        "Malmö kommun",
        "Lunds kommun",
        "Ystads kommun",
    ]

    selected = [
        municipality
        for municipality in preferred
        if municipality in available_municipalities
    ]

    for municipality in available_municipalities:
        if len(selected) >= 3:
            break

        if municipality not in selected:
            selected.append(municipality)

    return selected


# =========================
# SIDANS RUBRIK
# =========================

st.title("Geografisk prisjämförelse")

st.write(
    "Jämför hur modellen värderar samma bostad i olika kommuner. "
    "Bostadens egenskaper hålls oförändrade medan kommunen och "
    "koordinaterna ändras."
)


# =========================
# LADDA UNDERLAG
# =========================

try:
    profiles = load_profiles()
    geography_metrics = load_geography_metrics()

except (FileNotFoundError, ValueError) as error:
    st.error(
        "Geografiunderlaget kunde inte laddas. "
        f"Teknisk information: {error}"
    )
    st.stop()


# =========================
# VISA HYPOTESRESULTAT
# =========================


# =========================
# JÄMFÖRELSEFORMULÄR
# =========================

st.divider()
st.subheader("Jämför samma bostad mellan kommuner")

typology = st.selectbox(
    "Bostadstyp",
    options=list(TYPOLOGY_LABELS),
    format_func=lambda value: TYPOLOGY_LABELS[value],
)

available_municipalities = get_available_municipalities(
    profiles,
    typology,
)

input_column_1, input_column_2, input_column_3 = st.columns(3)

with input_column_1:
    living_area = st.number_input(
        "Boarea (m²)",
        min_value=1,
        value=80,
        step=1,
    )

with input_column_2:
    number_rooms = st.number_input(
        "Antal rum",
        min_value=1,
        value=3,
        step=1,
    )

with input_column_3:
    if typology == "APARTMENT":
        land_area = 0
        st.number_input(
            "Tomtarea (m²)",
            value=0,
            disabled=True,
        )
    else:
        land_area = st.number_input(
            "Tomtarea (m²)",
            min_value=0,
            value=500 if typology == "HOUSE" else 0,
            step=10,
        )

selected_municipalities = st.multiselect(
    "Välj mellan 2 och 5 kommuner",
    options=available_municipalities,
    default=default_municipalities(
        available_municipalities
    ),
    max_selections=5,
    key=f"geography_municipalities_{typology}",
)

compare_button = st.button(
    "Jämför priser",
    type="primary",
)


# =========================
# GÖR OCH VISA JÄMFÖRELSEN
# =========================

if compare_button:
    if len(selected_municipalities) < 2:
        st.warning("Välj minst två kommuner för att jämföra priser.")
        st.stop()

    try:
        bundle = load_bundle(MODEL_PATHS[typology])
        pipeline = bundle["pipeline"]

        results = compare_municipalities(
            pipeline=pipeline,
            profiles=profiles,
            typology=typology,
            municipalities=selected_municipalities,
            living_area_sqm=living_area,
            number_rooms=number_rooms,
            land_area_sqm=land_area,
        )

    except (FileNotFoundError, ValueError) as error:
        st.error(
            "Jämförelsen kunde inte genomföras. "
            f"Teknisk information: {error}"
        )
        st.stop()

    st.subheader("Resultat")

    chart = px.bar(
        results,
        x="municipality",
        y="predicted_price",
        text="predicted_price",
        labels={
            "municipality": "Kommun",
            "predicted_price": "Uppskattat utgångspris",
        },
        color="predicted_price",
        color_continuous_scale="Blues",
    )

    chart.update_traces(
        texttemplate="%{text:,.0f} kr",
        textposition="outside",
    )

    chart.update_layout(
        coloraxis_showscale=False,
        yaxis_tickformat=",.0f",
        xaxis_title=None,
    )

    st.plotly_chart(
        chart,
        use_container_width=True,
    )

    table = results[
        [
            "municipality",
            "predicted_price",
            "difference_sek",
            "difference_percent",
            "observations",
            "median_sqm_price",
        ]
    ].rename(columns={
        "municipality": "Kommun",
        "predicted_price": "Uppskattat pris",
        "difference_sek": "Skillnad från billigast",
        "difference_percent": "Skillnad (%)",
        "observations": "Observationer",
        "median_sqm_price": "Medianpris/m²",
    })

    st.dataframe(
        table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Uppskattat pris": st.column_config.NumberColumn(
                format="%d kr"
            ),
            "Skillnad från billigast": st.column_config.NumberColumn(
                format="%d kr"
            ),
            "Skillnad (%)": st.column_config.NumberColumn(
                format="%.1f %%"
            ),
            "Medianpris/m²": st.column_config.NumberColumn(
                format="%d kr"
            ),
        },
    )

    cheapest = results.iloc[0]
    most_expensive = results.iloc[-1]

    st.info(
        f"{cheapest['municipality']} fick jämförelsens lägsta "
        f"uppskattade pris på {format_price(cheapest['predicted_price'])}. "
        f"{most_expensive['municipality']} uppskattades till "
        f"{format_price(most_expensive['predicted_price'])}, vilket är "
        f"{most_expensive['difference_percent']:.1f} procent högre."
    )


# =========================
# BEGRÄNSNINGAR
# =========================

st.divider()

st.subheader("Resultat från hypotesen")

without_geography = geography_metrics["without_geography"]
with_geography = geography_metrics["with_geography"]
improvement = geography_metrics["rmse_improvement_percent"]

metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

metric_column_1.metric(
    "RMSE utan geografi",
    format_price(without_geography["rmse"]),
)

metric_column_2.metric(
    "RMSE med geografi",
    format_price(with_geography["rmse"]),
)

metric_column_3.metric(
    "Förbättring",
    f"{improvement:.1f} %",
)

st.success(
    "Modellen med kommun och koordinater fick cirka "
    f"{improvement:.1f} procent lägre RMSE. Resultatet ger stöd "
    "för hypotesen att geografi bidrar till modellens "
    "prediktionsförmåga."
)

with st.expander("Metod och begränsningar"):
    st.write(
        "Kommunens mediankoordinater används som en representativ position. "
        "Endast kommunprofiler med minst tio observationer kan väljas."
    )
    st.write(
        "Resultatet visar modellens uppskattning av sambandet mellan "
        "geografi och utgångspris. Det är inte ett bevis på att geografin "
        "ensam orsakar hela prisskillnaden."
    )
    st.write(
        "Modellen saknar bland annat information om bostadens skick, "
        "våningsplan, månadsavgift, skolor, kollektivtrafik och lokal service."
    )
