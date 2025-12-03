import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, List


def load_products() -> List[Dict[str, Any]]:
    base_path = os.path.join(os.path.dirname(__file__), "..", "backend", "products.json")
    try:
        with open(base_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


PRODUCTS = load_products()


class handler(BaseHTTPRequestHandler):  # Vercel Python entrypoint
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"products": PRODUCTS}).encode("utf-8"))
