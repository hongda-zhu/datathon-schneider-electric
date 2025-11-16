# -*- coding: utf-8 -*-
"""
Schneider Electric Datathon - Explainable AI Dashboard
Final version with tooltips, LLM-generated insights, and professional UX
"""

import streamlit as st
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
from pathlib import Path

# ============================================================
# FEATURE TRANSLATIONS TO BUSINESS LANGUAGE
# ============================================================

FEATURE_TRANSLATIONS = {
    "customer_activity": "Customer Activity Level",
    "customer_engagement": "Customer Engagement",
    "total_competitors": "Total Competitors",
    "competitor_diversity": "Competitor Diversity",
    "opp_old": "Opportunity Age",
    "opp_maturity": "Opportunity Maturity",
    "opp_quality_score": "Opportunity Quality Score",
    "product_A_ratio": "Product A Sales Ratio",
    "total_past_sales": "Total Historical Sales",
    "cust_hitrate": "Customer Success Rate",
    "cust_interactions": "Customer Interactions",
    "cust_contracts": "Customer Contracts",
    "has_competition": "Has Competition",
    "competition_risk": "Competitive Risk",
    "product_mix": "Product Mix",
    "product_count": "Product Count",
    "iberia_competition": "Iberia Competition",
    "iberia_engagement": "Iberia Engagement",
    "has_past_sales": "Has Past Sales",
    "contract_hitrate_ratio": "Contract/Success Ratio",
    "hitrate_interaction": "Success × Interaction",
    "hitrate_contracts": "Success × Contracts",
    "competition_engagement": "Competition × Engagement",
    "low_engagement_risk": "Low Engagement Risk",
    "opp_age_squared": "Opportunity Age²",
    "is_new_opp": "Is New Opportunity",
    "is_mature_opp": "Is Mature Opportunity",
    "product_A": "Product A",
    "product_C": "Product C",
    "product_D": "Product D",
    "competitor_X": "Competitor X",
    "competitor_Y": "Competitor Y",
    "competitor_Z": "Competitor Z",
    "cust_in_iberia": "Customer in Iberia",
    "product_A_sold_in_the_past": "Product A (Historical)",
    "product_B_sold_in_the_past": "Product B (Historical)",
    "product_A_recommended": "Product A Recommended",
    "opp_month": "Opportunity Month"
}

