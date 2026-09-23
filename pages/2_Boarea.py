from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Boarea och utgångspris",
    page_icon="🏠",
)

st.title("🏠 Boarea och utgångspris")

# Läs underlaget som sparades från notebooken
data_dir = Path(__file__).resolve().parents[1] / "data" / "h2"
file_names = ["eda_train.csv", "validation_results.csv", "test_results.csv"]

if not all((data_dir / name).exists() for name in file_names):
    st.error("Underlaget för boareaanalysen saknas. Sidan kan inte visas ännu.")
    st.stop()

train_data = pd.read_csv(data_dir / "eda_train.csv")
validation_results = pd.read_csv(
    data_dir / "validation_results.csv", index_col="Modell"
)
test_results = pd.read_csv(data_dir / "test_results.csv", index_col="Modell")

st.subheader("Samband i träningsdata")

# Filtrera bara den beskrivande analysen efter bostadstyp
housing_types = {
    "Alla": None,
    "Lägenheter": "APARTMENT",
    "Hus": "HOUSE",
    "Radhus": "ROW_HOUSE",
}
selected_type = st.selectbox(
    "Välj bostadstyp för diagrammet", list(housing_types))

if selected_type == "Alla":
    selected_data = train_data
else:
    selected_data = train_data[
        train_data["typology"] == housing_types[selected_type]
    ]

correlation = selected_data["living_area_sqm"].corr(
    selected_data["asking_price_sek"]
)
left, right = st.columns(2)
left.metric("Antal bostäder", f"{len(selected_data):,}".replace(",", " "))
right.metric("Pearsons korrelation", f"{correlation:.3f}".replace(".", ","))

# Visa samma samband som i notebooken, med svenska axelrubriker
plot_data = selected_data[["living_area_sqm", "asking_price_sek"]].rename(
    columns={
        "living_area_sqm": "Boarea (m²)",
        "asking_price_sek": "Utgångspris (miljoner kr)",
    }
)
plot_data["Utgångspris (miljoner kr)"] /= 1_000_000

st.scatter_chart(
    plot_data,
    x="Boarea (m²)",
    y="Utgångspris (miljoner kr)",
    color="#3b82f680",
    size=15,
    height=380,
)
st.caption("Diagrammet och korrelationen använder bara träningsdata.")

st.divider()
st.subheader("Modelljämförelse för alla bostadstyper")
st.caption("Jämförelsen gäller hela urvalet, oavsett bostadstypen som valts ovan.")

# Välj vilken av notebookens utvärderingar som ska visas
evaluation = st.radio(
    "Välj utvärdering", ["Testdata", "Valideringsdata"], horizontal=True
)
results = test_results if evaluation == "Testdata" else validation_results

without_area = results.loc["Modell utan boarea"]
with_area = results.loc["Modell med boarea"]
rmse_reduction = (without_area["RMSE"] -
                  with_area["RMSE"]) / without_area["RMSE"] * 100
mae_reduction = (without_area["MAE"] -
                 with_area["MAE"]) / without_area["MAE"] * 100

left, right = st.columns(2)
left.metric("Minskning av RMSE med boarea",
            f"{rmse_reduction:.2f} %".replace(".", ","))
right.metric("Minskning av MAE med boarea",
             f"{mae_reduction:.2f} %".replace(".", ","))

# Behåll alla fyra modeller och visa felmåtten i kronor
display_results = results.rename(
    columns={
        "MAE": "MAE (kr)",
        "RMSE": "RMSE (kr)",
        "Median error": "Medianfel (kr)",
        "R2": "R²",
    }
)
st.dataframe(
    display_results.style.format(precision=2, thousands=" ", decimal=","),
    width="stretch",
)
st.caption("Lägre MAE, RMSE och medianfel är bättre. Ett högre R² är bättre.")

if rmse_reduction > 0 and mae_reduction > 0:
    st.success(
        "Modellen med boarea har lägre RMSE och MAE i den valda utvärderingen.")
else:
    st.info("Jämför båda felmåtten i tabellen för att bedöma resultatet.")

with st.expander("Metod och begränsningar"):
    st.write(
        "Modellerna använde samma algoritm, inställningar och bostäder. "
        "Skillnaden var att den ena modellen även fick använda boarea. "
        "Båda använde bland annat bostadstyp, antal rum och geografiskt läge."
    )
    st.write(
        "Först tränades modellerna på träningsdata och jämfördes på valideringsdata. "
        "Sedan tränades nya kopior på träning och validering tillsammans "
        "inför den slutliga testningen."
    )
    st.write(
        "Resultatet gäller vårt filtrerade urval och utgångspriser, inte slutpriser. "
        "Sambandet mellan boarea och pris bevisar inte något orsakssamband."
    )
    st.write(
        "En första analys gjordes på hela datamängden före uppdelningen. "
        "Testdata var därför inte helt osedda."
    )
