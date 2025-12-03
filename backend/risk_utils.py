from typing import Dict, List


class SimpleRiskModel:
    """Lightweight classifier to keep the demo self contained."""

    def predict(self, rows: List[List[float]]) -> List[str]:
        predictions: List[str] = []
        for row in rows:
            stock, weekly_sales, product_age_days, rating, return_rate = row
            score = 0

            if stock > 600:
                score += 2
            elif stock > 300:
                score += 1

            if weekly_sales < 3:
                score += 2
            elif weekly_sales < 10:
                score += 1
            else:
                score -= 1

            if product_age_days > 250:
                score += 2
            elif product_age_days > 120:
                score += 1

            if rating < 2.5:
                score += 2
            elif rating < 3.5:
                score += 1
            else:
                score -= 1

            if return_rate > 0.20:
                score += 2
            elif return_rate > 0.10:
                score += 1

            if score >= 6:
                predictions.append("High")
            elif score >= 3:
                predictions.append("Medium")
            else:
                predictions.append("Low")

        return predictions


def explain_risk(features: Dict[str, float]) -> List[str]:
    reasons: List[str] = []
    if features["stock_amount"] > 600:
        reasons.append("Very high stock level")
    elif features["stock_amount"] > 300:
        reasons.append("High stock level")
    if features["weekly_sales"] < 3:
        reasons.append("Very low weekly sales")
    elif features["weekly_sales"] < 10:
        reasons.append("Slowing demand / low weekly sales")
    if features["product_age_days"] > 250:
        reasons.append("Product has been in inventory for a long time")
    elif features["product_age_days"] > 120:
        reasons.append("Product age is increasing (mid-term shelf time)")
    if features["rating"] < 2.5:
        reasons.append("Low customer rating (reduces purchase probability)")
    elif features["rating"] < 3.5:
        reasons.append("Average customer rating")
    if features["return_rate"] > 0.20:
        reasons.append("High return rate (indicates product quality issues)")
    elif features["return_rate"] > 0.10:
        reasons.append("Moderately high return rate")
    return reasons