# Tooltips for metrics
METRIC_HELP = {
    "f1_score": """
    **F1 Score (0 to 1)**: Harmonic mean of Precision and Recall, balancing both metrics.

    • **High (>0.7)**: Model is very reliable
    • **Medium (0.5-0.7)**: Useful, with room for improvement
    • **Low (<0.5)**: Needs significant tuning

    *Calculated on test set by comparing predictions vs. actual outcomes.*
    """,

    "auc": """
    **AUC - Area Under ROC Curve (0 to 1)**: Measures how well the model distinguishes between winning and losing opportunities.

    • **0.9-1.0**: Excellent discrimination
    • **0.8-0.9**: Very good
    • **0.7-0.8**: Acceptable
    • **<0.7**: Needs improvement

    *An AUC of 0.85 means the model has 85% probability of correctly ranking a winning opportunity above a losing one.*
    """,

    "precision": """
    **Precision (0 to 1)**: Of all opportunities the model predicts as wins, what percentage actually win?

    • **High**: Few false alarms
    • **Low**: Many predicted wins that actually lose

    *Useful when the cost of pursuing a losing opportunity is high.*
    """,

    "recall": """
    **Recall/Sensitivity (0 to 1)**: Of all opportunities that actually won, what percentage did the model identify?

    • **High**: Captures most winning opportunities
    • **Low**: Misses many valuable opportunities

    *Useful when you don't want to miss any potential wins.*
    """,

    "threshold": """
    **Decision Threshold (0 to 1)**: The probability cutoff where we classify an opportunity as "Win" vs "Loss".

    • If probability ≥ threshold → Prediction: Win
    • If probability < threshold → Prediction: Loss

    *This value is optimized to maximize F1 Score on your data.*
    """,

    "total_samples": """
    **Total Samples**: Number of opportunities analyzed in the test set.

    *This is 20% of your total data, reserved for model validation.*
    """,

    "predicted_wins": """
    **Predicted Wins**: Number of opportunities the model classifies as wins.

    *Based on the optimized decision threshold.*
    """,

    "win_rate": """
    **Predicted Win Rate**: Percentage of opportunities the model expects you to win.

    *Useful for estimating your sales pipeline and resource allocation.*
    """
}

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Schneider Electric - Opportunity Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS
st.markdown("""
<style>
    /* Headers */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #2c3e50;
        border-bottom: 3px solid #3ECEAC;
        padding-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #34495e;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }

    /* Enhanced cards with gradients and better contrast */
    .insight-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        color: #1a1a1a;  /* Dark text for better contrast */
    }
    .insight-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        color: #1a1a1a;  /* Dark text for better contrast */
    }
    .warning-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    .success-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        color: #1a1a1a;  /* Dark text for better contrast */
    }
    .success-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }

    /* Lists */
    .insight-box ul, .warning-box ul, .success-box ul {
        margin: 0.75rem 0;
        padding-left: 1.5rem;
    }
    .insight-box li, .warning-box li, .success-box li {
        margin: 0.75rem 0;
        line-height: 1.7;
        font-size: 1rem;
    }

    /* Chart descriptions */
    .chart-description {
        background: #f8f9fa;
        padding: 1.25rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0;
        font-size: 0.95rem;
        color: #212529;  /* Darker for better contrast */
        border-left: 4px solid #6c757d;
        line-height: 1.6;
    }

    /* Schneider Electric brand colors */
    .brand-accent {
        color: #3ECEAC;
        font-weight: 600;
    }

    /* Combined insights box */
    .combined-insights-box {
        background: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 0.75rem;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        line-height: 1.8;
        color: #1a1a1a;
    }

    .insights-section {
        margin-bottom: 1.5rem;
        text-align: justify;
    }

    .recommendations-section {
        text-align: justify;
    }

    .combined-insights-box strong {
        display: inline-block;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def translate_feature(feature_name):
    """Translate technical name to business language"""
    return FEATURE_TRANSLATIONS.get(feature_name, feature_name.replace("_", " ").title())

def get_metric_help(metric_key):
    """Get explanatory tooltip for a metric"""
    return METRIC_HELP.get(metric_key, "")

def get_feature_context(feature_name, value, feature_stats):
    """Get context label (Low/Avg/High) for a feature value"""
    if feature_name not in feature_stats:
        return "", ""  # No context available

    stats = feature_stats[feature_name]
    p25 = stats["p25"]
    p75 = stats["p75"]

    # Determine label and delta
    if value < p25:
        label = "Low"
        delta_color = "off"  # Gray/neutral
    elif value > p75:
        label = "High"
        delta_color = "normal"  # Green (positive)
    else:
        label = "Average"
        delta_color = "off"

    # For competitors, reverse the interpretation (fewer is better)
    if "compet" in feature_name.lower():
        if value < p25:
            label = "Low (Good)"
            delta_color = "normal"
        elif value > p75:
            label = "High (Concern)"
            delta_color = "inverse"  # Red

    return label, delta_color

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_resource
def load_model():
    """Load trained XGBoost model"""
    return joblib.load("output/model.pkl")

@st.cache_resource
def load_explainer():
    """Load SHAP explainer"""
    return joblib.load("output/explainer.pkl")

@st.cache_data
def load_test_data():
    """Load test data"""
    X_test = joblib.load("output/X_test.pkl")
    y_test = joblib.load("output/y_test.pkl")
    return X_test, y_test

@st.cache_data
def load_shap_values():
    """Load pre-computed SHAP values"""
    return joblib.load("output/shap_values.pkl")

@st.cache_data
def load_global_insights():
    """Load global insights JSON"""
    with open("output/json/global_insights.json") as f:
        return json.load(f)

@st.cache_data
def load_feature_names():
    """Load feature names"""
    return joblib.load("output/feature_names.pkl")

@st.cache_data
def load_threshold():
    """Load optimal threshold"""
    with open("output/threshold.txt") as f:
        return float(f.read().strip())

def load_case_json(case_id):
    """Load individual case analysis"""
    json_path = Path(f"output/json/{case_id}.json")
    if json_path.exists():
        with open(json_path) as f:
            return json.load(f)
    return None

def summarize_shap(values, names, top_k=3):
    """Return textual summary of most positive/negative SHAP contributors"""
    pairs = list(zip(names, values))
    sorted_pairs = sorted(pairs, key=lambda x: abs(x[1]), reverse=True)
    positives = [(translate_feature(f), v) for f, v in sorted_pairs if v > 0][:top_k]
    negatives = [(translate_feature(f), v) for f, v in sorted_pairs if v < 0][:top_k]
    return positives, negatives

# Load all data
try:
    model = load_model()
    explainer = load_explainer()
    X_test, y_test = load_test_data()
    shap_values = load_shap_values()
    global_insights = load_global_insights()
    feature_names = load_feature_names()
    threshold = load_threshold()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.info("ℹ️ Make sure the `output/` folder is in the same directory as this script.")
    st.stop()

# ============================================================
# HELPER FUNCTIONS (continued)
# ============================================================
def get_prediction(row):
    """Get model prediction for a single row"""
    prob = model.predict_proba([row])[0][1]
    pred = int(prob >= threshold)
    return prob, pred

def plot_shap_waterfall(shap_row, row, base_value):
    """Create SHAP waterfall plot with translated names"""
    fig, ax = plt.subplots(figsize=(10, 6))
    shap.plots.waterfall(
        shap.Explanation(
            values=shap_row,
            base_values=base_value,
            data=row.values,
            feature_names=[translate_feature(f) for f in feature_names]
        ),
        show=False
    )
    st.pyplot(fig)
    plt.close()

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("## ⚡ Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["🌍 Global Insights", "🔍 Case Explorer", "🎲 What-If Simulator"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Model Performance")
perf = global_insights["model_performance"]

st.sidebar.metric(
    "F1 Score",
    f"{perf['f1_score']:.3f}",
    help=get_metric_help("f1_score")
)
st.sidebar.metric(
    "AUC",
    f"{perf['auc']:.3f}",
    help=get_metric_help("auc")
)
st.sidebar.metric(
    "Threshold",
    f"{perf['threshold']:.3f}",
    help=get_metric_help("threshold")
)

# ============================================================
# PAGE 1: GLOBAL INSIGHTS
# ============================================================
if page == "🌍 Global Insights":
    st.markdown('<div class="main-header">🌍 Global Model Insights</div>', unsafe_allow_html=True)
    st.markdown("**Comprehensive overview of model performance and key patterns across all opportunities**")

    # Combined insights and recommendations at the top
    st.markdown("---")

    insights_text = " ".join(global_insights["business_insights"])
    recommendations_text = " ".join(global_insights["recommendations"])

    combined_html = f"""
    <div class='combined-insights-box'>
        <div class='insights-section'>
            <strong style='color: #2196f3; font-size: 1.1rem;'>💡 Key Insights:</strong> {insights_text}
        </div>
        <div class='recommendations-section'>
            <strong style='color: #4caf50; font-size: 1.1rem;'>🎯 Recommendations:</strong> {recommendations_text}
        </div>
    </div>
    """
    st.markdown(combined_html, unsafe_allow_html=True)

    st.markdown("---")

    # Performance metrics
    st.markdown('<div class="sub-header">📈 Model Performance Metrics</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "F1 Score",
        f"{perf['f1_score']:.3f}",
        help=get_metric_help("f1_score")
    )
    col2.metric(
        "AUC",
        f"{perf['auc']:.3f}",
        help=get_metric_help("auc")
    )
    col3.metric(
        "Precision",
        f"{perf['precision']:.3f}",
        help=get_metric_help("precision")
    )
    col4.metric(
        "Recall",
        f"{perf['recall']:.3f}",
        help=get_metric_help("recall")
    )

    # Prediction distribution
    st.markdown('<div class="sub-header">📊 Prediction Distribution</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-description">
    📌 <strong>What does this mean?</strong> Of all opportunities analyzed in the test set,
    the model predicts how many will be won vs. lost. This helps estimate your sales pipeline
    and resource allocation needs.
    </div>
    """, unsafe_allow_html=True)

    dist = global_insights["prediction_distribution"]
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Opportunities",
        dist['total_samples'],
        help=get_metric_help("total_samples")
    )
    col2.metric(
        "Predicted Wins",
        dist['predicted_wins'],
        help=get_metric_help("predicted_wins")
    )
    col3.metric(
        "Win Rate",
        f"{dist['win_rate']:.1%}",
        help=get_metric_help("win_rate")
    )

    # Probability buckets visualization
    if "probability_buckets" in dist:
        st.markdown("---")
        st.markdown("**Win Probability Distribution**")

        buckets_df = pd.DataFrame({
            "Confidence Level": list(dist["probability_buckets"].keys()),
            "Number of Opportunities": list(dist["probability_buckets"].values())
        })

        st.bar_chart(buckets_df.set_index("Confidence Level"))
        st.caption("Distribution of opportunities by predicted win probability. Focus resources on moving Medium deals to High/Very High categories.")

    # Feature importance
    st.markdown('<div class="sub-header">🔝 Top Influential Features</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-description">
    📌 <strong>What does this mean?</strong> These are the variables that have the most weight
    in determining whether an opportunity is won or lost. <strong>Focus on improving features
    with the highest bars</strong> to increase your win probability.
    <br><br>
    <strong>Source:</strong> Feature importance scores from XGBoost model, calculated based on
    how frequently and effectively each feature is used for decision splits across all trees.
    </div>
    """, unsafe_allow_html=True)

    feat_imp = global_insights["feature_importance_top20"]
    feat_df = pd.DataFrame({
        "Feature": [translate_feature(f) for f in list(feat_imp.keys())[:10]],
        "Importance": list(feat_imp.values())[:10]
    })
    st.bar_chart(feat_df.set_index("Feature"))

    # SHAP summary
    st.markdown('<div class="sub-header">🧠 Feature Impact on Win Probability</div>', unsafe_allow_html=True)

    if Path("output/images/shap_summary.png").exists():
        st.image("output/images/shap_summary.png", use_container_width=True)
        st.caption("Each dot represents an opportunity. Red = high feature value, Blue = low feature value. Right side increases win chance, left side decreases it.")

    # SHAP drivers textual summary
    if "shap_drivers" in global_insights:
        st.markdown("**Key Drivers:**")

        col_pos, col_neg = st.columns(2)

        with col_pos:
            st.markdown("**✅ Increase Win Chance:**")
            for driver in global_insights["shap_drivers"]["top_positive"]:
                feat_name = translate_feature(driver["feature"])
                shap_val = driver["mean_shap"]
                st.markdown(f"• **{feat_name}** (+{shap_val:.3f})")

        with col_neg:
            st.markdown("**⚠️ Decrease Win Chance:**")
            for driver in global_insights["shap_drivers"]["top_negative"]:
                feat_name = translate_feature(driver["feature"])
                shap_val = driver["mean_shap"]
                st.markdown(f"• **{feat_name}** ({shap_val:.3f})")

        st.caption("Average SHAP values across all opportunities. Positive values push predictions toward win, negative values toward loss.")


# ============================================================
# PAGE 2: CASE EXPLORER
# ============================================================
elif page == "🔍 Case Explorer":
    st.markdown('<div class="main-header">🔍 Individual Opportunity Analysis</div>', unsafe_allow_html=True)
    st.markdown("**Explore detailed predictions and explanations for specific opportunities**")

    # Case ID input
    available_ids = X_test.index.tolist()
    case_id = st.selectbox("Select Opportunity ID", available_ids, index=0)

    if case_id is not None:
        # Get row data
        row_pos = X_test.index.get_loc(case_id)
        row = X_test.loc[case_id]
        actual = int(y_test.loc[case_id])
        shap_row = shap_values[row_pos]

        # Get prediction
        prob, pred = get_prediction(row)

        # Load JSON if exists
        case_json = load_case_json(case_id)

        # Prediction results
        st.markdown('<div class="sub-header">🎯 Prediction Results</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Opportunity ID", str(case_id))
        col2.metric(
            "Win Probability",
            f"{prob:.1%}",
            help="Model's estimated probability that this opportunity will be won"
        )
        col3.metric(
            "Prediction",
            "🏆 Win" if pred == 1 else "❌ Loss",
            help=f"Classification based on threshold of {threshold:.3f}"
        )
        col4.metric(
            "Actual Outcome",
            "🏆 Win" if actual == 1 else "❌ Loss",
            help="Real outcome of this opportunity"
        )

        # Confidence indicator with explanation
        threshold_distance = (prob - threshold) * 100  # in percentage points

        # Get top factors for explanation
        top_positive = []
        top_negative = []
        if case_json and "shap_analysis" in case_json:
            top_positive = case_json["shap_analysis"]["top_positive_factors"][:2]
            top_negative = case_json["shap_analysis"]["top_negative_factors"][:2]

        # Determine confidence based on distance from threshold
        if threshold_distance > 40:  # >40pp above threshold
            confidence_level = "High"
            confidence_emoji = "✅"
            confidence_class = "success-box"
            explanation = f"Probability ({prob:.1%}) exceeds threshold ({threshold:.1%}) by {threshold_distance:.1f} percentage points."
            if top_positive:
                top_factor = translate_feature(top_positive[0]["feature"])
                explanation += f" Strong positive signals from {top_factor}."
        elif threshold_distance > 10:  # 10-40pp above threshold
            confidence_level = "Medium-High"
            confidence_emoji = "✅"
            confidence_class = "success-box"
            explanation = f"Probability ({prob:.1%}) is {threshold_distance:.1f}pp above threshold ({threshold:.1%})."
            if top_negative:
                top_concern = translate_feature(top_negative[0]["feature"])
                explanation += f" Watch for potential issues with {top_concern}."
        elif threshold_distance > 0:  # 0-10pp above threshold
            confidence_level = "Medium"
            confidence_emoji = "⚠️"
            confidence_class = "warning-box"
            explanation = f"Probability ({prob:.1%}) barely exceeds threshold ({threshold:.1%}) by only {threshold_distance:.1f}pp."
            if top_negative:
                top_concern = translate_feature(top_negative[0]["feature"])
                explanation += f" Negative signals from {top_concern} are holding it back."
        else:  # Below threshold
            confidence_level = "Low"
            confidence_emoji = "❌"
            confidence_class = "warning-box"
            explanation = f"Probability ({prob:.1%}) is {abs(threshold_distance):.1f}pp below threshold ({threshold:.1%})."
            if top_negative:
                main_blocker = translate_feature(top_negative[0]["feature"])
                explanation += f" Main blocker: {main_blocker}."

        st.markdown(
            f'<div class="{confidence_class}">{confidence_emoji} <strong>{confidence_level} Confidence:</strong> {explanation}</div>',
            unsafe_allow_html=True
        )

        # Key features
        st.markdown('<div class="sub-header">📊 Key Features for This Opportunity</div>', unsafe_allow_html=True)
        if case_json:
            key_feats = case_json["key_features"]
            feature_stats = global_insights.get("feature_statistics", {})

            col1, col2, col3 = st.columns(3)

            # Customer Activity
            cust_act_val = key_feats['customer_activity']
            cust_act_label, _ = get_feature_context("customer_activity", cust_act_val, feature_stats)
            col1.metric(
                translate_feature("customer_activity"),
                f"{cust_act_val:.3f}",
                delta=cust_act_label if cust_act_label else None,
                help="Customer activity level (average of hit rate, interactions, and contracts)"
            )

            # Total Competitors
            comp_val = key_feats['total_competitors']
            comp_label, _ = get_feature_context("total_competitors", comp_val, feature_stats)
            col2.metric(
                translate_feature("total_competitors"),
                f"{comp_val:.0f}",
                delta=comp_label if comp_label else None,
                help="Total number of competitors present in this opportunity"
            )

            # Opportunity Age
            opp_age_val = key_feats['opp_old']
            opp_age_label, _ = get_feature_context("opp_old", opp_age_val, feature_stats)
            col3.metric(
                translate_feature("opp_old"),
                f"{opp_age_val:.3f}",
                delta=opp_age_label if opp_age_label else None,
                help="Opportunity age (normalized)"
            )

        # Top SHAP Factors
        if case_json and "shap_analysis" in case_json:
            st.markdown('<div class="sub-header">🔍 Key Drivers for This Opportunity</div>', unsafe_allow_html=True)

            col_win, col_loss = st.columns(2)

            with col_win:
                st.markdown("**✅ What Pushes Toward Win:**")
                for factor in case_json["shap_analysis"]["top_positive_factors"][:3]:
                    feat_name = translate_feature(factor["feature"])
                    shap_val = factor["shap_value"]
                    st.markdown(f"• **{feat_name}** (+{shap_val:.3f})")

            with col_loss:
                st.markdown("**⚠️ What Holds It Back:**")
                if case_json["shap_analysis"]["top_negative_factors"]:
                    for factor in case_json["shap_analysis"]["top_negative_factors"][:3]:
                        feat_name = translate_feature(factor["feature"])
                        shap_val = factor["shap_value"]
                        st.markdown(f"• **{feat_name}** ({shap_val:.3f})")
                else:
                    st.markdown("• *No significant negative factors*")

            st.caption("SHAP values show how each feature affects this specific prediction. Larger absolute values = stronger influence.")

        # SHAP Waterfall
        st.markdown('<div class="sub-header">🌊 Why This Prediction?</div>', unsafe_allow_html=True)

        base_val = explainer.expected_value
        if isinstance(base_val, (list, np.ndarray)):
            base_val = float(base_val[1] if len(np.atleast_1d(base_val)) > 1 else base_val[0])
        plot_shap_waterfall(shap_row, row, base_val)
        st.caption("Red bars push probability UP (toward win), blue bars push it DOWN (toward loss). Starting from average, each feature adjusts the final prediction.")

        # SHAP waterfall summary
        if case_json and "shap_analysis" in case_json:
            top_pos = case_json["shap_analysis"]["top_positive_factors"]
            top_neg = case_json["shap_analysis"]["top_negative_factors"]

            summary_parts = []

            if top_pos:
                top_pos_name = translate_feature(top_pos[0]["feature"])
                top_pos_val = top_pos[0]["shap_value"]
                summary_parts.append(f"**Strongest positive push:** {top_pos_name} (+{top_pos_val:.2f})")

            if len(top_pos) > 1:
                second_pos_name = translate_feature(top_pos[1]["feature"])
                second_pos_val = top_pos[1]["shap_value"]
                summary_parts.append(f"{second_pos_name} (+{second_pos_val:.2f})")

            if top_neg:
                top_neg_name = translate_feature(top_neg[0]["feature"])
                top_neg_val = top_neg[0]["shap_value"]
                summary_parts.append(f"**Main obstacle:** {top_neg_name} ({top_neg_val:.2f})")

            if summary_parts:
                st.info("📝 **Summary:** " + " | ".join(summary_parts))

        # SHAP glossary (expandable)
        with st.expander("ℹ️ Understanding SHAP Waterfall Charts"):
            st.markdown("""
            **What is SHAP?**
            - SHAP (SHapley Additive exPlanations) shows how each feature contributes to the final prediction
            - Based on game theory - fairly distributes "credit" for the prediction

            **How to read the waterfall:**
            - **Base Value:** The average prediction across all opportunities (starting point)
            - **Red bars (positive):** Push the prediction UP (toward win)
            - **Blue bars (negative):** Push the prediction DOWN (toward loss)
            - **Final Value:** Where we end up after all features are considered

            **Key insights:**
            - Longer bars = stronger influence
            - The order shows relative importance for THIS specific opportunity
            - All bars sum up to explain the difference between base value and final prediction
            """)

        # Business recommendation
        if case_json and "business_recommendation" in case_json:
            st.markdown('<div class="sub-header">🎯 Recommended Action</div>', unsafe_allow_html=True)
            rec = case_json["business_recommendation"]

            st.markdown(f"""
            <div class='success-box'>
            <strong>Recommended Action:</strong> {rec['action']}<br>
            <strong>Priority Level:</strong> {rec['priority']}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("**Next Steps:**")
            for i, step in enumerate(rec['next_steps'], 1):
                st.markdown(f"{i}. {step}")

# ============================================================
# PAGE 3: WHAT-IF SIMULATOR
# ============================================================
elif page == "🎲 What-If Simulator":
    st.markdown('<div class="main-header">🎲 What-If Scenario Simulator</div>', unsafe_allow_html=True)
    st.markdown("**Simulate changes to key variables and observe real-time impact on win probability**")

    # Select base case
    available_ids = X_test.index.tolist()
    base_id = st.selectbox("Select Base Opportunity", available_ids, index=0)

    if base_id is not None:
        row_pos = X_test.index.get_loc(base_id)
        original_row = X_test.loc[base_id].copy()

        # Get original prediction
        original_prob, original_pred = get_prediction(original_row)

        # Display original
        st.markdown('<div class="sub-header">📍 Original State</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Original Probability", f"{original_prob:.1%}")
        col2.metric("Prediction", "🏆 Win" if original_pred == 1 else "❌ Loss")
        col3.metric(
            "Confidence",
            "High" if abs(original_prob - 0.5) > 0.3 else "Medium"
        )

        st.markdown("---")

        # Preset actions
        st.markdown('<div class="sub-header">⚡ Quick Scenarios</div>', unsafe_allow_html=True)
        st.markdown("Apply common business scenarios to auto-adjust sliders and instantly see the impact.")

        preset_options = [
            ("interactions_up", {
                "label": "📈 +20% Interactions",
                "short": "+20% Interactions",
                "description": "Boost customer interactions by 20% (capped at 2.0) to simulate extra touchpoints."
            }),
            ("reduce_comp", {
                "label": "🎯 Reduce Competitors",
                "short": "-1 Competitor",
                "description": "Remove one competitor to test the impact of a less crowded deal."
            }),
            ("fast_track", {
                "label": "⚡ Fast-Track (New)",
                "short": "Fast-track Opportunity",
                "description": "Set opportunity age to very new (-1.0) to mimic speeding up the cycle."
            }),
            ("reset", {
                "label": "🔄 Reset to Original",
                "short": "Reset sliders",
                "description": "Return all sliders to their original values."
            })
        ]

        preset_meta_map = {key: meta for key, meta in preset_options}

        preset_action = None
        preset_cols = st.columns(len(preset_options))
        for (option, meta), col in zip(preset_options, preset_cols):
            with col:
                if st.button(meta["label"], use_container_width=True):
                    preset_action = option
                st.caption(meta["description"])

        if preset_action:
            if preset_action == "reset":
                st.info("Resetting sliders to the original opportunity values.")
            else:
                meta = preset_meta_map[preset_action]
                st.success(f"Scenario applied: {meta['short']} — {meta['description']}")

        st.markdown("---")

        # What-if controls
        st.markdown('<div class="sub-header">🎛️ Adjust Variables</div>', unsafe_allow_html=True)

        modified_row = original_row.copy()

        # Apply preset if selected
        if preset_action == "interactions_up" and 'cust_interactions' in feature_names:
            modified_row['cust_interactions'] = min(2.0, original_row.get('cust_interactions', 0.5) * 1.2)
        elif preset_action == "reduce_comp" and 'total_competitors' in feature_names:
            modified_row['total_competitors'] = max(0, int(original_row.get('total_competitors', 2)) - 1)
        elif preset_action == "fast_track" and 'opp_old' in feature_names:
            modified_row['opp_old'] = -1.0  # Make it new

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**🤝 Customer Engagement**")
            if 'cust_interactions' in feature_names:
                feature_stats = global_insights.get("feature_statistics", {})
                current_val = float(modified_row.get('cust_interactions', 0.5))

                # Get context for help text
                stats = feature_stats.get('cust_interactions', {})
                help_text = "Number of interactions with the customer (normalized)"
                if stats:
                    help_text += f"\n• Average: {stats.get('median', 0):.2f}\n• P25: {stats.get('p25', 0):.2f}, P75: {stats.get('p75', 0):.2f}"

                new_interactions = st.slider(
                    translate_feature("cust_interactions"),
                    min_value=0.0,
                    max_value=2.0,
                    value=current_val,
                    step=0.1,
                    help=help_text,
                    key="slider_interactions"
                )
                modified_row['cust_interactions'] = new_interactions

            if 'cust_hitrate' in feature_names:
                current_val = float(modified_row.get('cust_hitrate', 0.5))

                feature_stats = global_insights.get("feature_statistics", {})
                stats = feature_stats.get('cust_hitrate', {})
                help_text = "Historical success rate with this customer (0-1)"
                if stats:
                    help_text += f"\n• Average: {stats.get('median', 0):.2f}\n• P25: {stats.get('p25', 0):.2f}, P75: {stats.get('p75', 0):.2f}"

                new_hitrate = st.slider(
                    translate_feature("cust_hitrate"),
                    min_value=0.0,
                    max_value=1.0,
                    value=current_val,
                    step=0.05,
                    help=help_text,
                    key="slider_hitrate"
                )
                modified_row['cust_hitrate'] = new_hitrate

        with col2:
            st.markdown("**📊 Opportunity Characteristics**")
            if 'opp_old' in feature_names:
                current_val = float(modified_row.get('opp_old', 0.0))

                new_opp_age = st.slider(
                    translate_feature("opp_old"),
                    min_value=-2.0,
                    max_value=2.0,
                    value=current_val,
                    step=0.1,
                    help="Opportunity age (standardized)\n• -2 = Very new\n• 0 = Average age\n• +2 = Very old",
                    key="slider_opp_old"
                )
                modified_row['opp_old'] = new_opp_age

            if 'total_competitors' in feature_names:
                current_val = int(modified_row.get('total_competitors', 0))

                new_competitors = st.slider(
                    translate_feature("total_competitors"),
                    min_value=0,
                    max_value=5,
                    value=current_val,
                    step=1,
                    help="Number of active competitors\n• 0 = No competition (best)\n• 1-2 = Moderate competition\n• 3+ = High competition (challenging)",
                    key="slider_competitors"
                )
                modified_row['total_competitors'] = float(new_competitors)

        # Recalculate derived features
        if 'customer_activity' in feature_names and all(f in feature_names for f in ['cust_hitrate', 'cust_interactions', 'cust_contracts']):
            modified_row['customer_activity'] = (
                modified_row['cust_hitrate'] +
                modified_row['cust_interactions'] +
                modified_row['cust_contracts']
            ) / 3.0

        if 'customer_engagement' in feature_names:
            modified_row['customer_engagement'] = modified_row['cust_hitrate'] * modified_row['cust_interactions']

        # Get new prediction
        new_prob, new_pred = get_prediction(modified_row)
        delta_prob = new_prob - original_prob

        st.markdown("---")

        # Show results
        st.markdown('<div class="sub-header">📊 Simulation Results</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("New Probability", f"{new_prob:.1%}", delta=f"{delta_prob:+.1%}")
        col2.metric("New Prediction", "🏆 Win" if new_pred == 1 else "❌ Loss")
        col3.metric("Change", f"{delta_prob:+.1%}")

        # Visual indicator
        if delta_prob > 0.1:
            st.markdown(
                '<div class="success-box">✅ <strong>Significant Improvement!</strong> These changes increase win probability. Consider implementing these actions.</div>',
                unsafe_allow_html=True
            )
        elif delta_prob < -0.1:
            st.markdown(
                '<div class="warning-box">⚠️ <strong>Warning:</strong> These changes decrease win probability. Avoid this scenario.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="insight-box">ℹ️ <strong>Minor change</strong> in win probability.</div>',
                unsafe_allow_html=True
            )

        # Detailed change summary
        st.markdown("**📝 What Changed:**")

        changes = []
        scenario_summary = None
        if preset_action:
            if preset_action == "reset":
                scenario_summary = "Reset sliders to original values"
            elif preset_action in preset_meta_map:
                scenario_summary = preset_meta_map[preset_action]["short"]

        # Track what changed
        if 'cust_interactions' in feature_names:
            orig_val = float(original_row.get('cust_interactions', 0))
            new_val = float(modified_row.get('cust_interactions', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"**Customer Interactions:** {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'cust_hitrate' in feature_names:
            orig_val = float(original_row.get('cust_hitrate', 0))
            new_val = float(modified_row.get('cust_hitrate', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"**Customer Success Rate:** {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'opp_old' in feature_names:
            orig_val = float(original_row.get('opp_old', 0))
            new_val = float(modified_row.get('opp_old', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"**Opportunity Age:** {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'total_competitors' in feature_names:
            orig_val = int(original_row.get('total_competitors', 0))
            new_val = int(modified_row.get('total_competitors', 0))
            if orig_val != new_val:
                delta_val = new_val - orig_val
                changes.append(f"**Total Competitors:** {orig_val} → {new_val} ({delta_val:+d})")

        original_label = "🏆 Win" if original_pred == 1 else "❌ Loss"
        new_label = "🏆 Win" if new_pred == 1 else "❌ Loss"
        if original_pred != new_pred:
            changes.insert(0, f"**Prediction:** {original_label} → {new_label}")

        if scenario_summary:
            changes.insert(0, f"**Scenario:** {scenario_summary}")

        if changes:
            for change in changes:
                st.markdown(f"• {change}")

            # Impact summary
            pp_change = delta_prob * 100
            st.info(f"💡 **Net Impact:** These changes moved win probability by **{pp_change:+.1f} percentage points** (from {original_prob:.1%} to {new_prob:.1%})")
        else:
            st.markdown("• *No changes made*")

        st.markdown("---")

        # SHAP for modified
        st.markdown('<div class="sub-header">🌊 Updated SHAP Explanation</div>', unsafe_allow_html=True)
        try:
            new_shap = explainer.shap_values(modified_row.values.reshape(1, -1))
            if isinstance(new_shap, list):
                new_shap = new_shap[1][0]
            else:
                new_shap = new_shap[0]

            base_val = explainer.expected_value
            if isinstance(base_val, (list, np.ndarray)):
                base_val = float(base_val[1] if len(np.atleast_1d(base_val)) > 1 else base_val[0])

            plot_shap_waterfall(new_shap, modified_row, base_val)
            st.caption("Starting from the average prediction, red bars increase the probability and blue bars decrease it for this simulated scenario.")

            pos_drivers, neg_drivers = summarize_shap(new_shap, feature_names)
            if pos_drivers or neg_drivers:
                st.markdown("**Key drivers after your adjustments:**")
                if pos_drivers:
                    st.markdown("✅ *What helps now*")
                    for name, val in pos_drivers:
                        st.markdown(f"- {name}: {val:+.2f}")
                if neg_drivers:
                    st.markdown("❌ *What still hurts*")
                    for name, val in neg_drivers:
                        st.markdown(f"- {name}: {val:+.2f}")

            with st.expander("ℹ️ How to interpret this chart"):
                st.markdown("""
                - **Base value** is the historical average win probability.
                - **Red bars** push the probability up (toward Win); **blue bars** push it down (toward Loss).
                - The final grey dot equals the new probability shown above.
                - Larger absolute values indicate stronger influence for this scenario.
                """)
        except Exception as e:
            st.warning(f"Could not generate SHAP plot: {e}")

        # Action recommendation
        st.markdown('<div class="sub-header">🎯 Action Recommendation</div>', unsafe_allow_html=True)
        if delta_prob > 0.1:
            st.markdown("""
            <div class='success-box'>
            <strong>Recommended Actions:</strong>
            <ul>
            <li>✓ Increase customer touchpoints and engagement</li>
            <li>✓ Act quickly to maintain momentum</li>
            <li>✓ Leverage improved position to close the deal</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='warning-box'>
            <strong>Recommended Actions:</strong>
            <ul>
            <li>⚠ Re-evaluate opportunity viability</li>
            <li>⚠ Consider if resources are better allocated elsewhere</li>
            <li>⚠ If pursuing, address key blockers identified in SHAP</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
