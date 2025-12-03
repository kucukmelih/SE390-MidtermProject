# Inventory Risk Radar

Flask + Bootstrap single-page app to score inventory risk with explanations.

## Quickstart

```bash
# 1) Create and activate a virtualenv
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2) Install backend dependencies
pip install -r requirements.txt

# 3) Ensure your trained model is available
# Default: backend/risk_model.pk (override with MODEL_PATH)

# 4) Run backend (port 5005 by default)
python -m backend.app
```
In a separate terminal for the frontend:

```bash
cd frontend
python -m http.server 8000
```

Open http://localhost:8000 and use “Check Risk”. The page calls the backend at http://localhost:5005/predict.

## Endpoints

- `POST /predict` — JSON body:
  ```json
  {
    "stock_amount": 800,
    "weekly_sales": 2,
    "product_age_days": 300,
    "rating": 2.1,
    "return_rate": 0.25
  }
  ```
  Returns:
  ```json
  {
    "risk": "High",
    "explanations": ["Very high stock level", "Very low weekly sales", "..."]
  }
  ```
- `GET /products` — Small sample catalog used by the frontend.

## Files & Structure

- `backend/app.py` — Flask API, loads model (`risk_model.pk` by default), exposes `/predict` and `/products`.
- `backend/risk_utils.py` — Simple fallback model + rule-based explanations.
- `backend/products.json` — Sample product data.
- `frontend/index.html` — UI with product cards + custom scenario form.
- `frontend/script.js` — Fetches products, calls `/predict`, handles risk UI.
- `frontend/styles.css` — Styling/theme.
- `requirements.txt` — Backend deps (Flask, CORS, sklearn, pandas, numpy).

## Notes

- Default backend port: 5005 (override with `PORT` env var).
- Model path override: set `MODEL_PATH` to your pickle if not using `backend/risk_model.pk`.
- The provided trained model reports ~97.5% accuracy.
