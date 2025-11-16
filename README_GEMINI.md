# ⚡ Schneider Electric - AI-Powered Opportunity Analyzer

**Final version with Gemini AI insights, professional tooltips, and English interface**

---

## 🎯 Quick Start (3 Steps)

### **Step 1: Ejecuta el pipeline completo en Colab**

1. Abre tu notebook en Colab.
2. Instala dependencias y descarga el dataset (`xgboost`, `shap`, etc.).
3. **Copia TODO `colab_full_pipeline.py` en una celda y ejecútala**.
4. (Opcional) Antes de ejecutar la celda, define tu API key:
   ```python
   import os
   os.environ["GEMINI_API_KEY"] = "tu_api_key"
   ```

El script:
- Entrena el modelo + genera SHAP/JSON.
- Calcula estadísticas necesarias para el dashboard.
- Guarda `output/` con modelos, imágenes y análisis.
- Integra Gemini si hay API key (insights globales + recomendaciones por caso).

Al finalizar:
```
🤖 GENERANDO INSIGHTS CON GEMINI
✅ LLM insights guardados en output/json/global_insights.json
✅ Recomendaciones AI generadas para N oportunidades
📦 output.zip listo para descargar
```

---

### **Step 2: Download Output**

In Colab:
```python
from google.colab import files
import shutil

shutil.make_archive('output', 'zip', 'output')
files.download('output.zip')
```

Extract `output.zip` to this folder (same location as `app_final.py`).

---

### **Step 3: Run Dashboard**

```bash
./run_final.sh
```

Or manually:
```bash
source venv/bin/activate
streamlit run app_final.py
```

Open: `http://localhost:8501`

---

## ✨ Features

### **🌍 Global Insights Page**
- Model performance metrics with **explanatory tooltips** (hover over ℹ️)
- Feature importance with **business-friendly names**
- SHAP summary with **detailed explanation** of how to read it
- **AI-generated business insights** (from Gemini)
- **AI-generated recommendations** (from Gemini)

### **🔍 Case Explorer Page**
- Select any opportunity by ID
- See prediction vs actual outcome
- SHAP waterfall explanation with **translated feature names**
- **AI-enhanced recommendations** for select cases

### **🎲 What-If Simulator Page**
- Adjust customer engagement, opportunity age, competitors
- See **real-time probability changes**
- Updated SHAP explanations
- Actionable recommendations based on simulation

---

## 🤖 AI Integration

**What Gemini generates:**

1. **Global Business Insights** (5 insights)
   - Explains WHY patterns exist in your data
   - Professional business language
   - Specific to your model results

2. **Global Recommendations** (5 actions)
   - WHAT the sales team should do
   - Actionable and specific
   - Prioritized by impact

3. **Individual Case Recommendations** (15 samples)
   - 3 specific next steps per opportunity
   - Tailored to each case's unique factors
   - High/medium/low probability mix

**API Cost:** ~$0.10 total (Gemini 1.5 Flash is very cheap)

---

## 📊 Tooltips Explained

Every metric has a tooltip. Hover over the ℹ️ icon to see:

**Example - F1 Score:**
```
F1 Score (0 to 1): Harmonic mean of Precision and Recall.

• High (>0.7): Model is very reliable
• Medium (0.5-0.7): Useful, with room for improvement
• Low (<0.5): Needs significant tuning

Calculated on test set by comparing predictions vs. actual outcomes.
```

**Available for:**
- F1 Score, AUC, Precision, Recall, Threshold
- Total Samples, Predicted Wins, Win Rate
- All key metrics

---

## 🎨 Feature Translations

Technical names → Business language:

| Before | After |
|--------|-------|
| `customer_activity` | Customer Activity Level |
| `customer_engagement` | Customer Engagement |
| `total_competitors` | Total Competitors |
| `opp_old` | Opportunity Age |
| `cust_hitrate` | Customer Success Rate |
| `cust_interactions` | Customer Interactions |

Applied to **all charts and displays**.

---

## 📁 Files

```
├── app_final.py                   ← MAIN DASHBOARD (English)
├── colab_full_pipeline.py         ← COPY TO COLAB (training + Gemini)
├── run_final.sh                   ← RUN THIS
├── FINAL_IMPLEMENTATION_GUIDE.md  ← DETAILED GUIDE
├── venv/                          ← Python environment
└── output/ (from Colab)           ← EXTRACT HERE
    ├── model.pkl / explainer.pkl
    ├── json/
    │   ├── global_insights.json   ← AI-ENHANCED
    │   └── *.json                 ← AI-ENHANCED CASES
    └── images/
```

---

## ✅ Verification Checklist

After running:

- [ ] Dashboard opens at `http://localhost:8501`
- [ ] Hover over F1 Score shows tooltip
- [ ] Charts show English names (not `customer_activity`)
- [ ] Blue description boxes appear above charts
- [ ] Business insights are detailed and specific (not generic)
- [ ] What-If simulator updates probability in real-time
- [ ] SHAP plots display properly

---

## 🎯 For Judges

**Unique selling points:**

1. **Complete Explainability**
   - Global + Local + Counterfactual
   - SHAP waterfall + Feature importance + What-If

2. **AI-Powered Insights**
   - Gemini generates business insights
   - Adapts to YOUR specific data
   - Professional recommendations

3. **Production-Ready UX**
   - Tooltips for every metric
   - Business-friendly language
   - Interactive simulations

4. **Professional Design**
   - Schneider Electric branding
   - Smooth animations
   - Clean, modern interface

---

## 🚨 Troubleshooting

**"No module named 'google.generativeai'"**
- Run in Colab: `!pip install google-generativeai`

**"API key error"**
- En local, revisa el archivo `.env` (ya contiene la clave por defecto, cámbiala si hace falta)
- En Colab, define `os.environ["GEMINI_API_KEY"] = "tu_api_key"` antes de ejecutar
- Verifica tu clave en: https://aistudio.google.com/apikey

**"Dashboard shows technical names"**
- Make sure you're running `app_final.py` (not `app.py`)
- Clear cache: `streamlit cache clear`

**"Insights are still generic"**
- Re-ejecuta `colab_full_pipeline.py` con la API key definida
- Descarga de nuevo `output/`
- Comprueba que `global_insights.json` y los JSON individuales tengan campos `business_insights`/`recommendations`

---

## 📧 Summary

You have:
- ✅ English dashboard with tooltips
- ✅ Gemini AI integration (global + individual)
- ✅ Professional CSS and UX
- ✅ Business-friendly translations
- ✅ Complete explainability

**Next:** Ejecuta `colab_full_pipeline.py` → Descarga `output/` → Lanza el dashboard

---

**Ready to win! 🏆**
