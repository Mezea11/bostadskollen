from pathlib import Path

import joblib


def load_model_bundle(path: str | Path) -> dict:
    """Ladda pipeline, metrics och metadata från en modellfil."""

    bundle = joblib.load(path)

    if not isinstance(bundle, dict):
        raise ValueError(
            "Modellfilen måste innehålla en dictionary."
        )

    required_keys = {
        "pipeline",
        "metrics",
        "metadata"
    }

    missing_keys = required_keys - bundle.keys()

    if missing_keys:
        raise ValueError(
            f"Modellfilen saknar: {sorted(missing_keys)}"
        )

    if not hasattr(bundle["pipeline"], "predict"):
        raise ValueError(
            "Modellfilens pipeline saknar predict()."
        )

    return bundle
