"""MLflow model scoring for Zestimate predictions."""

import pandas as pd
import mlflow
from functools import lru_cache
from config import REGISTERED_MODEL_NAME, MODEL_ALIAS


@lru_cache(maxsize=1)
def _load_model():
    """Load the registered price prediction model (cached)."""
    mlflow.set_registry_uri("databricks-uc")
    model_uri = f"models:/{REGISTERED_MODEL_NAME}@{MODEL_ALIAS}"
    return mlflow.sklearn.load_model(model_uri)


def predict_price(property_data: dict) -> float | None:
    """Predict the price (Zestimate) for a single property."""
    try:
        model = _load_model()
        feature_cols = [
            "beds", "baths", "sqft", "lot_size", "year_built",
            "school_rating", "walk_score", "hoa_fee",
            "city", "property_type", "neighborhood",
        ]
        row = {col: property_data.get(col) for col in feature_cols}
        df = pd.DataFrame([row])
        prediction = model.predict(df)[0]
        return round(float(prediction), -3)  # round to nearest $1,000
    except Exception:
        return None


def predict_prices_batch(properties: list[dict]) -> list[float | None]:
    """Predict prices for a batch of properties."""
    try:
        model = _load_model()
        feature_cols = [
            "beds", "baths", "sqft", "lot_size", "year_built",
            "school_rating", "walk_score", "hoa_fee",
            "city", "property_type", "neighborhood",
        ]
        rows = [{col: p.get(col) for col in feature_cols} for p in properties]
        df = pd.DataFrame(rows)
        predictions = model.predict(df)
        return [round(float(p), -3) for p in predictions]
    except Exception:
        return [None] * len(properties)
