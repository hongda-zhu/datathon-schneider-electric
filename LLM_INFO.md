# 🤖 LLM Implementation - Gemini 2.0-Flash

## ✅ 是的，有 LLM！(Yes, there is LLM!)

**Model:** Google Gemini 2.0-Flash
**Status:** ✅ Active and working
**Cases with AI:** 15 opportunities (5% of test set)

---

## 📍 在哪里？(Where is it?)

### 1. Code Location (代码位置)
File: `local_pipeline.py` (lines 543-663)

```python
# Line 543-663: GEMINI AI FOR INSIGHTS
gemini_key = os.environ.get("GEMINI_API_KEY")
if gemini_key:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model_llm = genai.GenerativeModel('gemini-2.0-flash')
```

### 2. Configuration (配置)
File: `.env`
```
GEMINI_API_KEY=AIzaSyAGltKL6hvhZ9L3YHCqglSafDUz_YTTcR4
```

### 3. Output Files (输出文件)
```
output/json/
├── global_insights.json     # Global insights (LLM-enhanced)
├── 13701.json              # Case with AI (ai_generated: true)
├── 13982.json              # Case with AI
├── 14992.json              # Case with AI
├── 15435.json              # Case with AI
└── ... (15 cases total with AI)
```

---

## 🎯 怎么用的？(How does it work?)

### What the LLM Does:

#### 1. **Global Business Insights** (全局洞察)
- Analyzes top 10 most important features
- Generates 5 business insights in business-friendly language
- Generates 5 actionable recommendations

**Input to LLM:**
```
Model performance: F1=0.837, AUC=0.922
Top features: opp_maturity, opp_age_squared, cust_hitrate...

Task: Generate 5 business insights and 5 recommendations
```

**LLM Output Example:**
```json
{
  "business_insights": [
    "Opportunity maturity and age are strong indicators...",
    "High customer hit rate is a positive signal..."
  ],
  "recommendations": [
    "Develop stricter qualification criteria for old opportunities...",
    "Invest in competitive intelligence..."
  ]
}
```

#### 2. **Case-Specific Action Plans** (个案行动计划)
For 15 sample opportunities, the LLM generates **3 specific next steps** based on SHAP values.

**Input to LLM:**
```
Opportunity ID: 13701
Win probability: 78.6%

Top positive factors:
- cust_hitrate: +0.264
- customer_activity: +0.195

Top negative factors:
- customer_engagement: -0.222
- product_A: -0.159

Task: Generate 3 actionable next steps
```

**LLM Output Example:**
```json
{
  "next_steps": [
    "Increase engagement with the customer beyond the current level to
     address the 'customer_engagement' negative factor",
    "Proactively propose alternative Schneider Electric products to
     decrease reliance on 'product_A'",
    "Leverage the positive 'iberia_engagement' by showcasing successful
     case studies from other Iberia customers"
  ]
}
```

---

## 🔍 怎么看？(How to view it?)

### Method 1: Dashboard (推荐)

```bash
streamlit run app_final.py
```

**Steps:**
1. Go to **Case Explorer**
2. Select one of these IDs (有AI的案例):
   - **13701** (Win 78.6% - High priority)
   - **14992** (Win 97.5% - Very high)
   - **3414** (Win 13.5% - Needs help)
   - **13982**, **15435**, **16232**, etc.

3. Scroll down to **"🎯 Recommended Action"**
4. You'll see AI-generated next steps like:
   ```
   Next Steps:
   1. Increase engagement with customer to address
      'customer_engagement' negative factor...
   2. Proactively propose alternative products...
   3. Leverage positive 'iberia_engagement'...
   ```

### Method 2: JSON Files (直接查看)

```bash
# View AI-generated case
cat output/json/13701.json | jq '.business_recommendation'
```

**Look for:**
```json
{
  "ai_generated": true,  ← This means LLM was used
  "next_steps": [
    "Specific action based on SHAP values..."
  ]
}
```

### Method 3: Compare AI vs Non-AI

**Case WITH AI (有AI):**
```bash
cat output/json/13701.json | jq '.business_recommendation.next_steps'
```
Output:
```
"Increase engagement... addressing 'customer_engagement' -0.22 impact"
```

**Case WITHOUT AI (没有AI):**
```bash
cat output/json/102.json | jq '.business_recommendation.next_steps'
```
Output:
```
"Leverage existing engagement"  ← Generic rule
```

---

## 📊 Statistics (统计)

```
Total test cases:        7,180
With JSON analysis:        300
With AI recommendations:    15 (5%)
Without AI:                285 (95% - use simple rules)
```

**Why only 15?**
- API quota limit: 15 requests/minute (free tier)
- Script generates AI for sample cases (first 5 + middle 5 + last 5)

---

## 🧪 Verify It's Working (验证方法)

### Quick Test:
```bash
# Check if LLM generated insights
cat output/json/global_insights.json | jq '.business_insights[0]'
```

Expected output (LLM-generated):
```
"Opportunity maturity and age are strong indicators, suggesting
timing and deal progression are critical factors..."
```

### Dashboard Test:
```bash
streamlit run app_final.py
```

1. **Global Insights** page → See business insights (LLM-enhanced)
2. **Case Explorer** → ID 13701 → See AI-generated next steps

---

## 🎯 Key Difference: AI vs Rules

| Feature | Without AI (规则) | With AI (LLM) |
|---------|-------------------|---------------|
| **Next Steps** | Generic templates | Specific to SHAP values |
| **Example** | "Leverage existing engagement" | "Increase engagement to address -0.22 impact of customer_engagement" |
| **Context** | None | References actual SHAP factors |
| **Language** | Simple | Business-friendly explanations |

---

## ✅ Summary (总结)

**是的，LLM 在运行！**

- ✅ Using: Google Gemini 2.0-Flash
- ✅ Location: `local_pipeline.py` lines 543-663
- ✅ API Key: Configured in `.env`
- ✅ Output: 15 cases with AI-generated recommendations
- ✅ Visible in: Dashboard (Case Explorer) and JSON files

**View in dashboard:**
```bash
streamlit run app_final.py
# Go to Case Explorer → Select ID 13701
# See AI-generated "Next Steps" in 🎯 Recommended Action
```
