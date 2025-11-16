"""
Update key_features in existing JSONs to replace opp_old with opp_quality_score
"""
import json
import joblib
from pathlib import Path

X_test = joblib.load("output/X_test.pkl")

# Update global insights feature_statistics
with open("output/json/global_insights.json") as f:
    global_insights = json.load(f)

# Add opp_quality_score stats, remove opp_old stats
if "opp_old" in global_insights["feature_statistics"]:
    del global_insights["feature_statistics"]["opp_old"]

series = X_test["opp_quality_score"]
global_insights["feature_statistics"]["opp_quality_score"] = {
    "median": float(series.median()),
    "p25": float(series.quantile(0.25)),
    "p75": float(series.quantile(0.75))
}

with open("output/json/global_insights.json", "w") as f:
    json.dump(global_insights, f, indent=2, ensure_ascii=False)

print("✅ Updated global_insights.json")

# Update individual case JSONs
json_files = list(Path("output/json").glob("*.json"))
json_files = [f for f in json_files if f.name != "global_insights.json"]

updated = 0
for json_path in json_files:
    case_id = int(json_path.stem)

    # Load JSON
    with open(json_path) as f:
        case_data = json.load(f)

    # Check if case exists in X_test
    if case_id not in X_test.index:
        continue

    # Update key_features
    if "key_features" in case_data:
        # Remove opp_old if present
        if "opp_old" in case_data["key_features"]:
            del case_data["key_features"]["opp_old"]

        # Add opp_quality_score
        case_data["key_features"]["opp_quality_score"] = float(
            X_test.loc[case_id, "opp_quality_score"]
        )

        # Save
        with open(json_path, "w") as f:
            json.dump(case_data, f, indent=2, ensure_ascii=False)

        updated += 1

print(f"✅ Updated {updated} case JSONs")
print(f"\nSample updated key_features:")
with open("output/json/102.json") as f:
    sample = json.load(f)
    print(json.dumps(sample["key_features"], indent=2))
