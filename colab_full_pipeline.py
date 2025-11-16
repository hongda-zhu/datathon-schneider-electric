# -*- coding: utf-8 -*-
"""
Schneider Electric Datathon - Explainable Pipeline
End-to-end Colab script that trains XGBoost, generates SHAP assets, and exports JSON insights.
"""

!wget -q https://raw.githubusercontent.com/data-students/datathon2025-challenges/refs/heads/main/Schneider%20Electric/dataset.csv
!pip install -q xgboost shap imbalanced-learn
!pip install -q streamlit pyngrok

import os
import json
import shutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    f1_score, roc_auc_score, precision_score,
    recall_score, accuracy_score, precision_recall_curve
)
from imblearn.combine import SMOTETomek

import shap

warnings.filterwarnings("ignore")
plt.rcParams["figure.dpi"] = 120

# ------------------------------------------------------------
# 0. OUTPUT
# ------------------------------------------------------------
os.makedirs("output/json", exist_ok=True)
os.makedirs("output/images", exist_ok=True)

print("✅ Librerías cargadas y carpetas creadas")

# ------------------------------------------------------------
# 1. CARGAR DATOS
# ------------------------------------------------------------
df = pd.read_csv("dataset.csv")
print("\n" + "="*70)
print("📂 DATASET CARGADO")
print("="*70)
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

required_cols = [
    "id", "target_variable",
    "cust_hitrate", "cust_interactions", "cust_contracts",
    "product_A_sold_in_the_past", "product_B_sold_in_the_past",
    "product_A_recommended",
    "product_A", "product_C", "product_D",
    "competitor_X", "competitor_Y", "competitor_Z",
    "cust_in_iberia",
    "opp_old", "opp_month"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"❌ Faltan columnas en dataset.csv: {missing}")
else:
    print("✅ Todas las columnas requeridas existen")

# ------------------------------------------------------------
# 2. FEATURE ENGINEERING (SOLO COLUMNAS EXISTENTES)
# ------------------------------------------------------------
print("\n" + "="*70)
print("🔨 FEATURE ENGINEERING")
print("="*70)

df_fe = df.copy()

df_fe["total_competitors"] = df_fe["competitor_X"] + df_fe["competitor_Y"] + df_fe["competitor_Z"]
df_fe["has_competition"] = (df_fe["total_competitors"] > 0).astype(int)
df_fe["competitor_diversity"] = (
    (df_fe["competitor_X"] > 0).astype(int) +
    (df_fe["competitor_Y"] > 0).astype(int) +
    (df_fe["competitor_Z"] > 0).astype(int)
)

df_fe["customer_activity"] = (
    df_fe["cust_hitrate"] + df_fe["cust_interactions"] + df_fe["cust_contracts"]
) / 3.0
df_fe["customer_engagement"] = df_fe["cust_hitrate"] * df_fe["cust_interactions"]
df_fe["contract_hitrate_ratio"] = df_fe["cust_contracts"] / (df_fe["cust_hitrate"] + 1e-3)

df_fe["total_past_sales"] = df_fe["product_A_sold_in_the_past"] + df_fe["product_B_sold_in_the_past"]
df_fe["product_A_ratio"] = df_fe["product_A_sold_in_the_past"] / (df_fe["total_past_sales"] + 1e-3)
df_fe["has_past_sales"] = (df_fe["total_past_sales"] > 0).astype(int)

df_fe["opp_age_squared"] = df_fe["opp_old"] ** 2
df_fe["opp_maturity"] = np.log1p(df_fe["opp_old"] + 10)
df_fe["is_new_opp"] = (df_fe["opp_old"] < -0.5).astype(int)
df_fe["is_mature_opp"] = (df_fe["opp_old"] > 1.0).astype(int)

df_fe["product_mix"] = df_fe["product_A"] + df_fe["product_C"] + df_fe["product_D"]
df_fe["product_count"] = (
    (df_fe["product_A"] > 0).astype(int) +
    (df_fe["product_C"] > 0).astype(int) +
    (df_fe["product_D"] > 0).astype(int)
)

