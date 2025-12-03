import json
import os
import pickle
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, List


try:
    # Vercel runs functions from repo root; adjust path to import helpers.
    from backend.risk_utils import SimpleRiskModel, explain_risk  # type: ignore
except Exception:
    from pathlib import Path
    import sys

    BASE_DIR = Path(__file__).resolve().parent.parent
    sys.path.append(str(BASE_DIR))
    from backend.risk_utils import SimpleRiskModel, explain_risk  # type: ignore


REQUIRED_FIELDS = [
    "stock_amount",
    "weekly_sales",
    "product_age_days",
    "rating",
    "return_rate",
]


def load_model() -> Any:
    base_path = os.path.join(os.path.dirname(__file__), "..", "backend")
    candidates = [
        os.environ.get("MODEL_PATH"),
        os.path.join(base_path, "risk_model.pkl"),
        os.path.join(base_path, "risk_model.pk"),
    ]
    for path in candidates:
        if not path:
            continue
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return SimpleRiskModel()


MODEL = load_model()


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


class handler(BaseHTTPRequestHandler):  # Vercel Python entrypoint
    def do_POST(self):
        request = self
        try:
            length = int(self.headers.get("content-length", 0))
            body_raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(body_raw.decode("utf-8"))
        except Exception:
            data = {}

        try:
            features = parse_features(data)
        except ValueError as exc:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
            return

        feature_vector: List[List[float]] = [
            [
                features["stock_amount"],
                features["weekly_sales"],
                features["product_age_days"],
                features["rating"],
                features["return_rate"],
            ]
        ]

        try:
            prediction = MODEL.predict(feature_vector)[0]
        except Exception:
            prediction = SimpleRiskModel().predict(feature_vector)[0]

        response = {
            "risk": prediction,
            "explanations": explain_risk(features),
        }

        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))
