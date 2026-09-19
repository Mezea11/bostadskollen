import streamlit as st
import pandas as pd
import folium
import plotly.express as px

from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from src.database import get_predictions


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
    "Utforska data från genomförda "
    "prisuppskattningar i Boprisindikatorn."
)


# =========================
# FILTER
# =========================

st.subheader("Filter")


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
# AVDELARE
# =========================

st.divider()


# =========================
# ÖVERSIKT
# =========================

st.subheader("Översikt")


kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)


# =========================
# FORMATERA PRIS
# =========================

def format_price(price):

    if price >= 1_000_000:

        return (
            f"{price / 1_000_000:.2f}"
            .replace(".", ",")
            + " Mkr"
        )

    if price >= 1_000:

        return (
            f"{price / 1_000:.0f}"
            .replace(".", ",")
            + " tkr"
        )

    return (
        f"{price:,.0f}"
        .replace(",", " ")
        + " kr"
    )


# =========================
# ANTAL UPPSKATTNINGAR
# =========================

with kpi_col1:

    st.metric(
        "Antal uppskattningar",
        f"{len(filtered_df):,}".replace(",", " "),
    )


# =========================
# GENOMSNITTLIGT PRIS
# =========================

with kpi_col2:

    average_price = filtered_df[
        "predicted_price"
    ].mean()

    st.metric(
        "Genomsnittligt pris",
        format_price(average_price),
    )


# =========================
# LÄGSTA
# =========================

with kpi_col3:

    min_price = filtered_df[
        "predicted_price"
    ].min()

    st.metric(
        "Lägsta uppskattning",
        format_price(min_price),
    )


# =========================
# HÖGSTA
# =========================

with kpi_col4:

    max_price = filtered_df[
        "predicted_price"
    ].max()

    st.metric(
        "Högsta uppskattning",
        format_price(max_price),
    )


# =========================
# DIAGRAM
# =========================

st.divider()


chart_col1, chart_col2 = st.columns(2)


# =========================
# ANTAL UPPSKATTNINGAR ÖVER TID
# =========================

with chart_col1:

    st.subheader(
        "Antal uppskattningar över tid"
    )

    time_df = (
        filtered_df
        .assign(
            date=filtered_df["timestamp"].dt.strftime("%d/%m")
        )
        .groupby("date")
        .size()
        .reset_index(name="Antal")
    )

    fig_time = px.bar(
        time_df,
        x="date",
        y="Antal",
        labels={
            "date": "Datum",
            "Antal": "Antal uppskattningar",
        },
    )

    fig_time.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    fig_time.update_xaxes(
        type="category",
    )

    st.plotly_chart(
        fig_time,
        width="stretch",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


# =========================
# FÖRDELNING PER BOSTADSTYP
# =========================

with chart_col2:

    st.subheader(
        "Fördelning per bostadstyp"
    )

    property_chart = (
        filtered_df["property_type"]
        .value_counts()
        .reset_index()
    )

    property_chart.columns = [
        "property_type",
        "Antal",
    ]

    fig_property = px.bar(
        property_chart,
        x="property_type",
        y="Antal",
        labels={
            "property_type": "Bostadstyp",
            "Antal": "Antal uppskattningar",
        },
    )

    fig_property.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    st.plotly_chart(
        fig_property,
        width="stretch",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


# =========================
# PRIS PER M² + PRISFÖRDELNING
# =========================

price_col1, price_col2 = st.columns(2)


# =========================
# GENOMSNITTLIGT PRIS PER M²
# =========================

with price_col1:

    st.subheader(
        "Genomsnittligt pris per m²"
    )

    price_sqm_df = filtered_df.copy()

    # Undvik division med 0
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
            "price_per_sqm": "Pris per m²",
        },
    )

    fig_price_sqm.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    fig_price_sqm.update_yaxes(
        tickformat=",.0f",
    )

    st.plotly_chart(
        fig_price_sqm,
        width="stretch",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )


# =========================
# PRISFÖRDELNING
# =========================

with price_col2:

    st.subheader(
        "Prisfördelning"
    )

    # Skapa prisintervall
    price_distribution_df = filtered_df.copy()

    price_distribution_df["prisintervall"] = pd.cut(
        price_distribution_df["predicted_price"],
        bins=[
            0,
            1_000_000,
            2_000_000,
            3_000_000,
            4_000_000,
            5_000_000,
            float("inf"),
        ],
        labels=[
            "0–1 Mkr",
            "1–2 Mkr",
            "2–3 Mkr",
            "3–4 Mkr",
            "4–5 Mkr",
            "5+ Mkr",
        ],
        right=False,
    )

    price_distribution_chart = (
        price_distribution_df["prisintervall"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    price_distribution_chart.columns = [
        "prisintervall",
        "Antal",
    ]

    fig_price_distribution = px.bar(
        price_distribution_chart,
        x="prisintervall",
        y="Antal",
        labels={
            "prisintervall": "Prisintervall",
            "Antal": "Antal uppskattningar",
        },
    )

    fig_price_distribution.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
    )

    st.plotly_chart(
        fig_price_distribution,
        width="stretch",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
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

    st.subheader(
        "Top 10 kommuner"
    )

    municipality_chart = (
        filtered_df["municipality"]
        .value_counts()
        .head(10)
    )

    municipality_chart = (
        municipality_chart
        .sort_values(ascending=True)
    )

    fig_municipality = px.bar(
        municipality_chart,
        x=municipality_chart.values,
        y=municipality_chart.index,
        orientation="h",
        labels={
            "x": "Antal uppskattningar",
            "y": "Kommun",
        },
    )

    fig_municipality.update_layout(
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
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

    st.subheader(
        "Geografisk fördelning"
    )

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

        center_lat = map_df[
            "latitude"
        ].mean()

        center_lon = map_df[
            "longitude"
        ].mean()


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


            address = (
                row["address"]
                if pd.notna(row["address"])
                and row["address"]
                else "Okänd adress"
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

            if pd.notna(
                row["predicted_price"]
            ):

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


                <b>Adress</b><br>
                {address}


                <br><br>


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