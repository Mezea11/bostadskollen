# Bostadskollen

Minimal boilerplate för ett ML-projekt med Jupyter Notebook och Streamlit.
Modellerna tränas och utvärderas i notebooken. Streamlit laddar de färdiga
modellerna från `models/` och gör prediktioner.

## Projektstruktur

```text
bostadskollen/
├── app.py
├── requirements.txt
├── data/
│   └── SwedenHousingPrices.csv
├── models/
├── notebooks/
│   └── model_training.ipynb
├── pages/
│   ├── 1_Geografi.py
│   ├── 2_Boarea.py
│   └── 3_Modelljamforelse.py
└── src/
    ├── model_loader.py
    └── preprocessing.py
```

## Installation

```bash
uv venv --python 3.14.5 .venv
source .venv/Scripts/activate
uv pip install -r requirements.txt
```

## Träna och spara modeller

Modellerna tränas i:

```text
notebooks/model_training.ipynb
```

Kör samtliga celler i notebooken för att skapa modellfilerna:

```text
models/global_model.joblib
models/apartment_model.joblib
models/house_model.joblib
models/row_house_model.joblib
```

Varje modellfil innehåller en komplett bundle:

```python
{
    "pipeline": trained_pipeline,
    "metrics": {
        "mae": ...,
        "rmse": ...,
        "median_error": ...,
        "r2": ...
    },
    "metadata": {
        "segment": ...,
        "model_name": ...,
        "training_rows": ...,
        "test_rows": ...,
        "feature_columns": ...,
        "target": "asking_price_sek",
        "price_min": 100_000,
        "price_max": 10_000_000,
        "random_state": 42,
        "data_file": "SwedenHousingPrices.csv",
        "sklearn_version": ...
    }
}
```

Globalmodellen innehåller dessutom testmetrics per bostadstyp:

```python
{
    "metrics_by_segment": {
        "APARTMENT": {...},
        "HOUSE": {...},
        "ROW_HOUSE": {...}
    }
}
```

Pipelinen innehåller både preprocessing och den tränade modellen. Streamlit-appen skickar därför rå formulärdata direkt till pipelinen.

Modellfilerna genereras lokalt och sparas inte i Git.

För en specialiserad modell byter ni bara modellvariabel, feature-lista och
filnamn. Inga modeller eller hyperparametrar definieras av boilerplaten.

## Starta Streamlit

```bash
python -m streamlit run app.py
```

Hypotesanalysen och modellträningen görs i notebooken. Streamlit-sidorna i
`pages/` används endast för den interaktiva presentationen.

## Liveversion

Appen finns publicerad här:

[Öppna Bostadskollen](DIN_STREAMLIT_LÄNK)

## Deployment

Applikationen distribueras genom Streamlit Community Cloud.

Produktionsversionen använder:

- `models/global_model.joblib`
- `models/apartment_model.joblib`
- lokal SQLite för demonstrationsdata

SQLite-datan kan återställas när molninstansen startas om.
