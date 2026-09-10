import pandas as pd


def prepare_input(user_input: dict, feature_columns: list[str]) -> pd.DataFrame:
    """Anpassa en formularrad till kolumnerna modellen tranades med."""
    input_df = pd.DataFrame([user_input])

    categorical_columns = [
        column
        for column in ["municipality", "typology"]
        if column in input_df.columns
    ]

    input_df = pd.get_dummies(input_df, columns=categorical_columns)

    return input_df.reindex(columns=feature_columns, fill_value=0)

