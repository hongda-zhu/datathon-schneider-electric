# ------------------------------------------------------------
# ADD TO COLAB SECTION 7 (SHAP Analysis)
# Insert this code AFTER calculating shap_values_full
# ------------------------------------------------------------

import numpy as np

print("\n📊 Calculating top SHAP drivers (positive/negative)...")

# Calculate mean SHAP value for each feature across all samples
mean_shap_values = np.mean(shap_values_full, axis=0)

# Create feature-shap pairs
feature_shap_pairs = list(zip(X.columns, mean_shap_values))

# Separate positive (increase win) and negative (decrease win) drivers
positive_drivers = [(feat, float(val)) for feat, val in feature_shap_pairs if val > 0]
negative_drivers = [(feat, float(val)) for feat, val in feature_shap_pairs if val < 0]

# Sort by magnitude
positive_drivers = sorted(positive_drivers, key=lambda x: x[1], reverse=True)[:3]
negative_drivers = sorted(negative_drivers, key=lambda x: x[1])[:3]

# Add to global_insights dictionary
global_insights["shap_drivers"] = {
    "top_positive": [
        {"feature": feat, "mean_shap": val}
        for feat, val in positive_drivers
    ],
    "top_negative": [
        {"feature": feat, "mean_shap": val}
        for feat, val in negative_drivers
    ]
}

print("✅ Top 3 Positive Drivers (increase win probability):")
for feat, val in positive_drivers:
    print(f"  • {feat}: +{val:.4f}")

print("\n✅ Top 3 Negative Drivers (decrease win probability):")
for feat, val in negative_drivers:
    print(f"  • {feat}: {val:.4f}")

# Now save global_insights with this new data
# (Your existing code to save global_insights.json goes here)
