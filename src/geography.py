from pathlib import Path

import pandas as pd


MIN_OBSERVATIONS = 10

REQUIRED_COLUMNS = {
    "municipality",
    "typology",
    "latitude",
    "longitude",
    "observations",
    "median_asking_price",
    "median_sqm_price",
}


def load_municipality_profiles(
    path: str | Path,
    min_observations: int = MIN_OBSERVATIONS,
) -> pd.DataFrame:
    """Läs och validera kommunprofilerna som skapats i notebooken."""

    profiles = pd.read_csv(path)

    missing_columns = REQUIRED_COLUMNS - set(profiles.columns)

    if missing_columns:
        raise ValueError(
            "Kommunprofilen saknar kolumner: "
            f"{sorted(missing_columns)}"
        )

    if min_observations < 1:
        raise ValueError("Minsta antal observationer måste vara minst 1.")

    reliable_profiles = profiles[
        profiles["observations"] >= min_observations
    ].copy()

    return reliable_profiles


def get_available_municipalities(
    profiles: pd.DataFrame,
    typology: str,
) -> list[str]:
    """Returnera valbara kommuner för en viss bostadstyp."""

    municipalities = (
        profiles.loc[
            profiles["typology"] == typology,
            "municipality",
        ]
        .dropna()
        .sort_values()
        .tolist()
    )

    return municipalities


def compare_municipalities(
    pipeline,
    profiles: pd.DataFrame,
    typology: str,
    municipalities: list[str],
    living_area_sqm: float,
    number_rooms: int,
    land_area_sqm: float = 0,
) -> pd.DataFrame:
    """Prediktera samma bostad i flera kommuner.

    Boarea, antal rum, bostadstyp och tomtarea hålls konstanta.
    Kommun och kommunens mediankoordinater förändras.
    """

    if not 2 <= len(municipalities) <= 5:
        raise ValueError("Välj mellan 2 och 5 kommuner.")

    if len(municipalities) != len(set(municipalities)):
        raise ValueError("Samma kommun kan inte väljas flera gånger.")

    if living_area_sqm <= 0:
        raise ValueError("Boarean måste vara större än 0.")

    if number_rooms <= 0:
        raise ValueError("Antal rum måste vara större än 0.")

    if land_area_sqm < 0:
        raise ValueError("Tomtarean kan inte vara negativ.")

    selected_profiles = profiles[
        (profiles["typology"] == typology)
        & profiles["municipality"].isin(municipalities)
    ].copy()

    found_municipalities = set(
        selected_profiles["municipality"]
    )
    missing_municipalities = (
        set(municipalities) - found_municipalities
    )

    if missing_municipalities:
        raise ValueError(
            "Kommunprofil saknas för: "
            f"{sorted(missing_municipalities)}"
        )

    # Behåll samma ordning som användaren valde kommunerna i.
    selected_profiles["municipality"] = pd.Categorical(
        selected_profiles["municipality"],
        categories=municipalities,
        ordered=True,
    )
    selected_profiles = selected_profiles.sort_values(
        "municipality"
    )

    model_rows = []

    for profile in selected_profiles.itertuples():
        model_land_area = land_area_sqm
        has_land_area = int(land_area_sqm > 0)

        if typology == "APARTMENT":
            model_land_area = None
            has_land_area = 0

        if typology == "HOUSE" and land_area_sqm < 50:
            model_land_area = None

        model_rows.append({
            "typology": typology,
            "municipality": str(profile.municipality),
            "land_area_sqm": model_land_area,
            "living_area_sqm": living_area_sqm,
            "number_rooms": number_rooms,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "has_land_area": has_land_area,
        })

    model_input = pd.DataFrame(model_rows)
    predictions = pipeline.predict(model_input)

    results = selected_profiles[
        [
            "municipality",
            "latitude",
            "longitude",
            "observations",
            "median_sqm_price",
        ]
    ].copy()

    results["municipality"] = results[
        "municipality"
    ].astype(str)
    results["predicted_price"] = [
        max(float(prediction), 0)
        for prediction in predictions
    ]

    reference_price = results["predicted_price"].min()

    results["difference_sek"] = (
        results["predicted_price"] - reference_price
    )

    if reference_price > 0:
        results["difference_percent"] = (
            results["difference_sek"]
            / reference_price
            * 100
        )
    else:
        results["difference_percent"] = 0.0

    return results.sort_values(
        "predicted_price"
    ).reset_index(drop=True)
