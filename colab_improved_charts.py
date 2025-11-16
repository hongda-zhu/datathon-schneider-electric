# ------------------------------------------------------------
# IMPROVED VISUALIZATION SECTION FOR COLAB
# Replace section 7 (SHAP) in your Colab with this
# ------------------------------------------------------------

print("\n" + "="*70)
print("🔍 SHAP EXPLAINABILITY - IMPROVED CHARTS")
print("="*70)

import shap
import matplotlib.pyplot as plt
import seaborn as sns

shap.initjs()

# Dictionary for translating feature names to business language
FEATURE_TRANSLATIONS = {
    "customer_activity": "Customer Activity Level",
    "customer_engagement": "Customer Engagement",
    "total_competitors": "Total Competitors",
    "competitor_diversity": "Competitor Diversity",
    "opp_old": "Opportunity Age",
    "opp_maturity": "Opportunity Maturity",
    "opp_quality_score": "Quality Score",
    "product_A_ratio": "Product A Ratio",
    "total_past_sales": "Past Sales Volume",
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

def translate_feature(feature_name):
    """Translate technical name to business language"""
    return FEATURE_TRANSLATIONS.get(feature_name, feature_name.replace("_", " ").title())

# Create explainer
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

# Create translated feature names for X_sample
X_sample_translated = X_sample.copy()
X_sample_translated.columns = [translate_feature(col) for col in X_sample.columns]

# ------------------------------------------------------------
# 7.1 IMPROVED SHAP SUMMARY PLOT
# ------------------------------------------------------------
print("\nGenerating improved SHAP summary plot...")

plt.figure(figsize=(12, 8))

# Use better color scheme and larger fonts
shap.summary_plot(
    shap_sample,
    X_sample_translated,
    show=False,
    max_display=15,  # Show top 15 for clarity
    plot_size=(12, 8),
    color_bar_label="Feature Value"
)

# Improve title and labels
plt.title(
    "Feature Impact on Win Probability",
    fontsize=16,
    fontweight="bold",
    pad=20,
    color='#1a1a1a'
)
plt.xlabel("Impact on Win Probability", fontsize=13, fontweight='bold', color='#1a1a1a')
plt.ylabel("Features (Ranked by Importance)", fontsize=13, fontweight='bold', color='#1a1a1a')

# Add subtle note
plt.figtext(
    0.99, 0.01,
    "Red = High value | Blue = Low value | Right = Increases win chance | Left = Decreases win chance",
    ha="right",
    fontsize=10,
    style='italic',
    color='#666666'
)

plt.tight_layout()
plt.savefig("output/images/shap_summary.png", dpi=300, bbox_inches="tight", facecolor='white')
plt.close()
print("✅ Saved: output/images/shap_summary.png")

# ------------------------------------------------------------
# 7.2 IMPROVED FEATURE IMPORTANCE PLOT
# ------------------------------------------------------------
print("\nGenerating improved feature importance plot...")

feature_importance = pd.DataFrame({
    "feature": X.columns,
    "importance": xgb_model.feature_importances_
}).sort_values("importance", ascending=False)

# Translate feature names
feature_importance['feature_translated'] = feature_importance['feature'].apply(translate_feature)

# Create professional bar plot
plt.figure(figsize=(10, 8))

top_15 = feature_importance.head(15)

# Use color gradient for bars
colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_15)))

ax = sns.barplot(
    data=top_15,
    x="importance",
    y="feature_translated",
    orient="h",
    palette=colors,
    edgecolor='white',
    linewidth=0.5
)

# Improve title and labels
plt.title(
    "Which Features Matter Most?",
    fontsize=16,
    fontweight="bold",
    pad=20,
    color='#1a1a1a'
)
plt.xlabel("Importance Score", fontsize=13, fontweight='bold', color='#1a1a1a')
plt.ylabel("", fontsize=13)  # No label needed, self-explanatory

# Add value labels on bars
for i, (idx, row) in enumerate(top_15.iterrows()):
    ax.text(
        row['importance'] + 0.002,
        i,
        f"{row['importance']:.3f}",
        va='center',
        fontsize=9,
        color='#1a1a1a'
    )

# Add subtle note
plt.figtext(
    0.99, 0.01,
    "Higher scores = More influence on predictions",
    ha="right",
    fontsize=10,
    style='italic',
    color='#666666'
)

plt.tight_layout()
plt.savefig("output/images/feature_importance.png", dpi=300, bbox_inches="tight", facecolor='white')
plt.close()
print("✅ Saved: output/images/feature_importance.png")

# ------------------------------------------------------------
# 7.3 IMPROVED PROBABILITY DISTRIBUTION
# ------------------------------------------------------------
print("\nGenerating improved probability distribution plots...")

plt.figure(figsize=(14, 6))

# Left plot: Distribution by actual outcome
plt.subplot(1, 2, 1)
plt.hist(
    y_prob[y_test == 0],
    bins=30,
    alpha=0.7,
    label="Actual Loss",
    color="#e74c3c",
    edgecolor='white',
    linewidth=0.5
)
plt.hist(
    y_prob[y_test == 1],
    bins=30,
    alpha=0.7,
    label="Actual Win",
    color="#27ae60",
    edgecolor='white',
    linewidth=0.5
)

plt.xlabel("Predicted Win Probability", fontsize=12, fontweight='bold', color='#1a1a1a')
plt.ylabel("Number of Opportunities", fontsize=12, fontweight='bold', color='#1a1a1a')
plt.title("Probability Distribution by Actual Outcome", fontsize=14, fontweight="bold", color='#1a1a1a')
plt.legend(fontsize=11, framealpha=0.9)
plt.grid(alpha=0.2, linestyle='--')

# Right plot: Confidence levels
plt.subplot(1, 2, 2)
bins_prob = [0, 0.3, 0.5, 0.7, 1.0]
labels_prob = ["Low\n(0-30%)", "Medium\n(30-50%)", "High\n(50-70%)", "Very High\n(70-100%)"]
prob_categories = pd.cut(y_prob, bins=bins_prob, labels=labels_prob)
category_counts = prob_categories.value_counts().sort_index()

colors_conf = ["#e74c3c", "#f39c12", "#2ecc71", "#27ae60"]
bars = plt.bar(
    range(len(category_counts)),
    category_counts.values,
    color=colors_conf,
    edgecolor='white',
    linewidth=1.5,
    width=0.7
)

plt.xticks(range(len(category_counts)), labels_prob, fontsize=11, color='#1a1a1a')
plt.xlabel("Confidence Level", fontsize=12, fontweight='bold', color='#1a1a1a')
plt.ylabel("Number of Opportunities", fontsize=12, fontweight='bold', color='#1a1a1a')
plt.title("Prediction Confidence Distribution", fontsize=14, fontweight="bold", color='#1a1a1a')
plt.grid(alpha=0.2, linestyle='--', axis='y')

# Add count labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2.,
        height,
        f'{int(height)}',
        ha='center',
        va='bottom',
        fontsize=11,
        fontweight='bold',
        color='#1a1a1a'
    )

plt.tight_layout()
plt.savefig("output/images/probability_distribution.png", dpi=300, bbox_inches="tight", facecolor='white')
plt.close()
print("✅ Saved: output/images/probability_distribution.png")

print("\n✅ All improved visualizations generated!")
