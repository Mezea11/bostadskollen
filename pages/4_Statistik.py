import streamlit as st
import pandas as pd
import folium
import plotly.express as px

from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from src.database import get_predictions


def format_price(price):
    if pd.isna(price):
        return "—"

    return f"{price:,.0f} kr".replace(",", " ")


# =========================
# SIDINSTÄLLNINGAR
# =========================

st.set_page_config(
    page_title="Statistik – Boprisindikatorn",
    page_icon="📈",
)


# =========================
# HÄMTA DATA
# =========================

rows, columns = get_predictions(10000)

df = pd.DataFrame(
    rows,
    columns=columns
)


# =========================
# INGEN DATA
# =========================

if df.empty:
    st.title("📈 Statistik")

    st.info(
        "Det finns inga registrerade prisuppskattningar ännu."
    )

    st.stop()


# =========================
# FÖRBERED DATA
# =========================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df["property_type"] = df["property_type"].replace({
    "APARTMENT": "Lägenhet",
    "HOUSE": "Villa",
    "ROW_HOUSE": "Radhus",
})


# =========================
# RUBRIK
# =========================

st.title("📈 Statistik")

st.write(
    "Utforska prisuppskattningar och geografisk fördelning i Boprisindikatorn."
)


# =========================
# FILTER
# =========================

st.subheader("Filter")

st.caption(
    "Välj datumintervall, bostadstyp och kommun "
    "för att anpassa statistiken."
)

