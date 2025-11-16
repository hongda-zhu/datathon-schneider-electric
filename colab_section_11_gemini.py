# ------------------------------------------------------------
# 11.5 GEMINI AI - DYNAMIC INSIGHTS GENERATION
# Add this section to your Colab after section 11
# ------------------------------------------------------------

print("\n" + "="*70)
print("🤖 GENERATING AI-POWERED INSIGHTS WITH GEMINI")
print("="*70)

# Install Google Generative AI
!pip install -q google-generativeai

import google.generativeai as genai
import json

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAGltKL6hvhZ9L3YHCqglSafDUz_YTTcR4"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

print("✅ Gemini API configured")

# ------------------------------------------------------------
# A. GENERATE GLOBAL BUSINESS INSIGHTS
# ------------------------------------------------------------
print("\n📊 Generating global business insights...")

# Prepare data summary for Gemini
top_features = feature_importance.head(10).to_dict()
feature_list = "\n".join([f"  • {feat}: {imp:.4f}" for feat, imp in top_features.items()])

global_prompt = f"""You are a senior B2B sales strategist for Schneider Electric, analyzing an AI model that predicts opportunity win/loss.

**Model Performance:**
- F1 Score: {f1:.3f}
- AUC: {auc:.3f}
- Precision: {precision:.3f}
- Recall: {recall:.3f}
- Win Rate: {y_pred.mean():.1%}
- Total Opportunities Analyzed: {len(y_test)}

**Top 10 Most Important Features (by model importance):**
{feature_list}

**CRITICAL OBSERVATIONS:**
1. The TWO most important features are opp_old and opp_age_squared (opportunity age metrics), which together account for ~40% of total model importance. This means OPPORTUNITY AGE is the DOMINANT factor.
2. Customer success rate (cust_hitrate) is the third most important at ~3.5%.
3. Competitor-related features (competitor_diversity, competition metrics) are also significant.
4. Historical Product A sales indicators appear multiple times in the top features.
5. Customer engagement has much LOWER importance than the features above.

**Task:**
Generate 5 business insights and 5 recommendations that EXPLICITLY focus on the features listed above, especially opportunity age (opp_old, opp_age_squared), customer success rate (cust_hitrate), and competition indicators.

**Output Format (JSON only, no markdown):**
{{
  "business_insights": [
    "insight 1 - must mention opportunity age as the dominant factor",
    "insight 2 - must mention competition indicators",
    "insight 3 - must mention customer success rate or Product A history",
    "insight 4 - another pattern from the top features",
    "insight 5 - regional or product-specific insight"
  ],
  "recommendations": [
    "recommendation 1 - specific action related to opportunity age management",
    "recommendation 2 - action related to competitive intelligence",
    "recommendation 3 - action related to customer success rate or historical sales",
    "recommendation 4 - another actionable step based on top features",
    "recommendation 5 - resource allocation or prioritization strategy"
  ]
}}

**Requirements:**
1. FIRST insight MUST explain that opportunity age (opp_old + opp_age_squared) is the strongest predictor
2. Insights must be based on the ACTUAL top features listed above, not generic sales advice
3. Recommendations must be SPECIFIC and ACTIONABLE
4. Use business language: "opportunity age" not "opp_old", "customer success rate" not "cust_hitrate"
5. Each point should be 1-2 sentences maximum
6. Return ONLY valid JSON, no extra text
"""

try:
    response = model.generate_content(global_prompt)
    response_text = response.text.strip()

    # Clean response (remove markdown code blocks if present)
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    llm_global = json.loads(response_text)

    # Update global insights with LLM-generated content
    global_insights["business_insights"] = llm_global["business_insights"]
    global_insights["recommendations"] = llm_global["recommendations"]

    print("✅ Global insights generated:")
    print(f"  • {len(llm_global['business_insights'])} business insights")
    print(f"  • {len(llm_global['recommendations'])} recommendations")

except Exception as e:
    print(f"⚠️ Error generating global insights: {e}")
    print("   Using default insights instead")

