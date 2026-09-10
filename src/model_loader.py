from pathlib import Path

import joblib


def load_model_bundle(path: str | Path) -> dict:
    """Ladda modellen och dess feature-kolumner fran notebooken."""
    bundle = joblib.load(path)

    if not isinstance(bundle, dict):
        raise ValueError("Modellfilen maste innehalla en dictionary.")

    if "model" not in bundle or "feature_columns" not in bundle:
        raise ValueError("Modellfilen saknar 'model' eller 'feature_columns'.")

    return bundle

