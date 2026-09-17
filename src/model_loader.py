from pathlib import Path

import joblib


def load_model_bundle(path: str | Path) -> dict:
    """Ladda och validera en sparad modellbundle."""

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

    metadata = bundle["metadata"]

    if not isinstance(metadata, dict):
        raise ValueError(
            "Modellfilens metadata måste vara en dictionary."
        )

    if metadata.get("segment") == "GLOBAL":
        metrics_by_segment = bundle.get(
            "metrics_by_segment"
        )

        if not isinstance(metrics_by_segment, dict):
            raise ValueError(
                "Globalmodellen saknar "
                "'metrics_by_segment'."
            )

        required_segments = {
            "APARTMENT",
            "HOUSE",
            "ROW_HOUSE"
        }

        missing_segments = (
            required_segments
            - metrics_by_segment.keys()
        )

        if missing_segments:
            raise ValueError(
                "Globalmodellen saknar metrics för: "
                f"{sorted(missing_segments)}"
            )

    return bundle
