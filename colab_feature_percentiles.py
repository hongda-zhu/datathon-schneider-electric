# ------------------------------------------------------------
# ADD TO COLAB SECTION 8 (Global Insights Generation)
# Calculate feature percentiles for Low/Avg/High labels
# Insert BEFORE saving global_insights.json
# ------------------------------------------------------------

print("\n📊 Calculating feature percentiles for context labels...")

import numpy as np
import pandas as pd

# Calculate percentiles for key features
key_features = [
    'customer_activity',
    'total_competitors',
    'opp_old',
    'cust_hitrate',
    'product_A_ratio',
    'customer_engagement',
    'competitor_diversity',
    'opp_age_squared',
    'cust_interactions',
    'cust_contracts'
]

feature_stats = {}

for feature in key_features:
    if feature in X.columns:
        values = X[feature]

        feature_stats[feature] = {
            "mean": float(values.mean()),
            "median": float(values.median()),
            "std": float(values.std()),
            "p25": float(values.quantile(0.25)),
            "p50": float(values.quantile(0.50)),
            "p75": float(values.quantile(0.75)),
            "min": float(values.min()),
            "max": float(values.max())
        }

# Add feature stats to global_insights
global_insights["feature_statistics"] = feature_stats

print("✅ Feature statistics calculated:")
print(f"  • {len(feature_stats)} features with percentiles")
print("\nExample (customer_activity):")
if 'customer_activity' in feature_stats:
    stats = feature_stats['customer_activity']
    print(f"  • P25 (Low threshold): {stats['p25']:.3f}")
    print(f"  • P50 (Median): {stats['p50']:.3f}")
    print(f"  • P75 (High threshold): {stats['p75']:.3f}")

# Now save global_insights with feature_statistics included
# (Your existing code to save global_insights.json goes here)
