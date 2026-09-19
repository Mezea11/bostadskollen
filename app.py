from pathlib import Path
import streamlit as st
from src.database import get_predictions
import time

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Boprisindikatorn",
    page_icon="🏠"
)

st.markdown(
    """
    <style>
        header[data-testid="stHeader"] {
            display: none;
        }

        div[data-testid="stMainBlockContainer"] {
            padding-top: 0 !important;
        }
        div[data-testid="stSidebarHeader"] {
            display: none;
        }
        [data-testid="stDivider"] {
            margin-top: 0px;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

pages = [
    st.Page(
        "pages/0_App.py",
        title="App",
        icon="🏠"
    ),
    st.Page(
        "pages/1_Geografi.py",
        title="Geografi",
        icon="🌍"
    ),
    st.Page(
        "pages/2_Boarea.py",
        title="Boarea",
        icon="📐"
    ),
    st.Page(
        "pages/3_Modelljamforelse.py",
        title="Modelljämförelse",
        icon="📊"
    ),
    st.Page(
        "pages/4_Statistik.py", 
        title="Statistik", 
        icon="📈"
    )
]

pg = st.navigation(
    pages,
    position="hidden"
)



# =========================
# NY PREDIKTION - SIDOMENY
# =========================

@st.fragment(run_every="1s")
def prediction_notification():

    rows, columns = get_predictions(1)

    latest_prediction = None

    if rows:
        latest_prediction = dict(
            zip(columns, rows[0])
        )

    latest_id = (
        latest_prediction["id"]
        if latest_prediction
        else None
    )

    # Första kontrollen:
    # Spara aktuell prediktion som utgångsläge.
    # Visa inte en gammal prediktion som ny vid uppstart.
    if "notification_last_id" not in st.session_state:

        st.session_state.notification_last_id = latest_id
        st.session_state.new_prediction = None

    # Ny prediktion har registrerats.
    elif latest_id != st.session_state.notification_last_id:

        st.session_state.notification_last_id = latest_id

        st.session_state.new_prediction = latest_prediction

        # Spara när notisen ska börja visas
        st.session_state.notification_time = time.monotonic()

    prediction = st.session_state.get("new_prediction")

    # Visa ingenting om det inte finns någon ny prediktion.
    if not prediction:
        return

    # Dölj notisen efter 5 sekunder.
    notification_time = st.session_state.get("notification_time")

    if notification_time is None:
        return

    if time.monotonic() - notification_time >= 5:
        st.session_state.new_prediction = None
        st.session_state.notification_time = None
        return

    # =========================
    # FORMATERING
    # =========================

    municipality = (
        prediction.get("municipality")
        or "Okänd kommun"
    )

    rooms = prediction.get("number_rooms")

    if rooms is not None:
        rooms_text = f"{rooms:.0f} rum"
    else:
        rooms_text = "Antal rum saknas"

    living_area = prediction.get("living_area")

    if living_area is not None:
        area_text = f"{living_area:.0f} m²"
    else:
        area_text = "Boarea saknas"

    property_types = {
        "APARTMENT": "Lägenhet",
        "HOUSE": "Villa",
        "ROW_HOUSE": "Radhus",
    }

    property_type = property_types.get(
        prediction.get("property_type"),
        prediction.get("property_type") or "Bostad"
    )

    price = prediction.get("predicted_price")

    if price is not None:
        price_text = (
            f"{price:,.0f} kr".replace(",", " ")
        )
    else:
        price_text = "Pris saknas"

    lower_price = prediction.get("lower_price")
    upper_price = prediction.get("upper_price")

    if lower_price is not None and upper_price is not None:
        interval_text = (
            f"{lower_price:,.0f}–{upper_price:,.0f} kr"
            .replace(",", " ")
        )
    else:
        interval_text = None

    # =========================
    # VISA NOTIS
    # =========================

    with st.container(border=True):

        st.markdown("### 🟢 Ny uppskattning!")

        st.markdown(f"**{municipality}**")

        st.caption(
            f"{property_type} · {rooms_text} · {area_text}"
        )

        st.markdown("**Uppskattat pris**")

        st.markdown(
            f"## {price_text}"
        )

        if interval_text:
            st.caption(
                f"Prisintervall: {interval_text}"
            )

        st.caption("Senaste registrerade uppskattningen")


with st.sidebar:
    st.title("🏠 Boprisindikatorn")
    st.write(
        "Uppskatta en bostads utgångspris med en modell tränad i notebooken."
    )

    st.divider()

    st.page_link(
        "pages/0_App.py",
        label="App",
        icon="🏠"
    )
    st.page_link(
        "pages/1_Geografi.py",
        label="Geografi",
        icon="🌍"
    )
    st.page_link(
        "pages/2_Boarea.py",
        label="Boarea",
        icon="📐"
    )
    st.page_link(
        "pages/3_Modelljamforelse.py",
        label="Modelljämförelse",
        icon="📊"
    )
    st.page_link(
        "pages/4_Statistik.py",
        label="Statistik",
        icon="📈"
    )

    prediction_notification()

pg.run()