with st.container(border=True):

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    # =========================
    # DATUMFILTER
    # =========================

    with filter_col1:

        min_date = df["timestamp"].min().date()
        max_date = df["timestamp"].max().date()

        date_range = st.date_input(
            "Datum",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    # =========================
    # BOSTADSTYP
    # =========================

    with filter_col2:

        property_options = [
            "Alla"
        ] + sorted(
            df["property_type"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_property = st.selectbox(
            "Bostadstyp",
            property_options,
        )

    # =========================
    # KOMMUN
    # =========================

    with filter_col3:

        municipality_options = [
            "Alla"
        ] + sorted(
            df["municipality"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_municipality = st.selectbox(
            "Kommun",
            municipality_options,
        )


# =========================
# FILTRERA DATA
# =========================

filtered_df = df.copy()


# Datum

if len(date_range) == 2:

    start_date = pd.Timestamp(
        date_range[0]
    )

    end_date = (
        pd.Timestamp(date_range[1])
        + pd.Timedelta(days=1)
    )

    filtered_df = filtered_df[
        (filtered_df["timestamp"] >= start_date)
        &
        (filtered_df["timestamp"] < end_date)
    ]


# Bostadstyp

if selected_property != "Alla":

    filtered_df = filtered_df[
        filtered_df["property_type"]
        == selected_property
    ]


# Kommun

if selected_municipality != "Alla":

    filtered_df = filtered_df[
        filtered_df["municipality"]
        == selected_municipality
    ]


# =========================
# INGEN DATA EFTER FILTER
# =========================

if filtered_df.empty:

    st.warning(
        "Det finns inga uppskattningar "
        "som matchar de valda filtren."
    )

    st.stop()


# =========================
# CSV-EXPORT
# =========================

# Exportera alla uppskattningar som matchar de aktiva filtren.

export_df = filtered_df[
    [
        "timestamp",
        "municipality",
        "property_type",
        "living_area",
        "land_area",
        "predicted_price",
        "lower_price",
        "upper_price",
    ]
].copy()


# Svenska kolumnrubriker och läsbar tidsstämpel.

export_df = export_df.rename(
    columns={
        "timestamp": "Tid",
        "address": "Adress",
        "municipality": "Kommun",
        "property_type": "Bostadstyp",
        "living_area": "Boarea (m²)",
        "land_area": "Tomtarea (m²)",
        "predicted_price": "Uppskattat pris (kr)",
        "lower_price": "Lägsta pris i intervall (kr)",
        "upper_price": "Högsta pris i intervall (kr)",
    }
)

export_df["Tid"] = export_df["Tid"].dt.strftime(
    "%Y-%m-%d %H:%M"
)


# Semikolon fungerar bra som avgränsare i svensk Excel.

csv_data = export_df.to_csv(
    index=False,
    sep=";",
    encoding="utf-8-sig",
)

st.download_button(
    label="📥 Ladda ner CSV",
    data=csv_data,
    file_name="boprisindikatorn_uppskattningar.csv",
    mime="text/csv",
    help="Ladda ner alla uppskattningar som matchar de valda filtren.",
)


# =========================
# AVDELARE
# =========================

st.divider()


# =========================
# ÖVERSIKT – KPI-KORT
# =========================

st.subheader("Översikt")

st.caption(
    "Sammanfattning av prisuppskattningarna "
    "som matchar dina valda filter."
)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

total_predictions = len(filtered_df)

average_price = filtered_df["predicted_price"].mean()
min_price = filtered_df["predicted_price"].min()
max_price = filtered_df["predicted_price"].max()


def format_price_millions(price):
    if pd.isna(price):
        return "—"

    return f"{price / 1_000_000:.2f} Mkr".replace(".", ",")


with kpi_col1:
    with st.container(border=True):
        st.metric(
            label="Antal uppskattningar",
            value=f"{total_predictions:,}".replace(",", " "),
        )

with kpi_col2:
    with st.container(border=True):
        st.metric(
            label="Genomsnittspris",
            value=format_price_millions(average_price),
        )

with kpi_col3:
    with st.container(border=True):
        st.metric(
            label="Lägsta pris",
            value=format_price_millions(min_price),
        )

with kpi_col4:
    with st.container(border=True):
        st.metric(
            label="Högsta pris",
            value=format_price_millions(max_price),
        )

st.divider()


# =========================
# DIAGRAM
# =========================


# Gemensamma inställningar för enhetliga och lättlästa diagram.

chart_config = {
    "displayModeBar": False,
    "scrollZoom": False,
}

chart_layout = {
    "template": "plotly_white",
    "height": 340,
    "margin": dict(l=12, r=12, t=24, b=12),
    "font": dict(size=12),
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
}

chart_col1, chart_col2 = st.columns(2, gap="large")


# =========================
# ANTAL UPPSKATTNINGAR ÖVER TID
# =========================

with chart_col1:
    with st.container(border=True):

        st.subheader("Antal uppskattningar över tid")

        st.caption(
            "Antal registrerade uppskattningar per datum."
        )

        # Gruppera på hela datumet så att datum från olika år inte slås ihop.

        time_df = (
            filtered_df
            .dropna(subset=["timestamp"])
            .assign(date=filtered_df["timestamp"].dt.date)
            .groupby("date")
            .size()
            .reset_index(name="Antal")
            .sort_values("date")
        )

        time_df["Datum"] = pd.to_datetime(
            time_df["date"]
        ).dt.strftime("%d/%m")

        fig_time = px.bar(
            time_df,
            x="Datum",
            y="Antal",
            labels={
                "Datum": "Datum",
                "Antal": "Antal uppskattningar",
            },
            text="Antal",
        )

        fig_time.update_layout(**chart_layout)

        fig_time.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig_time.update_xaxes(
            type="category",
            showgrid=False,
            title=None,
        )

        fig_time.update_yaxes(
            rangemode="tozero",
            gridcolor="rgba(128,128,128,0.18)",
            zeroline=False,
        )

        st.plotly_chart(
            fig_time,
            width="stretch",
            config=chart_config,
        )


# =========================
# FÖRDELNING PER BOSTADSTYP
# =========================

with chart_col2:
    with st.container(border=True):

        st.subheader("Fördelning per bostadstyp")

        st.caption(
            "Antal uppskattningar för varje bostadstyp."
        )

        property_chart = (
            filtered_df["property_type"]
            .value_counts()
            .rename_axis("Bostadstyp")
            .reset_index(name="Antal")
        )

        fig_property = px.bar(
            property_chart,
            x="Bostadstyp",
            y="Antal",
            labels={
                "Bostadstyp": "Bostadstyp",
                "Antal": "Antal uppskattningar",
            },
            text="Antal",
        )

        fig_property.update_layout(**chart_layout)

        fig_property.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig_property.update_xaxes(
            showgrid=False,
            title=None,
        )

        fig_property.update_yaxes(
            rangemode="tozero",
            gridcolor="rgba(128,128,128,0.18)",
            zeroline=False,
        )

        st.plotly_chart(
            fig_property,
            width="stretch",
            config=chart_config,
        )


# =========================
# PRIS PER M² + PRISFÖRDELNING
# =========================

price_col1, price_col2 = st.columns(2, gap="large")


# =========================
# GENOMSNITTLIGT PRIS PER M²
# =========================

with price_col1:
    with st.container(border=True):

        st.subheader("Genomsnittligt pris per m²")

        st.caption(
            "Genomsnittligt uppskattat kvadratmeterpris per bostadstyp."
        )

        price_sqm_df = filtered_df.copy()

        # Undvik division med 0.

        price_sqm_df = price_sqm_df[
            price_sqm_df["living_area"] > 0
        ]

        price_sqm_df["price_per_sqm"] = (
            price_sqm_df["predicted_price"]
            / price_sqm_df["living_area"]
        )

        price_sqm_chart = (
            price_sqm_df
            .groupby("property_type")["price_per_sqm"]
            .mean()
            .reset_index()
        )

        price_sqm_chart["price_per_sqm"] = (
            price_sqm_chart["price_per_sqm"]
            .round(0)
        )

        fig_price_sqm = px.bar(
            price_sqm_chart,
            x="property_type",
            y="price_per_sqm",
            labels={
                "property_type": "Bostadstyp",
                "price_per_sqm": "Pris per m² (kr)",
            },
            text="price_per_sqm",
        )

        fig_price_sqm.update_layout(**chart_layout)

        fig_price_sqm.update_traces(
            texttemplate="%{text:,.0f} kr",
            textposition="outside",
            cliponaxis=False,
        )

        fig_price_sqm.update_xaxes(
            showgrid=False,
            title=None,
        )

        fig_price_sqm.update_yaxes(
            tickformat=",.0f",
            rangemode="tozero",
            gridcolor="rgba(128,128,128,0.18)",
            zeroline=False,
        )

        st.plotly_chart(
            fig_price_sqm,
            width="stretch",
            config=chart_config,
        )


# =========================
# PRISFÖRDELNING
# =========================

with price_col2:
    with st.container(border=True):

        st.subheader("Prisfördelning")

        st.caption(
            "Hur uppskattningarna fördelar sig mellan prisintervallen."
        )

        price_distribution_df = filtered_df.copy()

        price_bins = [
            0,
            1_000_000,
            2_000_000,
            3_000_000,
            4_000_000,
            5_000_000,
            float("inf"),
        ]

        price_labels = [
            "0–1 Mkr",
            "1–2 Mkr",
            "2–3 Mkr",
            "3–4 Mkr",
            "4–5 Mkr",
            "5+ Mkr",
        ]

        price_distribution_df["prisintervall"] = pd.cut(
            price_distribution_df["predicted_price"],
            bins=price_bins,
            labels=price_labels,
            right=False,
        )

        price_distribution_chart = (
            price_distribution_df["prisintervall"]
            .value_counts()
            .reindex(price_labels, fill_value=0)
            .rename_axis("Prisintervall")
            .reset_index(name="Antal")
        )

        fig_price_distribution = px.bar(
            price_distribution_chart,
            x="Prisintervall",
            y="Antal",
            labels={
                "Prisintervall": "Prisintervall",
                "Antal": "Antal uppskattningar",
            },
            text="Antal",
        )

        fig_price_distribution.update_layout(**chart_layout)

        fig_price_distribution.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig_price_distribution.update_xaxes(
            showgrid=False,
            title=None,
        )

        fig_price_distribution.update_yaxes(
            rangemode="tozero",
            gridcolor="rgba(128,128,128,0.18)",
            zeroline=False,
        )

        st.plotly_chart(
            fig_price_distribution,
            width="stretch",
            config=chart_config,
        )


# =========================
# KOMMUN + KARTA
# =========================

st.divider()

municipality_col, map_col = st.columns(2)



# =========================
# TOPP 10 KOMMUNER
# =========================

with municipality_col:

    with st.container(border=True):

        st.subheader("Top 10 kommuner")

        st.caption(
            "Kommunerna med flest prisuppskattningar "
            "bland de filtrerade resultaten."
        )

        municipality_chart = (
            filtered_df["municipality"]
            .dropna()
            .value_counts()
            .head(10)
            .sort_values(ascending=True)
        )

        fig_municipality = px.bar(
            x=municipality_chart.values,
            y=municipality_chart.index,
            orientation="h",
            labels={
                "x": "Antal uppskattningar",
                "y": "Kommun",
            },
            text=municipality_chart.values,
        )

        fig_municipality.update_layout(
            template="plotly_white",
            height=400,
            margin=dict(l=12, r=20, t=15, b=12),
            font=dict(size=12),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig_municipality.update_traces(
            textposition="outside",
            cliponaxis=False,
        )

        fig_municipality.update_xaxes(
            title=None,
            rangemode="tozero",
            gridcolor="rgba(128,128,128,0.18)",
            zeroline=False,
        )

        fig_municipality.update_yaxes(
            title=None,
            showgrid=False,
        )

        st.plotly_chart(
            fig_municipality,
            width="stretch",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
            },
        )


# =========================
# KARTA
# =========================

with map_col:

    st.subheader("Geografisk fördelning")

    map_df = filtered_df.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )

    if map_df.empty:

        st.info(
            "Det finns inga uppskattningar "
            "med geografiska koordinater."
        )

    else:

        # =========================
        # KARTANS CENTRUM
        # =========================

        center_lat = map_df["latitude"].mean()
        center_lon = map_df["longitude"].mean()


        # =========================
        # SKAPA KARTA
        # =========================

        stats_map = folium.Map(
            location=[
                center_lat,
                center_lon,
            ],
            zoom_start=6,
        )


        # =========================
        # MARKÖRKLUSTER
        # =========================

        marker_cluster = MarkerCluster().add_to(
            stats_map
        )


        # =========================
        # MARKÖRER
        # =========================

        for _, row in map_df.iterrows():

            # -------------------------
            # SÄKRA TEXTVÄRDEN
            # -------------------------

            property_type = (
                row["property_type"]
                if pd.notna(row["property_type"])
                and row["property_type"]
                else "Okänd"
            )


            municipality = (
                row["municipality"]
                if pd.notna(row["municipality"])
                and row["municipality"]
                else "Okänd"
            )


            # -------------------------
            # BOAREA
            # -------------------------

            if pd.notna(row["living_area"]):

                living_area = (
                    f"{row['living_area']:.0f} m²"
                )

            else:

                living_area = "–"


            # -------------------------
            # PRIS
            # -------------------------

            if pd.notna(row["predicted_price"]):

                predicted_price = (
                    f"{row['predicted_price']:,.0f} kr"
                    .replace(",", " ")
                )

            else:

                predicted_price = "–"


            # -------------------------
            # PRISINTERVALL
            # -------------------------

            if (
                pd.notna(row["lower_price"])
                and pd.notna(row["upper_price"])
            ):

                price_interval = (
                    f"{row['lower_price']:,.0f}"
                    .replace(",", " ")
                    +
                    " – "
                    +
                    f"{row['upper_price']:,.0f} kr"
                    .replace(",", " ")
                )

            else:

                price_interval = "–"


            # =========================
            # POPUP
            # =========================

            popup_html = f"""
            <div style="
                min-width: 240px;
                font-family: Arial, sans-serif;
            ">

                <h4 style="
                    margin-top: 0;
                    margin-bottom: 14px;
                ">
                    🏠 Bostadsuppskattning
                </h4>

                <b>Kommun</b><br>
                {municipality}

                <br><br>

                <b>Bostadstyp</b><br>
                {property_type}

                <br><br>

                <b>Boarea</b><br>
                {living_area}

                <br><br>

                <b>Uppskattat pris</b><br>

                <strong>
                    {predicted_price}
                </strong>

                <br><br>

                <b>Prisintervall</b><br>
                {price_interval}

            </div>
            """


            # =========================
            # CIRKELMARKÖR
            # =========================

            folium.CircleMarker(
                location=[
                    row["latitude"],
                    row["longitude"],
                ],

                radius=7,

                popup=folium.Popup(
                    popup_html,
                    max_width=350,
                ),

                tooltip=(
                    f"{municipality} – "
                    f"{predicted_price}"
                ),

                fill=True,
            ).add_to(
                marker_cluster
            )


        # =========================
        # VISA KARTA
        # =========================

        st_folium(
            stats_map,
            width=None,
            height=500,
            returned_objects=[],
        )


# =========================
# SENASTE UPPSKATTNINGARNA
# =========================

st.divider()

st.subheader("Senaste uppskattningarna")


# Sortera efter tid och hämta de 10 senaste.

latest_df = (
    filtered_df
    .sort_values("timestamp", ascending=False)
    .head(10)
    .copy()
)


# =========================
# FORMATERA TABELLEN
# =========================

# Datum och tid

latest_df["Tid"] = (
    latest_df["timestamp"]
    .dt.strftime("%Y-%m-%d %H:%M")
)


# Boarea

latest_df["Boarea (m²)"] = (
    latest_df["living_area"]
    .apply(
        lambda x: f"{x:.0f}" if pd.notna(x) else "–"
    )
)


# Tomtarea

latest_df["Tomtarea (m²)"] = (
    latest_df["land_area"]
    .apply(
        lambda x: f"{x:.0f}" if pd.notna(x) and x > 0 else "–"
    )
)


# Uppskattat pris

latest_df["Uppskattat pris"] = (
    latest_df["predicted_price"]
    .apply(
        lambda x: f"{x:,.0f} kr".replace(",", " ")
        if pd.notna(x) else "–"
    )
)


# Prisintervall

latest_df["Intervall"] = latest_df.apply(
    lambda row: (
        f"{row['lower_price']:,.0f} – "
        f"{row['upper_price']:,.0f} kr"
    ).replace(",", " ")
    if (
        pd.notna(row["lower_price"])
        and pd.notna(row["upper_price"])
    )
    else "–",
    axis=1,
)


# =========================
# VÄLJ KOLUMNER
# =========================

display_df = latest_df[
    [
        "Tid",
        "municipality",
        "property_type",
        "Boarea (m²)",
        "Tomtarea (m²)",
        "Uppskattat pris",
        "Intervall",
    ]
].rename(
    columns={
        "municipality": "Kommun",
        "property_type": "Bostadstyp",
        "Intervall": "Prisintervall",
    }
)


# =========================
# VISA TABELL
# =========================


st.dataframe(
    display_df,
    hide_index=True,
    width="stretch",
    height=390,
    column_config={
        "Tid": st.column_config.TextColumn(
            "Tid",
            help="Datum och tid då uppskattningen registrerades.",
        ),
        "Kommun": st.column_config.TextColumn(
            "Kommun",
        ),
        "Bostadstyp": st.column_config.TextColumn(
            "Bostadstyp",
        ),
        "Boarea (m²)": st.column_config.TextColumn(
            "Boarea (m²)",
        ),
        "Tomtarea (m²)": st.column_config.TextColumn(
            "Tomtarea (m²)",
        ),
        "Uppskattat pris": st.column_config.TextColumn(
            "Uppskattat pris",
        ),
        "Intervall": st.column_config.TextColumn(
            "Prisintervall",
            width="medium",
        ),
    },
)