import json
import os
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st

from backend.risk_utils import SimpleRiskModel, explain_risk


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"


@st.cache_resource
def get_model() -> Any:
    """Load the saved model or fall back to the simple rules-based model."""
    model_path = Path(os.environ.get("MODEL_PATH", BACKEND_DIR / "risk_model.pkl"))
    try:
        with open(model_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return SimpleRiskModel()
    except Exception:
        st.warning("Model failed to load; using the fallback rules-based model.")
        return SimpleRiskModel()


@st.cache_data
def load_products() -> List[Dict[str, Any]]:
    products_path = BACKEND_DIR / "products.json"
    try:
        with open(products_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def predict_risk(features: Dict[str, float]) -> Tuple[str, List[str]]:
    model = get_model()
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
        risk = model.predict(feature_vector)[0]
    except Exception:
        risk = SimpleRiskModel().predict(feature_vector)[0]
    explanations = explain_risk(features)
    return risk, explanations


def risk_badge(risk: str) -> str:
    colors = {
        "High": ("#dc3545", "#fff"),
        "Medium": ("#ffc107", "#212529"),
        "Low": ("#28a745", "#fff"),
    }
    bg, fg = colors.get(risk, ("#6c757d", "#fff"))
    return f"<span class='badge' style='background:{bg};color:{fg};padding:0.35rem 0.6rem;border-radius:999px;font-size:0.9rem'>{risk} risk</span>"


def render_result(risk: str, explanations: List[str]) -> None:
    st.markdown(risk_badge(risk), unsafe_allow_html=True)
    st.markdown("**Model notes**")
    if explanations:
        for item in explanations:
            st.write(f"- {item}")
    else:
        st.write("- No specific drivers found.")


def render_custom_form() -> None:
    st.subheader("Try your own numbers")
    st.caption("Fill the form and run the risk check instantly.")

    with st.form("custom_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            stock_amount = st.number_input("Stock amount", min_value=0, value=500, step=10)
            product_age_days = st.number_input("Product age (days)", min_value=0, value=120, step=5)
        with col2:
            weekly_sales = st.number_input("Weekly sales", min_value=0, value=8, step=1)
            rating = st.number_input("Rating (1-5)", min_value=0.0, max_value=5.0, value=3.7, step=0.1)
        with col3:
            return_rate = st.number_input("Return rate (0-1)", min_value=0.0, max_value=1.0, value=0.12, step=0.01)

        submitted = st.form_submit_button("Check risk")

    if submitted:
        features = {
            "stock_amount": float(stock_amount),
            "weekly_sales": float(weekly_sales),
            "product_age_days": float(product_age_days),
            "rating": float(rating),
            "return_rate": float(return_rate),
        }
        risk, explanations = predict_risk(features)
        render_result(risk, explanations)


def render_products(products: List[Dict[str, Any]]) -> None:
    if not products:
        st.info("No sample products found. Add items to backend/products.json to see cards here.")
        return

    st.subheader("Sample catalog")
    st.caption("Check risk for preloaded products.")

    cols = st.columns(3)
    for idx, product in enumerate(products):
        col = cols[idx % 3]
        with col:
            st.markdown(f"**{product['name']}**")
            st.caption(product.get("category", "Inventory"))
            if product.get("image"):
                st.image(product["image"], use_column_width=True)
            st.write(product.get("description", ""))
            st.write(
                f"Stock: {product['stock_amount']} | Weekly sales: {product['weekly_sales']} | Age: {product['product_age_days']} days"
            )
            st.write(f"Rating: {product['rating']} | Returns: {product['return_rate']*100:.0f}%")

            if st.button("Check risk", key=f"btn-{product['id']}"):
                features = {
                    "stock_amount": float(product["stock_amount"]),
                    "weekly_sales": float(product["weekly_sales"]),
                    "product_age_days": float(product["product_age_days"]),
                    "rating": float(product["rating"]),
                    "return_rate": float(product["return_rate"]),
                }
                risk, explanations = predict_risk(features)
                st.session_state.setdefault("product_results", {})[product["id"]] = (risk, explanations)

            results = st.session_state.get("product_results", {}).get(product["id"])
            if results:
                risk, explanations = results
                render_result(risk, explanations)
            st.divider()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {background: radial-gradient(circle at 10% 20%, #1b2735, #0d1117 60%);}
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Inventory Risk Radar",
        page_icon="IR",
        layout="wide",
    )
    inject_styles()

    st.title("Inventory Risk Radar")
    st.write("Streamlit dashboard to check stock risk with model-backed explanations.")
    st.caption("Model fallback keeps the app working even if the pickle file is missing.")

    render_custom_form()
    st.markdown("---")

    products = load_products()
    render_products(products)


if __name__ == "__main__":
    main()