# Save updated global insights
with open("output/json/global_insights.json", "w") as f:
    json.dump(global_insights, f, indent=2, ensure_ascii=False)

print("✅ Saved: output/json/global_insights.json (with AI insights)")

# ------------------------------------------------------------
# B. GENERATE INDIVIDUAL CASE RECOMMENDATIONS (Sample)
# ------------------------------------------------------------
print("\n👤 Generating AI recommendations for individual cases...")

# Select representative cases (high/medium/low probability)
high_prob_cases = [idx for idx, p in zip(X_test.index[:300], y_prob[:300]) if p > 0.7][:5]
med_prob_cases = [idx for idx, p in zip(X_test.index[:300], y_prob[:300]) if 0.4 < p <= 0.7][:5]
low_prob_cases = [idx for idx, p in zip(X_test.index[:300], y_prob[:300]) if p <= 0.4][:5]

sample_cases = high_prob_cases + med_prob_cases + low_prob_cases
total_enhanced = 0

for idx in sample_cases:
    if idx not in X_test.index:
        continue

    row_pos = X_test.index.get_loc(idx)
    x_row = X_test.loc[idx]
    shap_row = shap_values_full[row_pos]
    prob = float(y_prob[row_pos])

    # Load existing JSON
    json_path = f"output/json/{idx}.json"
    try:
        with open(json_path) as f:
            case_data = json.load(f)
    except:
        continue

    # Get top factors
    shap_pairs = list(zip(X.columns, shap_row))
    shap_sorted = sorted(shap_pairs, key=lambda x: abs(x[1]), reverse=True)
    top_positive = [(f, float(v)) for f, v in shap_sorted if v > 0][:3]
    top_negative = [(f, float(v)) for f, v in shap_sorted if v < 0][:3]

    # Prepare prompt
    case_prompt = f"""You are a sales strategy advisor for Schneider Electric.

**Opportunity Details:**
- ID: {idx}
- Win Probability: {prob:.1%}
- Customer Activity: {x_row.get('customer_activity', 0):.3f}
- Competitors: {x_row.get('total_competitors', 0):.0f}
- Opportunity Age: {x_row.get('opp_old', 0):.3f}

**Top Positive Factors (increase win chance):**
{chr(10).join([f"  • {f}: +{v:.3f}" for f, v in top_positive])}

**Top Negative Factors (decrease win chance):**
{chr(10).join([f"  • {f}: {v:.3f}" for f, v in top_negative])}

**Task:**
Generate 3 specific, actionable next steps for the sales team to maximize win probability.

**Output Format (JSON only):**
{{
  "next_steps": [
    "specific action 1",
    "specific action 2",
    "specific action 3"
  ]
}}

**Requirements:**
1. Be SPECIFIC (mention actual factors from the data)
2. Be ACTIONABLE (clear steps to take)
3. Prioritize highest-impact actions
4. Each step should be 1 sentence
5. Return ONLY valid JSON
"""

    try:
        response = model.generate_content(case_prompt)
        response_text = response.text.strip()

        # Clean response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        llm_rec = json.loads(response_text)

        # Update case JSON with AI recommendations
        case_data["business_recommendation"]["next_steps"] = llm_rec["next_steps"]
        case_data["business_recommendation"]["ai_generated"] = True

        # Save updated JSON
        with open(json_path, "w") as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)

        total_enhanced += 1

    except Exception as e:
        print(f"  ⚠️ Error for case {idx}: {e}")
        continue

print(f"✅ Enhanced {total_enhanced}/{len(sample_cases)} sample cases with AI recommendations")

# ------------------------------------------------------------
# C. SUMMARY
# ------------------------------------------------------------
print("\n" + "="*70)
print("✅ AI INSIGHT GENERATION COMPLETE")
print("="*70)
print("\nGenerated:")
print(f"  • Global business insights: {len(global_insights['business_insights'])}")
print(f"  • Global recommendations: {len(global_insights['recommendations'])}")
print(f"  • Enhanced individual cases: {total_enhanced}")
print("\n📁 All AI-generated insights saved to output/json/")
print("\n🚀 Ready for Streamlit dashboard!")
print("="*70)
