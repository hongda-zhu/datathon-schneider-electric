# 🔍 Verificación del LLM - Schneider Electric Datathon

## ✅ Comprobación Visual

### 1️⃣ **Ejecutar el dashboard**
```bash
streamlit run app_final.py
```

### 2️⃣ **Navegar a "Case Explorer"**
- Selecciona una oportunidad **CON AI** (ej: 3414, 13701, 14992, 16232)
- Scroll hasta **"Recommended Action"**
- Verás recomendaciones específicas que mencionan:
  - Valores SHAP exactos (ej: "-0.73 impact")
  - Features específicas (ej: "customer_activity", "cust_interactions")
  - Acciones concretas basadas en esos valores

### 3️⃣ **Comparar con caso SIN AI**
- Selecciona oportunidad **SIN AI** (ej: 102, 10305, 10593)
- Las recomendaciones serán genéricas:
  - "Leverage existing engagement"
  - "Maintain momentum with key stakeholders"
  - "Capitalize on the lack of competition"

---

## 📊 Comprobación por Línea de Comandos

### Opción 1: Script de verificación
```bash
./verificar_llm.sh
```

### Opción 2: Comandos individuales

**Ver estadísticas:**
```bash
echo "Total casos: $(ls output/json/*.json | grep -v global | wc -l)"
echo "Con AI: $(grep -l 'ai_generated' output/json/*.json | wc -l)"
```

**Ver caso CON AI:**
```bash
cat output/json/3414.json | jq '.business_recommendation'
```

**Ver caso SIN AI:**
```bash
cat output/json/102.json | jq '.business_recommendation'
```

**Ver insights globales:**
```bash
cat output/json/global_insights.json | jq '.business_insights'
```

---

## 🔬 Diferencias Clave

| Característica | SIN AI (Reglas) | CON AI (Gemini 2.0-Flash) |
|----------------|-----------------|---------------------------|
| **Tipo** | If/else hardcoded | Generadas por LLM |
| **Contexto** | Genérico | Basado en SHAP values |
| **Ejemplo** | "Leverage existing engagement" | "Increase customer activity by scheduling a meeting to address the -0.73 impact of 'customer_activity'" |
| **Referencia SHAP** | ❌ No | ✅ Sí (valores exactos) |
| **Personalización** | Baja | Alta |
| **Campo en JSON** | `"ai_generated": false` (o ausente) | `"ai_generated": true` |

---

## 📋 Resumen de Resultados

- **Total de casos analizados:** 300
- **Con recomendaciones AI:** 15 (5%)
- **Sin AI (reglas simples):** 285 (95%)

**Nota:** Solo se generaron 15 casos con AI debido a:
1. Límites de cuota de la API de Gemini (15 requests/min en tier gratuito)
2. El script genera AI solo para casos de muestra (5 + 5 + 5)

---

## 🎯 Evidencia del Deliverable

**Requisito:** "Use a Large Language Model (LLM) to help summarize and interpret SHAP/other explainability outputs automatically"

✅ **Cumplido:**
- LLM configurado: Gemini 2.0-Flash
- Insights globales generados automáticamente
- Recomendaciones por caso basadas en SHAP values
- Output human-readable ("non-technical person should understand")

**Ejemplo real:**

```json
{
  "opportunity_id": "3414",
  "win_probability": 0.135,
  "next_steps": [
    "Increase customer activity by scheduling a meeting to understand their
     current challenges and future needs, directly addressing the -0.73
     impact of 'customer_activity'.",

    "Improve customer interactions by proactively sharing relevant case
     studies and technical resources to address concerns indicated by the
     -0.34 impact of 'cust_interactions'."
  ],
  "ai_generated": true
}
```

El LLM **automáticamente** convierte:
- SHAP value: `-0.73` → Acción: "schedule a meeting"
- Feature: `customer_activity` → Business language: "understand challenges"
- Contexto técnico → Recomendación ejecutable
