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


def render_header() -> None:
    st.markdown(
        """
        <div class="section-card hero">
            <p class="eyebrow">Live inventory insights</p>
            <h1 class="page-title">Inventory Risk Radar</h1>
            <p class="lede">Streamlit view of your catalog with model-backed explanations for each risk check.</p>
            <div class="metric-row">
                <span class="metric-chip">Streamlit + Python</span>
                <span class="metric-chip">Flask model fallback ready</span>
                <span class="metric-chip">Catalog: backend/products.json</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {background: radial-gradient(circle at 10% 20%, #0f172a, #0b1220 60%); color: #e8edf5;}
            .block-container {padding-top: 1rem; max-width: 1200px;}
            h1, h2, h3, h4 {color: #f2f5fb;}
            .section-card {background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 1.3rem 1.5rem; box-shadow: 0 12px 40px rgba(0,0,0,0.35);}
            .hero {margin-bottom: 1rem;}
            .eyebrow {text-transform: uppercase; letter-spacing: 1px; font-size: 0.75rem; color: #8ea0c2; margin-bottom: 0.15rem;}
            .page-title {margin: 0 0 0.25rem 0; font-size: 2.4rem;}
            .lede {color: #c7d3e5; margin-bottom: 0.7rem;}
            .metric-row {display: flex; gap: 0.5rem; flex-wrap: wrap;}
            .metric-chip {display: inline-flex; align-items: center; padding: 0.45rem 0.75rem; border-radius: 999px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.1); color: #d8e0ee; font-size: 0.9rem;}
            div[data-testid="stForm"] {background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); padding: 1rem; border-radius: 14px;}
            div[data-testid="stForm"] button[kind="primary"] {width: 100%;}
            div[data-testid="column"] > div {background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.25);}
            .badge {text-transform: uppercase; letter-spacing: 0.5px;}
            .stMarkdown {color: #e8edf5;}
            .stCaption {color: #a6b6cf;}
            img {border-radius: 12px;}
            div[data-testid="stDivider"] {margin: 0.8rem 0;}
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

    render_header()

    render_custom_form()
    st.markdown("---")

    products = load_products()
    render_products(products)


if __name__ == "__main__":
    main()
