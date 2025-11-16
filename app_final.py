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
import plotly.express as px
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

    • If probability >= threshold -> Prediction: Win
    • If probability < threshold -> Prediction: Loss

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
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --md-black: #101010;
        --md-dark: #383838;
        --md-cream: #f4efe9;
        --md-white: #ffffff;
        --md-blue: #6bc3fb;
        --md-yellow: #fbdc04;
        --md-teal: #14ab9b;
        --md-coral: #fb736b;
        --md-border: #0f0f10;
        --md-shadow-hard: -10px 10px 0 rgba(15,15,16,0.9);
        --md-shadow-soft: 0 18px 40px rgba(0,0,0,0.12);
        --font-sans: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
        --font-mono: 'Space Mono', 'IBM Plex Mono', monospace;
    }

    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 8px;
        z-index: 999;
        background: linear-gradient(90deg, var(--md-yellow), var(--md-teal), var(--md-blue), var(--md-coral));
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top, #fdf9f0 0%, var(--md-cream) 55%, #bce2ff 140%);
        color: var(--md-dark);
        font-family: var(--font-sans);
    }

    [data-testid="block-container"] {
        padding: 1.5rem 5vw 4rem 5vw;
        max-width: 1200px;
        margin: 0 auto;
    }

    a {
        color: var(--md-blue);
        font-weight: 600;
    }

    [data-testid="stSidebar"] {
        background: #050505;
        color: #f5f5f5;
        border-right: 4px solid var(--md-yellow);
        box-shadow: inset -8px 0 16px rgba(0,0,0,0.65);
    }

    [data-testid="stSidebar"] * {
        color: inherit !important;
    }

    /* Restore Material Icon font so glyphs render instead of text names */
    .material-icons,
    .material-icons-round,
    .material-icons-outlined,
    .material-icons-two-tone,
    .material-icons-sharp {
        font-family: "Material Icons", "Material Icons Round", "Material Icons Outlined", "Material Icons Two Tone", "Material Icons Sharp" !important;
        font-feature-settings: "liga";
        font-style: normal;
        font-weight: normal;
        font-size: 24px;
        line-height: 1;
    }

    .sidebar-design {
        padding: 1rem;
        border: 1px dashed rgba(251, 220, 4, 0.5);
        border-radius: 18px;
        margin-bottom: 1rem;
        background: rgba(255,255,255,0.05);
    }

    .sidebar-design .nav-title {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #f7f5e8;
        margin-bottom: 0.4rem;
        font-family: var(--font-mono);
    }

    .sidebar-design .nav-subtitle {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.72);
        line-height: 1.4;
        margin-top: 0.3rem;
    }

    .concept-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.2rem 0.75rem;
        border-radius: 999px;
        background: rgba(20, 171, 155, 0.18);
        color: var(--md-black);
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
        border: 1px solid rgba(20, 171, 155, 0.4);
        font-family: var(--font-mono);
    }

    .nav-pill-container {
        background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.02));
        padding: 0.6rem;
        border-radius: 1rem;
        border: 1px solid rgba(255,255,255,0.18);
        box-shadow: inset 0 0 20px rgba(20, 171, 155, 0.1);
        margin-bottom: 1.5rem;
    }

    .nav-chips {
        margin-top: 0.4rem;
    }

    .nav-pill-container [data-baseweb="radio"] {
        background: transparent !important;
    }

    .nav-pill-container [data-baseweb="radio"] > div {
        gap: 0.35rem !important;
    }

    .nav-pill-container .stRadio [role="radiogroup"] label {
        background: rgba(255,255,255,0.92);
        border-radius: 999px;
        padding: 0.45rem 0.9rem;
        margin-bottom: 0.35rem;
        border: 1px solid rgba(251, 220, 4, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        cursor: pointer;
    }

    .nav-pill-container .stRadio [role="radiogroup"] label:hover {
        transform: translateX(6px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }

    .nav-pill-container .stRadio [role="radiogroup"] label span {
        font-weight: 600 !important;
        color: var(--md-black) !important;
        font-family: var(--font-sans);
    }

    .stSelectbox label,
    .stSlider label,
    .stNumberInput label {
        color: var(--md-black) !important;
        font-family: var(--font-mono);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.85rem;
    }

    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        background: var(--md-white);
        border: 2px solid var(--md-border);
        border-radius: 18px;
        color: var(--md-black);
        min-height: 48px;
    }

    .stSelectbox div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] span {
        color: var(--md-black) !important;
        font-weight: 600;
    }

    .stSelectbox div[data-baseweb="popover"],
    .stMultiSelect div[data-baseweb="popover"] {
        background: var(--md-white);
        color: var(--md-black);
    }

    .stSlider [data-testid="stTickBarMin"],
    .stSlider [data-testid="stTickBarMax"],
    .stSlider [data-testid="stTickBarValue"] {
        color: var(--md-dark) !important;
    }

    .md-control-card {
        border: 2px solid var(--md-border);
        border-radius: 26px;
        background: var(--md-white);
        padding: 1.25rem;
        box-shadow: var(--md-shadow-soft);
        margin-bottom: 1.5rem;
    }

    .md-driver-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }

    .md-driver-card {
        border: 2px solid var(--md-border);
        border-radius: 22px;
        padding: 1rem 1.25rem;
        background: var(--md-white);
        box-shadow: var(--md-shadow-soft);
    }

    .md-driver-card.positive {
        border-left: 6px solid var(--md-teal);
    }

    .md-driver-card.negative {
        border-left: 6px solid var(--md-coral);
    }

    .md-driver-card h4 {
        margin: 0 0 0.6rem 0;
        font-family: var(--font-mono);
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .md-driver-card ul {
        list-style: none;
        padding-left: 0;
        margin: 0;
    }

    .md-driver-card li {
        margin: 0.35rem 0;
        font-weight: 600;
        color: var(--md-dark);
    }

    [data-testid="stMetric"] {
        background: var(--md-black);
        border: 3px solid var(--md-yellow);
        border-radius: 26px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: var(--md-shadow-hard);
        font-family: var(--font-mono);
        transition: transform 0.2s ease;
        color: #fdfdfd;
    }

    [data-testid="stMetric"]:hover {
        transform: translate(-4px, -4px);
    }

    [data-testid="stMetricLabel"] {
        color: var(--md-yellow) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.85rem;
    }

    [data-testid="stMetricValue"] {
        color: var(--md-blue) !important;
        font-size: 2rem;
        font-weight: 700;
    }

    [data-testid="stMetricDelta"] {
        font-weight: 600;
        color: var(--md-teal) !important;
    }

    .stButton>button {
        border-radius: 999px;
        background: var(--md-black);
        color: var(--md-yellow);
        border: 2px solid var(--md-yellow);
        padding: 0.65rem 1.8rem;
        font-weight: 700;
        text-transform: uppercase;
        box-shadow: var(--md-shadow-hard);
        transition: transform 0.2s ease, background 0.2s ease, color 0.2s ease;
        font-family: var(--font-mono);
    }

    .stButton>button:hover {
        background: var(--md-yellow);
        color: var(--md-black);
        transform: translate(-4px, -4px);
    }

    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        font-family: var(--font-mono);
        color: var(--md-black);
        background: var(--md-white);
        border: 2px solid var(--md-border);
        padding: 1.25rem 1.75rem;
        border-radius: 30px;
        box-shadow: var(--md-shadow-hard);
        margin-bottom: 1.5rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .sub-header {
        font-family: var(--font-mono);
        font-size: 1.4rem;
        color: var(--md-black);
        margin: 2rem 0 1rem;
        padding-left: 1rem;
        border-left: 8px solid var(--md-blue);
        text-transform: uppercase;
    }

    .insight-box,
    .warning-box,
    .success-box,
    .chart-description,
    .combined-insights-box {
        border-radius: 26px;
        padding: 1.75rem;
        margin: 1.5rem 0;
        border: 2px solid var(--md-border);
        background: var(--md-white);
        box-shadow: var(--md-shadow-hard);
        transition: transform 0.2s ease;
    }

    .insight-box:hover,
    .warning-box:hover,
    .success-box:hover,
    .chart-description:hover,
    .combined-insights-box:hover {
        transform: translate(-6px, -6px);
    }

    .insight-box {
        border-top: 10px solid var(--md-blue);
    }

    .warning-box {
        border-top: 10px solid var(--md-coral);
    }

    .success-box {
        border-top: 10px solid var(--md-teal);
    }

    .chart-description {
        border-top: 10px solid var(--md-yellow);
        background: #fffdf3;
    }

    .insight-box ul,
    .warning-box ul,
    .success-box ul {
        margin: 0.75rem 0;
        padding-left: 1.25rem;
        color: var(--md-dark);
    }

    .insight-box li,
    .warning-box li,
    .success-box li {
        margin-bottom: 0.6rem;
        line-height: 1.6;
        font-size: 1rem;
    }

    .combined-insights-box strong {
        display: inline-block;
        margin-bottom: 0.4rem;
        font-size: 1.05rem;
        font-family: var(--font-mono);
    }

    .brand-accent {
        color: var(--md-yellow);
        font-weight: 700;
    }

    .insights-section,
    .recommendations-section {
        text-align: justify;
        color: var(--md-black);
        line-height: 1.8;
    }

    .insights-section {
        margin-bottom: 1.5rem;
    }

    [data-testid="stDataFrame"] {
        background: var(--md-white);
        border-radius: 26px;
        border: 2px solid var(--md-border);
        box-shadow: var(--md-shadow-soft);
        padding: 0.5rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.75rem;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 18px;
        padding: 0.4rem 1.5rem;
        border: 2px solid var(--md-border);
        background: var(--md-white);
        color: var(--md-dark);
        font-weight: 600;
        font-family: var(--font-mono);
        transition: transform 0.2s ease, background 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        transform: translate(-3px, -3px);
        background: #fff8db;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--md-black);
        background: #dff1ff;
        border-color: var(--md-blue);
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
    median = stats.get("median", p25)

    # Special case: if p25 == p75, distribution is very concentrated
    if abs(p25 - p75) < 0.0001:  # Essentially the same value
        if abs(value - median) < 0.0001:
            label = "Typical"
            delta_color = "off"
        elif value > median:
            label = "Outlier (High)"
            delta_color = "normal" if "compet" not in feature_name.lower() else "inverse"
        else:
            label = "Outlier (Low)"
            delta_color = "off"
    else:
        # Normal case: use percentiles
        if value < p25:
            label = "Low"
            delta_color = "off"
        elif value > p75:
            label = "High"
            delta_color = "normal"
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
                delta_color = "inverse"

    return label, delta_color

def clamp_value(value, min_value, max_value):
    """Clamp numeric value to a specific range"""
    return max(min_value, min(max_value, value))

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
st.sidebar.markdown("## Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["Global Insights", "Case Explorer", "What-If Simulator"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Model Performance")
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
if page == "Global Insights":
    st.markdown('<div class="main-header">Global Model Insights</div>', unsafe_allow_html=True)
    st.markdown("**Comprehensive overview of model performance and key patterns across all opportunities**")

    # Combined insights and recommendations at the top
    st.markdown("---")

    insights_text = " ".join(global_insights["business_insights"])
    recommendations_text = " ".join(global_insights["recommendations"])

    combined_html = f"""
    <div class='combined-insights-box'>
        <div class='insights-section'>
            <strong style='color: #2196f3; font-size: 1.1rem;'>Key Insights:</strong> {insights_text}
        </div>
        <div class='recommendations-section'>
            <strong style='color: #4caf50; font-size: 1.1rem;'>Recommendations:</strong> {recommendations_text}
        </div>
    </div>
    """
    st.markdown(combined_html, unsafe_allow_html=True)

    st.markdown("---")

    # Performance metrics
    st.markdown('<div class="sub-header">Model Performance Metrics</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="sub-header">Prediction Distribution</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-description">
    <strong>What does this mean?</strong> Of all opportunities analyzed in the test set,
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

        st.markdown("""
        <div class="chart-description">
        <strong>🔴 Low (0-30%):</strong> Urgent intervention or re-evaluation needed<br>
        <strong>🟠 Medium (30-50%):</strong> Increase interactions, address objections<br>
        <strong>🟢 High (50-70%):</strong> Maintain momentum, accelerate close<br>
        <strong>🔵 Very High (70-100%):</strong> Prioritize to close quickly<br><br>
        <strong>Strategy:</strong> Move Medium → High deals by increasing customer touchpoints
        </div>
        """, unsafe_allow_html=True)

        # Use actual labels from JSON
        bucket_labels_json = ["Low", "Medium", "High", "Very High"]
        bucket_labels_display = ["🔴 Low (0-30%)", "🟠 Medium (30-50%)", "🟢 High (50-70%)", "🔵 Very High (70-100%)"]
        buckets_df = pd.DataFrame({
            "Confidence Level": bucket_labels_display,
            "Number of Opportunities": [dist["probability_buckets"].get(label, 0) for label in bucket_labels_json]
        })

        fig_buckets = px.bar(
            buckets_df,
            x="Confidence Level",
            y="Number of Opportunities",
            text="Number of Opportunities",
            color="Confidence Level",
            color_discrete_sequence=["#f94144", "#f3722c", "#90be6d", "#277da1"]
        )
        fig_buckets.update_traces(textposition="outside")
        fig_buckets.update_layout(
            xaxis_title="Nivel de Confianza",
            yaxis_title="Número de Oportunidades",
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_buckets, width="stretch")

    # Feature importance
    st.markdown('<div class="sub-header">Top Influential Features</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="chart-description">
    <strong>What does this mean?</strong> These are the variables that have the most weight
    in determining whether an opportunity is won or lost. <strong>Focus on improving features
    with the highest bars</strong> to increase your win probability.
    <br><br>
    <strong>Source:</strong> Feature importance scores from XGBoost model, calculated based on
    how frequently and effectively each feature is used for decision splits across all trees.
    </div>
    """, unsafe_allow_html=True)

    feat_imp = global_insights["feature_importance_top20"]
    feat_df = pd.DataFrame({
        "Feature": [translate_feature(f) for f in list(feat_imp.keys())[:15]],
        "Importance": list(feat_imp.values())[:15]
    })
    feat_df = feat_df.sort_values("Importance", ascending=True)

    fig_feat = px.bar(
        feat_df,
        x="Importance",
        y="Feature",
        orientation="h",
        text=feat_df["Importance"].map(lambda v: f"{v:.3f}"),
        color="Importance",
        color_continuous_scale="Blues"
    )
    fig_feat.update_traces(textposition="outside")
    fig_feat.update_layout(
        xaxis_title="Relative Importance (XGBoost gain)",
        yaxis_title="Feature",
        margin=dict(l=0, r=0, t=10, b=10),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_feat, width="stretch")

    # SHAP summary (static image)
    st.markdown('<div class="sub-header">Feature Impact on Win Probability</div>', unsafe_allow_html=True)
    if Path("output/images/shap_summary.png").exists():
        with st.expander("See SHAP summary plot"):
            st.markdown("""
                <div class="chart-description">
                Each dot represents an opportunity. Red = high feature value, Blue = low feature value. Right side increases win chance, left side decreases it. 
                </div>
                """, unsafe_allow_html=True)
            st.image("output/images/shap_summary.png", width="stretch")
            #st.caption("Each dot represents an opportunity. Red = high feature value, Blue = low feature value. Right side increases win chance, left side decreases it.")
    else:
        st.info("SHAP summary image not found. Please regenerate it from the Colab notebook.")

    # SHAP drivers textual summary
    if "shap_drivers" in global_insights:
        st.markdown("**Key Drivers:**")

        # Build HTML for positive drivers
        positive_drivers_html = ""
        for driver in global_insights["shap_drivers"]["top_positive"]:
            feat_name = translate_feature(driver["feature"])
            shap_val = driver["mean_shap"]
            positive_drivers_html += f"• <strong>{feat_name}</strong> (+{shap_val:.3f})<br>"

        # Build HTML for negative drivers
        negative_drivers_html = ""
        for driver in global_insights["shap_drivers"]["top_negative"]:
            feat_name = translate_feature(driver["feature"])
            shap_val = driver["mean_shap"]
            negative_drivers_html += f"• <strong>{feat_name}</strong> ({shap_val:.3f})<br>"

        st.markdown(f"""
        <div class="insight-box">
        <table width="100%">
        <tr>
        <td width="50%" valign="top">
        <strong>Increase Win Chance:</strong><br><br>
        {positive_drivers_html}
        </td>
        <td width="50%" valign="top">
        <strong>Decrease Win Chance:</strong><br><br>
        {negative_drivers_html}
        </td>
        </tr>
        </table>
        <br>
        <em>Average SHAP values across all opportunities. Positive values push predictions toward win, negative values toward loss.</em>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# PAGE 2: CASE EXPLORER
# ============================================================
elif page == "Case Explorer":
    st.markdown('<div class="main-header">Individual Opportunity Analysis</div>', unsafe_allow_html=True)
    st.markdown("**Explore detailed predictions and explanations for specific opportunities**")

    # Case ID input
    available_ids = sorted(X_test.index.tolist())

    case_id = st.selectbox(
        "Select Opportunity ID",
        available_ids,
        index=available_ids.index(102) if 102 in available_ids else 0,
        help=f"Choose from {len(available_ids):,} opportunities in the test set"
    )

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
        st.markdown('<div class="sub-header">Prediction Results</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Opportunity ID", str(case_id))
        col2.metric(
            "Win Probability",
            f"{prob:.1%}",
            help="Model's estimated probability that this opportunity will be won"
        )
        col3.metric(
            "Prediction",
            "Win" if pred == 1 else "Loss",
            help=f"Classification based on threshold of {threshold:.3f}"
        )
        col4.metric(
            "Actual Outcome",
            "Win" if actual == 1 else "Loss",
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
            confidence_class = "success-box"
            explanation = f"Probability ({prob:.1%}) exceeds threshold ({threshold:.1%}) by {threshold_distance:.1f} percentage points."
            if top_positive:
                top_factor = translate_feature(top_positive[0]["feature"])
                explanation += f" Strong positive signals from {top_factor}."
        elif threshold_distance > 10:  # 10-40pp above threshold
            confidence_level = "Medium-High"
            confidence_class = "success-box"
            explanation = f"Probability ({prob:.1%}) is {threshold_distance:.1f}pp above threshold ({threshold:.1%})."
            if top_negative:
                top_concern = translate_feature(top_negative[0]["feature"])
                explanation += f" Watch for potential issues with {top_concern}."
        elif threshold_distance > 0:  # 0-10pp above threshold
            confidence_level = "Medium"
            confidence_class = "warning-box"
            explanation = f"Probability ({prob:.1%}) barely exceeds threshold ({threshold:.1%}) by only {threshold_distance:.1f}pp."
            if top_negative:
                top_concern = translate_feature(top_negative[0]["feature"])
                explanation += f" Negative signals from {top_concern} are holding it back."
        else:  # Below threshold
            confidence_level = "Low"
            confidence_class = "warning-box"
            explanation = f"Probability ({prob:.1%}) is {abs(threshold_distance):.1f}pp below threshold ({threshold:.1%})."
            if top_negative:
                main_blocker = translate_feature(top_negative[0]["feature"])
                explanation += f" Main blocker: {main_blocker}."

        st.markdown(
            f'<div class="{confidence_class}"><strong>{confidence_level} Confidence:</strong> {explanation}</div>',
            unsafe_allow_html=True
        )

        # Key features
        #st.markdown('<div class="sub-header">Key Features for This Opportunity</div>', unsafe_allow_html=True)
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

            # Opportunity Quality Score
            opp_quality_val = key_feats['opp_quality_score']
            opp_quality_label, _ = get_feature_context("opp_quality_score", opp_quality_val, feature_stats)
            col3.metric(
                translate_feature("opp_quality_score"),
                f"{opp_quality_val:.3f}",
                delta=opp_quality_label if opp_quality_label else None,
                help="Composite quality score based on customer activity, hit rate, and Product A affinity. Higher is better."
            )

        # Top SHAP Factors
        if case_json and "shap_analysis" in case_json:
            st.markdown('<div class="sub-header">Key Drivers for This Opportunity</div>', unsafe_allow_html=True)

            # Build HTML for positive factors
            positive_html = ""
            for factor in case_json["shap_analysis"]["top_positive_factors"][:3]:
                feat_name = translate_feature(factor["feature"])
                shap_val = factor["shap_value"]
                positive_html += f"• <strong>{feat_name}</strong> (+{shap_val:.3f})<br>"

            # Build HTML for negative factors
            negative_html = ""
            if case_json["shap_analysis"]["top_negative_factors"]:
                for factor in case_json["shap_analysis"]["top_negative_factors"][:3]:
                    feat_name = translate_feature(factor["feature"])
                    shap_val = factor["shap_value"]
                    negative_html += f"• <strong>{feat_name}</strong> ({shap_val:.3f})<br>"
            else:
                negative_html = "• <em>No significant negative factors</em><br>"

            st.markdown(f"""
            <div class="insight-box">
            <table width="100%">
            <tr>
            <td width="50%" valign="top">
            <strong>What Pushes Toward Win:</strong><br><br>
            {positive_html}
            </td>
            <td width="50%" valign="top">
            <strong>What Holds It Back:</strong><br><br>
            {negative_html}
            </td>
            </tr>
            </table>
            <br>
            <em>SHAP values show how each feature affects this specific prediction. Larger absolute values = stronger influence.</em>
            </div>
            """, unsafe_allow_html=True)

        # SHAP Waterfall
        st.markdown('<div class="sub-header">Why This Prediction?</div>', unsafe_allow_html=True)

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
                st.info("**Summary:** " + " | ".join(summary_parts))

        # SHAP glossary (expandable)
        with st.expander("Understanding SHAP Waterfall Charts"):
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

            # Build next steps HTML
            next_steps_html = ""
            for i, step in enumerate(rec['next_steps'], 1):
                next_steps_html += f"{i}. {step}<br>"

            st.markdown(f"""
            <div class='success-box'>
            <strong>Recommended Action:</strong> {rec['action']}<br>
            <strong>Priority Level:</strong> {rec['priority']}<br><br>
            <strong>Next Steps:</strong><br>
            {next_steps_html}
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# PAGE 3: WHAT-IF SIMULATOR
# ============================================================
elif page == "What-If Simulator":
    st.markdown('<div class="main-header">What-If Scenario Simulator</div>', unsafe_allow_html=True)
    st.markdown("**Simulate changes to key variables and observe real-time impact on win probability**")

    # Select base case
    available_ids = X_test.index.tolist()
    available_ids.sort()
    base_id = st.selectbox("Select Base Opportunity", available_ids, index=0)

    if base_id is not None:
        row_pos = X_test.index.get_loc(base_id)
        original_row = X_test.loc[base_id].copy()

        # Initialize slider states when opportunity changes (only if not already set)
        if st.session_state.get("last_base_id") != base_id:
            st.session_state["last_base_id"] = base_id
            if 'cust_interactions' in feature_names:
                st.session_state["slider_interactions"] = clamp_value(float(original_row.get('cust_interactions', 0.5)), 0.0, 2.0)
            if 'cust_hitrate' in feature_names:
                st.session_state["slider_hitrate"] = clamp_value(float(original_row.get('cust_hitrate', 0.5)), 0.0, 1.0)
            if 'opp_old' in feature_names:
                st.session_state["slider_opp_old"] = clamp_value(float(original_row.get('opp_old', 0.0)), -2.0, 2.0)
            if 'total_competitors' in feature_names:
                st.session_state["slider_competitors"] = clamp_value(float(original_row.get('total_competitors', 0)), 0.0, 5.0)

        # Get original prediction
        original_prob, original_pred = get_prediction(original_row)

        # Display original
        st.markdown('<div class="sub-header">Original State</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Original Probability", f"{original_prob:.1%}")
        col2.metric("Prediction", "Win" if original_pred == 1 else "Loss")
        col3.metric(
            "Confidence",
            "High" if abs(original_prob - 0.5) > 0.3 else "Medium"
        )

        st.markdown("---")

        # Preset actions
        st.markdown('<div class="sub-header">Quick Scenarios</div>', unsafe_allow_html=True)
        st.markdown("Apply common business scenarios to auto-adjust sliders and instantly see the impact.")

        preset_options = [
            ("interactions_up", {
                "label": "+20% Interactions",
                "short": "+20% Interactions",
                "description": "Boost customer interactions by 20% (capped at 2.0) to simulate extra touchpoints."
            }),
            ("reduce_comp", {
                "label": "Reduce Competitors",
                "short": "-1 Competitor",
                "description": "Remove one competitor to test the impact of a less crowded deal."
            }),
            ("fast_track", {
                "label": "Fast-Track (New)",
                "short": "Fast-track Opportunity",
                "description": "Set opportunity age to very new (-1.0) to mimic speeding up the cycle."
            }),
            ("reset", {
                "label": "Reset to Original",
                "short": "Reset sliders",
                "description": "Return all sliders to their original values."
            })
        ]

        preset_meta_map = {key: meta for key, meta in preset_options}

        preset_action = None
        preset_cols = st.columns(len(preset_options))
        for (option, meta), col in zip(preset_options, preset_cols):
            with col:
                if st.button(meta["label"], use_container_width=True):  # Buttons don't support width parameter yet
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
        st.markdown('<div class="sub-header">Adjust Variables</div>', unsafe_allow_html=True)

        modified_row = original_row.copy()

        # Apply preset if selected
        if preset_action == "interactions_up" and 'cust_interactions' in feature_names:
            base_val = st.session_state.get("slider_interactions", float(original_row.get('cust_interactions', 0.5)))
            new_val = clamp_value(base_val * 1.2, 0.0, 2.0)
            st.session_state["slider_interactions"] = new_val
            modified_row['cust_interactions'] = new_val
        elif preset_action == "reduce_comp" and 'total_competitors' in feature_names:
            base_val = st.session_state.get("slider_competitors", float(original_row.get('total_competitors', 0)))
            new_val = clamp_value(int(base_val) - 1, 0, 5)
            st.session_state["slider_competitors"] = float(new_val)
            modified_row['total_competitors'] = float(new_val)
        elif preset_action == "fast_track" and 'opp_old' in feature_names:
            new_val = clamp_value(-1.0, -2.0, 2.0)
            st.session_state["slider_opp_old"] = new_val
            modified_row['opp_old'] = new_val  # Make it new
        elif preset_action == "reset":
            if 'cust_interactions' in feature_names:
                base_val = clamp_value(float(original_row.get('cust_interactions', 0.5)), 0.0, 2.0)
                st.session_state["slider_interactions"] = base_val
                modified_row['cust_interactions'] = base_val
            if 'cust_hitrate' in feature_names:
                base_val = clamp_value(float(original_row.get('cust_hitrate', 0.5)), 0.0, 1.0)
                st.session_state["slider_hitrate"] = base_val
                modified_row['cust_hitrate'] = base_val
            if 'opp_old' in feature_names:
                base_val = clamp_value(float(original_row.get('opp_old', 0.0)), -2.0, 2.0)
                st.session_state["slider_opp_old"] = base_val
                modified_row['opp_old'] = base_val
            if 'total_competitors' in feature_names:
                base_val = clamp_value(float(original_row.get('total_competitors', 0)), 0.0, 5.0)
                st.session_state["slider_competitors"] = base_val
                modified_row['total_competitors'] = base_val

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Customer Engagement**")
            if 'cust_interactions' in feature_names:
                feature_stats = global_insights.get("feature_statistics", {})
                stats = feature_stats.get('cust_interactions', {})
                help_text = "Number of interactions with the customer (normalized)"
                if stats:
                    help_text += f"\n• Average: {stats.get('median', 0):.2f}\n• P25: {stats.get('p25', 0):.2f}, P75: {stats.get('p75', 0):.2f}"

                new_interactions = st.slider(
                    translate_feature("cust_interactions"),
                    min_value=0.0,
                    max_value=2.0,
                    step=0.1,
                    help=help_text,
                    key="slider_interactions"
                )
                modified_row['cust_interactions'] = new_interactions

            if 'cust_hitrate' in feature_names:
                feature_stats = global_insights.get("feature_statistics", {})
                stats = feature_stats.get('cust_hitrate', {})
                help_text = "Historical success rate with this customer (0-1)"
                if stats:
                    help_text += f"\n• Average: {stats.get('median', 0):.2f}\n• P25: {stats.get('p25', 0):.2f}, P75: {stats.get('p75', 0):.2f}"

                new_hitrate = st.slider(
                    translate_feature("cust_hitrate"),
                    min_value=0.0,
                    max_value=1.0,
                    step=0.05,
                    help=help_text,
                    key="slider_hitrate"
                )
                modified_row['cust_hitrate'] = new_hitrate

        with col2:
            st.markdown("**Opportunity Characteristics**")
            if 'opp_old' in feature_names:
                new_opp_age = st.slider(
                    translate_feature("opp_old"),
                    min_value=-2.0,
                    max_value=2.0,
                    step=0.1,
                    help="Opportunity age (standardized)\n• -2 = Very new\n• 0 = Average age\n• +2 = Very old",
                    key="slider_opp_old"
                )
                modified_row['opp_old'] = new_opp_age

            if 'total_competitors' in feature_names:
                new_competitors = st.slider(
                    translate_feature("total_competitors"),
                    min_value=0,
                    max_value=5,
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
        st.markdown('<div class="sub-header">Simulation Results</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("New Probability", f"{new_prob:.1%}", delta=f"{delta_prob:+.1%}")
        col2.metric("New Prediction", "Win" if new_pred == 1 else "Loss")
        col3.metric("Change", f"{delta_prob:+.1%}")

        # Build change summary first
        changes = []
        scenario_summary = None
        if preset_action:
            if preset_action == "reset":
                scenario_summary = "Reset to original"
            elif preset_action in preset_meta_map:
                scenario_summary = preset_meta_map[preset_action]["short"]

        # Track what changed
        if 'cust_interactions' in feature_names:
            orig_val = float(original_row.get('cust_interactions', 0))
            new_val = float(modified_row.get('cust_interactions', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"Customer Interactions: {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'cust_hitrate' in feature_names:
            orig_val = float(original_row.get('cust_hitrate', 0))
            new_val = float(modified_row.get('cust_hitrate', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"Customer Success Rate: {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'opp_old' in feature_names:
            orig_val = float(original_row.get('opp_old', 0))
            new_val = float(modified_row.get('opp_old', 0))
            if abs(new_val - orig_val) > 0.01:
                delta_val = new_val - orig_val
                changes.append(f"Opportunity Age: {orig_val:.2f} → {new_val:.2f} ({delta_val:+.2f})")

        if 'total_competitors' in feature_names:
            orig_val = int(original_row.get('total_competitors', 0))
            new_val = int(modified_row.get('total_competitors', 0))
            if orig_val != new_val:
                delta_val = new_val - orig_val
                changes.append(f"Total Competitors: {orig_val} → {new_val} ({delta_val:+d})")

        original_label = "Win" if original_pred == 1 else "Loss"
        new_label = "Win" if new_pred == 1 else "Loss"
        if original_pred != new_pred:
            changes.insert(0, f"Prediction: {original_label} → {new_label}")

        if scenario_summary:
            changes.insert(0, f"Scenario: {scenario_summary}")

        # Build change summary text
        change_summary = ""
        if changes:
            change_summary = "<br>".join([f"• {change}" for change in changes])

        pp_change = delta_prob * 100

        # Visual indicator with embedded changes
        if delta_prob > 0.1:
            st.markdown(
                f'<div class="success-box"><strong>Significant Improvement!</strong> These changes increase win probability. Consider implementing these actions.<br><br><strong>What Changed:</strong><br>{change_summary}<br><br><strong>Net Impact:</strong> These changes moved win probability by <strong>{pp_change:+.1f} percentage points</strong> (from {original_prob:.1%} to {new_prob:.1%})</div>',
                unsafe_allow_html=True
            )
        elif delta_prob < -0.1:
            st.markdown(
                f'<div class="warning-box"><strong>Warning:</strong> These changes decrease win probability. Avoid this scenario.<br><br><strong>What Changed:</strong><br>{change_summary}<br><br><strong>Net Impact:</strong> Win probability decreased by <strong>{pp_change:.1f} percentage points</strong> (from {original_prob:.1%} to {new_prob:.1%})</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="insight-box"><strong>Minor change</strong> in win probability.</div>',
                unsafe_allow_html=True
            )
            if changes:
                st.markdown("**What Changed:**")
                for change in changes:
                    st.markdown(f"- {change}")

        st.markdown("---")

        # SHAP for modified
        st.markdown('<div class="sub-header">Updated SHAP Explanation</div>', unsafe_allow_html=True)
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
                driver_html = "<div class='md-driver-grid'>"
                if pos_drivers:
                    driver_html += "<div class='md-driver-card positive'><h4>What helps now</h4><ul>"
                    for name, val in pos_drivers:
                        driver_html += f"<li>{name}: {val:+.2f}</li>"
                    driver_html += "</ul></div>"
                if neg_drivers:
                    driver_html += "<div class='md-driver-card negative'><h4>What still hurts</h4><ul>"
                    for name, val in neg_drivers:
                        driver_html += f"<li>{name}: {val:+.2f}</li>"
                    driver_html += "</ul></div>"
                driver_html += "</div>"
                st.markdown(driver_html, unsafe_allow_html=True)

            with st.expander("How to interpret this chart"):
                st.markdown("""
                - **Base value** is the historical average win probability.
                - **Red bars** push the probability up (toward Win); **blue bars** push it down (toward Loss).
                - The final grey dot equals the new probability shown above.
                - Larger absolute values indicate stronger influence for this scenario.
                """)
        except Exception as e:
            st.warning(f"Could not generate SHAP plot: {e}")

        # Action recommendation
        st.markdown('<div class="sub-header">Action Recommendation</div>', unsafe_allow_html=True)
        if delta_prob > 0.1:
            st.markdown("""
            <div class='success-box'>
            <strong>Recommended Actions:</strong>
            <ul>
            <li>Increase customer touchpoints and engagement</li>
            <li>Act quickly to maintain momentum</li>
            <li>Leverage improved position to close the deal</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='warning-box'>
            <strong>Recommended Actions:</strong>
            <ul>
            <li>Re-evaluate opportunity viability</li>
            <li>Consider if resources are better allocated elsewhere</li>
            <li>If pursuing, address key blockers identified in SHAP</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
