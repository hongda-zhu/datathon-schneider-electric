"""
Run only the LLM insights generation part
"""
import os
import json
from pathlib import Path
import joblib
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Load pre-computed data
X_test = joblib.load("output/X_test.pkl")
y_test = joblib.load("output/y_test.pkl")
model = joblib.load("output/model.pkl")

# Load global insights
with open("output/json/global_insights.json") as f:
    global_insights = json.load(f)

# Get predictions
y_prob = model.predict_proba(X_test)[:, 1]
best_th = global_insights["model_performance"]["threshold"]
y_pred = (y_prob >= best_th).astype(int)

# Feature importance
feature_importance = pd.DataFrame({
    "feature": list(global_insights["feature_importance_top20"].keys()),
    "importance": list(global_insights["feature_importance_top20"].values())
})

gemini_key = os.environ.get("GEMINI_API_KEY")
if not gemini_key:
    print("❌ GEMINI_API_KEY not found in environment")
    exit(1)

print("="*70)
print("🤖 GENERANDO INSIGHTS CON GEMINI 2.0-FLASH")
print("="*70)

try:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model_llm = genai.GenerativeModel('gemini-2.0-flash')

    # ----- Global insights -----
    top_features = feature_importance.head(10)
    feature_list = "\n".join([f"  • {feat}: {imp:.4f}" for feat, imp in top_features.values])

    global_prompt = f"""You are a senior B2B sales strategist for Schneider Electric, analyzing an AI model that predicts opportunity win/loss.

Model performance:
- F1 Score: {global_insights['model_performance']['f1_score']:.3f}
- AUC: {global_insights['model_performance']['auc']:.3f}
- Precision: {global_insights['model_performance']['precision']:.3f}
- Recall: {global_insights['model_performance']['recall']:.3f}
- Win Rate: {y_pred.mean():.1%}
- Total Opportunities Analyzed: {len(y_test)}

Top 10 most important features:
{feature_list}

Task:
- Produce five insights and five recommendations that explicitly reference the dominant features (opportunity age metrics, customer success rate, competition indicators, Product A history).
- Use JSON only with keys 'business_insights' and 'recommendations'.
- Each item max 2 sentences, business-friendly wording.
"""

    print("\n🔄 Generating global insights...")
    response = model_llm.generate_content(global_prompt)
    response_text = response.text.strip()

    # Clean markdown code blocks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    llm_global = json.loads(response_text)

    # Extract text from responses (handle both dict and string formats)
    insights = llm_global.get("business_insights", global_insights["business_insights"])
    recommendations = llm_global.get("recommendations", global_insights["recommendations"])

    # If LLM returned objects with 'text' field, extract just the text
    if insights and isinstance(insights[0], dict):
        insights = [item.get("text", str(item)) for item in insights]
    if recommendations and isinstance(recommendations[0], dict):
        recommendations = [item.get("text", str(item)) for item in recommendations]

    global_insights["business_insights"] = insights
    global_insights["recommendations"] = recommendations

    with open("output/json/global_insights.json", "w") as f:
        json.dump(global_insights, f, indent=2, ensure_ascii=False)

    print("✅ LLM global insights guardados")
    print("\n📋 Business Insights:")
    for i, insight in enumerate(global_insights["business_insights"], 1):
        print(f"  {i}. {insight}")

    print("\n📋 Recommendations:")
    for i, rec in enumerate(global_insights["recommendations"], 1):
        print(f"  {i}. {rec}")

    # ----- Sample case recommendations -----
    print("\n🔄 Generating case-specific recommendations...")
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

Output 3 actionable next steps in JSON format under 'next_steps' key. One sentence per step. Focus on concrete actions based on the SHAP factors."""

        resp_case = model_llm.generate_content(case_prompt)
        resp_text = resp_case.text.strip()

        # Clean markdown
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
        print(f"  ✓ Enhanced opportunity {idx}")

    print(f"\n✅ Recomendaciones AI generadas para {enhanced} oportunidades")

except Exception as e:
    print(f"⚠️ Error con Gemini: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("✅ LLM INSIGHTS COMPLETE")
print("="*70)
