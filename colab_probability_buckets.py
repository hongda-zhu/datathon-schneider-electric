# ------------------------------------------------------------
# ADD TO COLAB SECTION 8 (Global Insights Generation)
# Insert this code BEFORE saving global_insights.json
# ------------------------------------------------------------

# Calculate probability distribution buckets
import numpy as np

# Define probability buckets
bins = [0, 0.3, 0.5, 0.7, 1.0]
labels = ['Low (0-30%)', 'Medium (30-50%)', 'High (50-70%)', 'Very High (70-100%)']

# Count opportunities in each bucket
bucket_counts = {}
for i in range(len(bins) - 1):
    count = np.sum((y_prob >= bins[i]) & (y_prob < bins[i+1]))
    bucket_counts[labels[i]] = int(count)

# Handle upper boundary (include 1.0)
if bins[-1] == 1.0:
    bucket_counts[labels[-1]] = int(np.sum((y_prob >= bins[-2]) & (y_prob <= bins[-1])))

# Add to global_insights dictionary
global_insights["prediction_distribution"]["probability_buckets"] = bucket_counts

print("\n📊 Probability Distribution by Buckets:")
for bucket, count in bucket_counts.items():
    percentage = (count / len(y_prob)) * 100
    print(f"  {bucket}: {count} ({percentage:.1f}%)")

# Now save global_insights with the new data
# (Your existing code to save global_insights.json goes here)
