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

## Spara modeller från notebooken

Kör detta efter att respektive modell har tränats. Använd modellens egna
X-kolumner, exempelvis `X_global.columns` för den globala modellen.

```python
from pathlib import Path
import joblib

Path("../models").mkdir(exist_ok=True)

joblib.dump(
    {
        "model": rf_global,
        "feature_columns": X_global.columns.tolist(),
    },
    "../models/global_random_forest.joblib",
)
```

För en specialiserad modell byter ni bara modellvariabel, feature-lista och
filnamn. Inga modeller eller hyperparametrar definieras av boilerplaten.

## Starta Streamlit

```bash
python -m streamlit run app.py
```

Hypotesanalysen och modellträningen görs i notebooken. Streamlit-sidorna i
`pages/` används endast för den interaktiva presentationen.

