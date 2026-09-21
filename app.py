
from pathlib import Path
import html
import textwrap
import time

import streamlit as st
from src.database import get_predictions


ROOT = Path(__file__).resolve().parent


st.set_page_config(
    page_title="Boprisindikatorn",
    page_icon="🏠"
)


# =========================
# CSS
# =========================

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


# =========================
# SIDOR
# =========================

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
# BEVAKNING AV NY PREDIKTION
# =========================
# Fragmentet kontrollerar databasen varje sekund.
# Popupen renderas INTE här, så den byggs inte om
# varje gång fragmentet körs.

@st.fragment(run_every="1s")
def check_for_new_prediction():

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
    # Spara befintlig prediktion som utgångsläge.
    # Visa inte en gammal prediktion vid uppstart.
    if "notification_last_id" not in st.session_state:

        st.session_state.notification_last_id = latest_id
        st.session_state.new_prediction = None
        st.session_state.notification_time = None

    # En ny prediktion har registrerats.
    elif latest_id != st.session_state.notification_last_id:

        st.session_state.notification_last_id = latest_id

        # Om prediktionen skapades i den här sessionen
        # ska ingen popup visas.
        if st.session_state.get("just_created_prediction", False):

            st.session_state.just_created_prediction = False

            st.session_state.new_prediction = None
            st.session_state.notification_time = None

        else:

            st.session_state.new_prediction = latest_prediction
            st.session_state.notification_time = time.monotonic()

        # Kör om appen så att eventuella ändringar visas.
        st.rerun()



# =========================
# KÖR DATABASKONTROLLEN
# =========================

check_for_new_prediction()


# =========================
# POPUP - FORMATERING
# =========================

prediction = st.session_state.get("new_prediction")
notification_time = st.session_state.get("notification_time")

show_notification = (
    prediction is not None
    and notification_time is not None
    and time.monotonic() - notification_time < 5
)


# =========================
# POPUP - RENDERING
# =========================
# Denna del ligger utanför fragmentet.
# CSS-animationen döljer popupen efter 5 sekunder.

if show_notification:

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
        price_text = f"{price:,.0f} kr".replace(",", " ")
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

    # Säker HTML-formatering
    municipality_safe = html.escape(str(municipality))
    property_type_safe = html.escape(str(property_type))
    rooms_text_safe = html.escape(str(rooms_text))
    area_text_safe = html.escape(str(area_text))
    price_text_safe = html.escape(str(price_text))

    interval_html = ""

    if interval_text:

        interval_html = textwrap.dedent(
            f"""
            <div style="
                margin-top: 8px;
                font-size: 13px;
                color: #cbd5e1;
            ">
                Prisintervall: {html.escape(str(interval_text))}
            </div>
            """
        ).strip()

    # Popupens HTML
    popup_html = textwrap.dedent(
        f"""
        <style>
            @keyframes popup-fade {{
                0% {{
                    opacity: 0;
                    transform: translateY(12px);
                }}

                8% {{
                    opacity: 1;
                    transform: translateY(0);
                }}

                85% {{
                    opacity: 1;
                    transform: translateY(0);
                }}

                100% {{
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(8px);
                }}
            }}
        </style>

        <div style="
            position: fixed;
            bottom: 24px;
            left: 24px;
            z-index: 999999;
            width: 340px;
            max-width: calc(100vw - 48px);
            box-sizing: border-box;
            background: #17212b;
            color: #ffffff;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
            font-family: sans-serif;
            animation: popup-fade 5s ease forwards;
        ">

            <div style="
                font-size: 17px;
                font-weight: 700;
                margin-bottom: 10px;
            ">
                🟢 Ny uppskattning!
            </div>

            <div style="
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 6px;
            ">
                {municipality_safe}
            </div>

            <div style="
                color: #cbd5e1;
                font-size: 13px;
                margin-bottom: 14px;
            ">
                {property_type_safe} · {rooms_text_safe} · {area_text_safe}
            </div>

            <div style="
                color: #cbd5e1;
                font-size: 13px;
                margin-bottom: 4px;
            ">
                Uppskattat pris
            </div>

            <div style="
                font-size: 27px;
                font-weight: 700;
                line-height: 1.2;
            ">
                {price_text_safe}
            </div>

            {interval_html}
        
        </div>
        """
    ).strip()

    st.html(popup_html)


# =========================
# EGEN SIDOMENY
# =========================

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


# =========================
# KÖR AKTUELL SIDA
# =========================

pg.run()