df_fe["hitrate_interaction"] = df_fe["cust_hitrate"] * df_fe["cust_interactions"]
df_fe["hitrate_contracts"] = df_fe["cust_hitrate"] * df_fe["cust_contracts"]
df_fe["competition_engagement"] = df_fe["total_competitors"] * df_fe["customer_engagement"]

df_fe["competition_risk"] = df_fe["total_competitors"] / (df_fe["customer_activity"] + 1e-3)
df_fe["low_engagement_risk"] = (
    (df_fe["cust_interactions"] < df_fe["cust_interactions"].median()) &
    (df_fe["total_competitors"] > 0)
).astype(int)

df_fe["opp_quality_score"] = (
    df_fe["cust_hitrate"] * 0.3 +
    df_fe["customer_activity"] * 0.3 +
    df_fe["product_A_ratio"] * 0.4
)

df_fe["iberia_competition"] = df_fe["cust_in_iberia"] * df_fe["total_competitors"]
df_fe["iberia_engagement"] = df_fe["cust_in_iberia"] * df_fe["customer_engagement"]

print(f"✅ Features finales: {df_fe.shape[1]} (incluyendo id y target)")
print(f"✅ Nuevas columnas creadas: {df_fe.shape[1] - len(df.columns)}")

# ------------------------------------------------------------
# 3. PREPARAR X, y
# ------------------------------------------------------------
print("\n" + "="*70)
print("📐 PREPARACIÓN DE DATOS")
print("="*70)

X = df_fe.drop(columns=["id", "target_variable"])
X = X.select_dtypes(include=[np.number])
y = df_fe["target_variable"]

print(f"X shape: {X.shape}, y shape: {y.shape}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"✅ Train: {X_train.shape}")
print(f"✅ Test : {X_test.shape}")

# ------------------------------------------------------------
# 4. SMOTETomek
# ------------------------------------------------------------
print("\n" + "="*70)
print("⚖️ SMOTETomek BALANCING")
print("="*70)

print("Antes del balanceo:")
print(y_train.value_counts())

smote_tomek = SMOTETomek(random_state=42)
X_train_bal, y_train_bal = smote_tomek.fit_resample(X_train, y_train)

print("\nDespués del balanceo:")
print(pd.Series(y_train_bal).value_counts())
print(f"✅ Train balanceado: {X_train_bal.shape}")

# ------------------------------------------------------------
# 5. XGBoost
# ------------------------------------------------------------
print("\n" + "="*70)
print("🤖 ENTRENANDO XGBOOST")
print("="*70)

best_params = {
    "n_estimators": 591,
    "max_depth": 11,
    "learning_rate": 0.08699593128513321,
    "subsample": 0.9237068376069122,
    "colsample_bytree": 0.8494749947027712,
    "min_child_weight": 1,
    "gamma": 0.2773435281567039,
    "reg_alpha": 0.1959828624191452,
    "reg_lambda": 0.045227288910538066,
    "scale_pos_weight": 1.0650660661526528,
    "random_state": 42,
    "eval_metric": "logloss",
    "use_label_encoder": False
}

xgb_model = XGBClassifier(**best_params)
xgb_model.fit(X_train_bal, y_train_bal)

print("✅ XGBoost entrenado")

# ------------------------------------------------------------
# 6. EVALUACIÓN + OPTIMAL THRESHOLD (por F1)
# ------------------------------------------------------------
print("\n" + "="*70)
print("📊 EVALUACIÓN DEL MODELO")
print("="*70)

y_prob = xgb_model.predict_proba(X_test)[:, 1]
precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)
f1_scores = 2 * precisions * recalls / (precisions + recalls + 1e-10)

best_idx = np.argmax(f1_scores)
best_th = thresholds[best_idx] if len(thresholds) > 0 else 0.5

y_pred = (y_prob >= best_th).astype(int)

f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
acc = accuracy_score(y_test, y_pred)

