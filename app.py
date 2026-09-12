from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Bostadskollen",
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
]

pg = st.navigation(
    pages,
    position="hidden"
)

with st.sidebar:
    st.title("🏠 Bostadskollen")
    st.write(
        "Uppskatta en bostads utgångspris med en modell tränad i notebooken."
    )
    st.write(
        "Observera att träningsdatan inte har kunnat verifieras och att modellens resultat därför inte bör betraktas som tillförlitligt."
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

pg.run()