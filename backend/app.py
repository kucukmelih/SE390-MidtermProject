import os
import pickle
import json
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from .risk_utils import SimpleRiskModel, explain_risk
except ImportError:
    from risk_utils import SimpleRiskModel, explain_risk


def load_model(path: str) -> Any:
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        # Fallback keeps the API usable even if the pickle is missing.
        return SimpleRiskModel()


app = Flask(__name__)
CORS(app)

model_path = os.environ.get(
    "MODEL_PATH", os.path.join(os.path.dirname(__file__), "risk_model.pk")
)
model = load_model(model_path)


def load_products() -> List[Dict[str, Any]]:
    products_path = os.path.join(os.path.dirname(__file__), "products.json")
    try:
        with open(products_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


REQUIRED_FIELDS = [
    "stock_amount",
    "weekly_sales",
    "product_age_days",
    "rating",
    "return_rate",
]


def parse_features(payload: Dict[str, Any]) -> Dict[str, float]:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")
    try:
        return {
            "stock_amount": float(payload["stock_amount"]),
            "weekly_sales": float(payload["weekly_sales"]),
            "product_age_days": float(payload["product_age_days"]),
            "rating": float(payload["rating"]),
            "return_rate": float(payload["return_rate"]),
        }
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid input types; all fields must be numeric") from exc


@app.route("/predict", methods=["POST"])
def predict() -> Any:
    data = request.get_json(silent=True) or {}
    try:
        features = parse_features(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    feature_vector = [
        [
            features["stock_amount"],
            features["weekly_sales"],
            features["product_age_days"],
            features["rating"],
            features["return_rate"],
        ]
    ]

    try:
        prediction = model.predict(feature_vector)[0]
    except Exception as exc:  # noqa: BLE001 - surfaced as API error
        return jsonify({"error": f"Model prediction failed: {exc}"}), 500

    response = {
        "risk": prediction,
        "explanations": explain_risk(features),
    }
    return jsonify(response)


@app.route("/products", methods=["GET"])
def products() -> Any:
    return jsonify({"products": load_products()})


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5005))
    app.run(host="0.0.0.0", port=port, debug=False)