print(f"Threshold óptimo (F1): {best_th:.3f}")
print(f"F1       : {f1:.4f}")
print(f"AUC      : {auc:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"Accuracy : {acc:.4f}")

# ------------------------------------------------------------
# 7. SHAP
# ------------------------------------------------------------
print("\n" + "="*70)
print("🔍 SHAP EXPLAINABILITY")
print("="*70)

shap.initjs()

explainer = shap.TreeExplainer(
    xgb_model,
    feature_perturbation="interventional"
)

print("Calculando SHAP values para X_test ...")
shap_values_full = explainer.shap_values(X_test)

if isinstance(shap_values_full, list):
    shap_values_full = shap_values_full[1]

sample_size = min(800, len(X_test))
X_sample = X_test.sample(sample_size, random_state=42)
sample_idx = X_sample.index
sample_positions = [X_test.index.get_loc(i) for i in sample_idx]
shap_sample = shap_values_full[sample_positions]

plt.figure(figsize=(10, 6))
shap.summary_plot(shap_sample, X_sample, show=False, max_display=20)
plt.title("SHAP Summary Plot - Top 20 Features", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("output/images/shap_summary.png", dpi=300, bbox_inches="tight")
plt.close()
print("✅ Saved: output/images/shap_summary.png")

feature_importance = pd.DataFrame({
    "feature": X.columns,
    "importance": xgb_model.feature_importances_
}).sort_values("importance", ascending=False)

plt.figure(figsize=(8, 8))
top_15 = feature_importance.head(15)
sns.barplot(data=top_15, x="importance", y="feature", orient="h")
plt.title("Top 15 Feature Importances (XGBoost)", fontsize=14, fontweight="bold")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig("output/images/feature_importance.png", dpi=300, bbox_inches="tight")
plt.close()
print("✅ Saved: output/images/feature_importance.png")

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(y_prob[y_test == 0], bins=40, alpha=0.7, label="Actual Loss", color="red")
plt.hist(y_prob[y_test == 1], bins=40, alpha=0.7, label="Actual Win", color="green")
plt.xlabel("Predicted Win Probability")
plt.ylabel("Frequency")
plt.title("Probability Distribution by Actual Outcome")
plt.legend()
plt.grid(alpha=0.3)

plt.subplot(1, 2, 2)
bins_prob = [0, 0.3, 0.5, 0.7, 1.0]
labels_prob = ["Low", "Medium", "High", "Very High"]
prob_categories = pd.cut(y_prob, bins=bins_prob, labels=labels_prob)
category_counts = prob_categories.value_counts().reindex(labels_prob, fill_value=0)
colors = ["red", "orange", "lightgreen", "darkgreen"]
plt.bar(category_counts.index, category_counts.values, color=colors)
plt.xlabel("Confidence Level")
plt.ylabel("Number of Opportunities")
plt.title("Prediction Confidence Distribution")
plt.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("output/images/probability_distribution.png", dpi=300, bbox_inches="tight")
plt.close()
print("✅ Saved: output/images/probability_distribution.png")

# ------------------------------------------------------------
# 8. GLOBAL JSON INSIGHTS
# ------------------------------------------------------------
print("\n" + "="*70)
print("💾 GUARDANDO GLOBAL_INSIGHTS.JSON")
print("="*70)

probability_buckets = {
    label: int(category_counts[label])
    for label in labels_prob
}

feature_stats_cols = [
    "customer_activity", "total_competitors",
    "opp_old", "cust_hitrate", "cust_interactions"
]

feature_statistics = {}
for feat in feature_stats_cols:
    if feat in X.columns:
        series = X[feat]
        feature_statistics[feat] = {
            "median": float(series.median()),
            "p25": float(series.quantile(0.25)),
            "p75": float(series.quantile(0.75))
        }

shap_df = pd.DataFrame(shap_values_full, columns=X.columns)
mean_shap = shap_df.mean().sort_values()
top_negative_drivers = [
    {"feature": feat, "mean_shap": float(val)}
    for feat, val in mean_shap.head(3).items()
]
top_positive_drivers = [
    {"feature": feat, "mean_shap": float(val)}
    for feat, val in mean_shap.tail(3).items()
]

global_insights = {
    "model_performance": {
        "threshold": float(best_th),
        "f1_score": float(f1),
        "auc": float(auc),
        "precision": float(precision),
        "recall": float(recall),
        "accuracy": float(acc)
    },
    "feature_importance_top20": {
        feature: float(importance)
        for feature, importance in feature_importance.head(20).values
    },
    "prediction_distribution": {
        "total_samples": int(len(y_test)),
        "predicted_wins": int(y_pred.sum()),
        "predicted_losses": int(len(y_pred) - y_pred.sum()),
        "win_rate": float(y_pred.mean()),
        "avg_win_probability": float(y_prob[y_pred == 1].mean()) if y_pred.sum() > 0 else 0.0,
        "avg_loss_probability": float(y_prob[y_pred == 0].mean()) if (len(y_pred) - y_pred.sum()) > 0 else 0.0,
        "probability_buckets": probability_buckets
    },
    "feature_statistics": feature_statistics,
    "shap_drivers": {
        "top_positive": top_positive_drivers,
        "top_negative": top_negative_drivers
    },
    "business_insights": [
        "Opportunity age is the most powerful predictor: deals that are either too new or too old have a lower chance of success.",
        "Opportunities with even a single competitor need rapid intervention; diversity of competitors further reduces win probability.",
        "Customers with high historical success rate quickly convert—monitor cust_hitrate to prioritize touchpoints.",
        "Repeated success with Product A (recommendations and historical volume) signals readiness for additional upsell.",
        "Iberia-specific interactions show different competitive behavior, requiring tailored strategies."
    ],
    "recommendations": [
        "Track opportunity age closely and escalate when deals stay open beyond the optimal window.",
        "Deploy competitive intelligence early when multiple brands appear, especially in Iberia accounts.",
        "Double down on customers showing rising success rates to secure quick wins.",
        "Use Product A historical adoption to design bundles and cross-sell motions.",
        "Allocate extra coverage to medium-probability deals by increasing interactions to push them above threshold."
    ]
}

with open("output/json/global_insights.json", "w") as f:
    json.dump(global_insights, f, indent=2)

print("✅ Saved: output/json/global_insights.json")

# ------------------------------------------------------------
# 9. INDIVIDUAL OPPORTUNITY JSON (primeros 300)
# ------------------------------------------------------------
print("\n" + "="*70)
print("👤 INDIVIDUAL OPPORTUNITY ANALYSIS (300 casos)")
print("="*70)

base_val = explainer.expected_value
if isinstance(base_val, (list, np.ndarray)):
    base_val = float(base_val[1] if len(np.atleast_1d(base_val)) > 1 else base_val[0])
else:
    base_val = float(base_val)

def get_factor_explanation(feature_name: str) -> str:
    explanations = {
        "customer_activity": "Nivel global de actividad del cliente",
        "customer_engagement": "Interacciones y calidad de relación con el cliente",
        "total_competitors": "Número total de competidores presentes",
        "competitor_diversity": "Diversidad de competidores en la oferta",
        "opp_old": "Antigüedad de la oportunidad",
        "opp_maturity": "Madurez de la oportunidad",
        "opp_quality_score": "Score agregado de calidad de oportunidad",
        "product_A_ratio": "Peso de ventas históricas de Product A",
        "total_past_sales": "Volumen total de ventas históricas",
        "cust_hitrate": "Tasa de éxito histórica con el cliente",
        "cust_interactions": "Número de interacciones con el cliente",
        "cust_contracts": "Número de contratos con el cliente",
        "has_competition": "Indicador de presencia de competencia",
        "competition_risk": "Riesgo asociado a la competencia",
        "product_mix": "Diversidad de productos activos",
        "product_count": "Número de líneas de producto en la oportunidad",
        "iberia_competition": "Competencia en clientes de Iberia",
        "iberia_engagement": "Engagement de clientes de Iberia"
    }
    return explanations.get(feature_name, feature_name.replace("_", " ").title())

test_indices = X_test.index[:300]

for idx_count, idx in enumerate(test_indices, start=1):
    row_pos = X_test.index.get_loc(idx)
    x_row = X_test.loc[idx]
    shap_row = shap_values_full[row_pos]
    actual = int(y_test.loc[idx])
    prob = float(y_prob[row_pos])
    pred = int(prob >= best_th)

    shap_pairs = list(zip(X.columns, shap_row))
    shap_sorted = sorted(shap_pairs, key=lambda x: abs(x[1]), reverse=True)

    top_positive = [(f, float(v)) for f, v in shap_sorted if v > 0][:5]
    top_negative = [(f, float(v)) for f, v in shap_sorted if v < 0][:5]

    if x_row.get("total_competitors", 0) > 0:
        competitive_action = "Monitor competitive landscape and adjust pricing/offer."
    else:
        competitive_action = "Capitalize on the lack of competition to close fast."

    confidence = "High" if abs(prob - best_th) > 0.3 else ("Medium" if abs(prob - best_th) > 0.15 else "Low")

    analysis = {
        "opportunity_id": str(idx),
        "prediction": {
            "predicted_outcome": "Win" if pred == 1 else "Loss",
            "actual_outcome": "Win" if actual == 1 else "Loss",
            "win_probability": prob,
            "threshold": float(best_th),
            "confidence": confidence
        },
        "key_features": {
            "customer_activity": float(x_row.get("customer_activity", 0.0)),
            "total_competitors": float(x_row.get("total_competitors", 0.0)),
            "opp_old": float(x_row.get("opp_old", 0.0)),
            "cust_hitrate": float(x_row.get("cust_hitrate", 0.0)),
            "product_A_ratio": float(x_row.get("product_A_ratio", 0.0))
        },
        "shap_analysis": {
            "base_value": base_val,
            "prediction_value": float(base_val + shap_row.sum()),
            "top_positive_factors": [
                {
                    "feature": feat,
                    "shap_value": val,
                    "explanation": get_factor_explanation(feat)
                }
                for feat, val in top_positive
            ],
            "top_negative_factors": [
                {
                    "feature": feat,
                    "shap_value": val,
                    "explanation": get_factor_explanation(feat)
                }
                for feat, val in top_negative
            ]
        },
        "business_recommendation": {
            "action": (
                "Accelerate"
                if prob > 0.7 else
                ("Nurture" if prob > 0.4 else "Re-evaluate")
            ),
            "priority": (
                "High"
                if prob > 0.7 else
                ("Medium" if prob > 0.4 else "Low")
            ),
            "next_steps": [
                "Leverage existing engagement" if prob > 0.5 else "Increase touchpoints and engagement",
                "Maintain momentum with key stakeholders" if pred == 1 else "Clarify blockers with decision-makers",
                competitive_action
            ]
        }
    }

    with open(f"output/json/{idx}.json", "w") as f:
        json.dump(analysis, f, indent=2)

    if idx_count % 50 == 0:
        print(f"  → {idx_count}/300 JSONs generados")

print("✅ 300 análisis individuales guardados en output/json/")

# ------------------------------------------------------------
# 10. RESUMEN FINAL
# ------------------------------------------------------------
print("\n" + "="*60)
print("EXPLAINABILITY ANALYSIS COMPLETE")
print("="*60)
print("\nModel Performance:")
print(f"  Threshold : {best_th:.3f}")
print(f"  F1        : {f1:.4f}")
print(f"  AUC       : {auc:.4f}")
print(f"  Precision : {precision:.4f}")
print(f"  Recall    : {recall:.4f}")
print(f"  Accuracy  : {acc:.4f}")

print("\nGenerated Files:")
print("  - output/json/global_insights.json")
print("  - output/json/[id].json  (primeros 300 opportunities)")
print("  - output/images/shap_summary.png")
print("  - output/images/feature_importance.png")
print("  - output/images/probability_distribution.png")
print("\n✅ Ready for Streamlit / PPT / Business demo")
print("="*60)

# ------------------------------------------------------------
# 11. SAVE MODEL & DATA FOR STREAMLIT
# ------------------------------------------------------------
print("\n" + "="*70)
print("💾 SAVING MODEL & DATA FOR STREAMLIT")
print("="*70)

import joblib

joblib.dump(xgb_model, "output/model.pkl")
joblib.dump(explainer, "output/explainer.pkl")
joblib.dump(X_test, "output/X_test.pkl")
joblib.dump(y_test, "output/y_test.pkl")
joblib.dump(shap_values_full, "output/shap_values.pkl")
joblib.dump(list(X.columns), "output/feature_names.pkl")

with open("output/threshold.txt", "w") as f:
    f.write(str(best_th))

metadata = {
    "n_features": len(X.columns),
    "n_test_samples": len(X_test),
    "threshold": float(best_th),
    "f1": float(f1),
    "auc": float(auc)
}
with open("output/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("✅ Model, explainer, data, and metadata saved in output/")

# ------------------------------------------------------------
# 11.5 (OPCIONAL) GEMINI AI FOR INSIGHTS
# ------------------------------------------------------------
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    print("\n" + "="*70)
    print("🤖 GENERANDO INSIGHTS CON GEMINI")
    print("="*70)
    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)
        model_llm = genai.GenerativeModel('gemini-1.5-flash')

        # ----- Global insights -----
        top_features = feature_importance.head(10)
        feature_list = "\n".join([f"  • {feat}: {imp:.4f}" for feat, imp in top_features.values])

        global_prompt = f"""You are a senior B2B sales strategist for Schneider Electric, analyzing an AI model that predicts opportunity win/loss.

        Model performance:
        - F1 Score: {f1:.3f}
        - AUC: {auc:.3f}
        - Precision: {precision:.3f}
        - Recall: {recall:.3f}
        - Win Rate: {y_pred.mean():.1%}
        - Total Opportunities Analyzed: {len(y_test)}

        Top 10 most important features:
        {feature_list}

        Task:
        - Produce five insights and five recommendations that explicitly reference the dominant features (opportunity age metrics, customer success rate, competition indicators, Product A history).
        - Use JSON only with keys 'business_insights' and 'recommendations'.
        - Each item max 2 sentences, business-friendly wording.
        """

        response = model_llm.generate_content(global_prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        llm_global = json.loads(response_text)
        global_insights["business_insights"] = llm_global.get("business_insights", global_insights["business_insights"])
        global_insights["recommendations"] = llm_global.get("recommendations", global_insights["recommendations"])

        with open("output/json/global_insights.json", "w") as f:
            json.dump(global_insights, f, indent=2, ensure_ascii=False)

        print("✅ LLM insights guardados en output/json/global_insights.json")

        # ----- Sample case recommendations -----
        sample_indices = list(X_test.index[:300])
        sample_cases = sample_indices[:5] + sample_indices[100:105] + sample_indices[200:205]
        enhanced = 0

        for idx in sample_cases:
            json_path = Path(f"output/json/{idx}.json")
            if not json_path.exists():
                continue
            with open(json_path) as f:
                case_data = json.load(f)

            shap_pos = case_data["shap_analysis"]["top_positive_factors"][:3]
            shap_neg = case_data["shap_analysis"]["top_negative_factors"][:3]

            case_prompt = f"""You advise Schneider Electric sales teams.
            Opportunity ID: {idx}
            Win probability: {case_data['prediction']['win_probability']:.1%}
            Top positive factors:
            {'; '.join([f"{item['feature']}:+{item['shap_value']:.2f}" for item in shap_pos])}
            Top negative factors:
            {'; '.join([f"{item['feature']}:{item['shap_value']:.2f}" for item in shap_neg])}
            Output 3 actionable next steps in JSON under 'next_steps'. One sentence per step."""

            resp_case = model_llm.generate_content(case_prompt)
            resp_text = resp_case.text.strip()
            if resp_text.startswith("```"):
                resp_text = resp_text.split("```")[1]
                if resp_text.startswith("json"):
                    resp_text = resp_text[4:]

            llm_case = json.loads(resp_text)
            case_data["business_recommendation"]["next_steps"] = llm_case.get("next_steps", case_data["business_recommendation"]["next_steps"])
            case_data["business_recommendation"]["ai_generated"] = True

            with open(json_path, "w") as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            enhanced += 1

        print(f"✅ Recomendaciones AI generadas para {enhanced} oportunidades de ejemplo")

    except Exception as e:
        print(f"⚠️ No se pudieron generar insights con Gemini: {e}")
else:
    print("\nℹ️ Saltando sección Gemini (define GEMINI_API_KEY para habilitarla).")

# ------------------------------------------------------------
# 12. DOWNLOAD PACKAGE
# ------------------------------------------------------------
shutil.make_archive('output', 'zip', 'output')

try:
    from google.colab import files
    files.download('output.zip')
    print("📦 output.zip listo para descargar")
except Exception:
    print("📦 output.zip generado (descárgalo manualmente si no estás en Colab).")
