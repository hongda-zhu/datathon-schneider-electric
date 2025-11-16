# 📋 ¿Por qué no hay Opportunity IDs 1, 2, 3, 4?

## 📊 Resumen

Los IDs 1, 2, 3, 4 **SÍ existen en el dataset original**, pero están en el **training set**, no en el **test set** que usa el dashboard.

---

## 🔍 Explicación Detallada

### Dataset Original (Completo)
```
Total de oportunidades: 35,899
IDs disponibles: 1 a 35,899 (consecutivos)
```

### División Train/Test (80/20)
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```

**Resultado:**
- **Train set (80%)**: ~28,719 oportunidades
- **Test set (20%)**: ~7,180 oportunidades

### ¿Qué IDs quedaron en cada conjunto?

**Train set (NO visible en dashboard):**
- Incluye IDs: 1, 2, 3, 4, 6, 7, 8, ... (la mayoría)

**Test set (SÍ visible en dashboard):**
- IDs disponibles: 5, 20, 23, 26, 33, 35, 42, ...
- Rango: **5 a 35,898**
- Total: **7,180 IDs** (no consecutivos)

---

## 🎯 ¿Por qué no son consecutivos?

La función `train_test_split()` con `random_state=42`:
1. Mezcla aleatoriamente los 35,899 IDs
2. Asigna 80% al train set, 20% al test set
3. Los IDs no quedan ordenados consecutivamente en cada conjunto

**Ejemplo:**
```
Dataset completo: [1, 2, 3, 4, 5, 6, 7, 8, ...]

Después del split:
  Train: [1, 2, 3, 4, 6, 7, 9, 10, ...]  ← 80%
  Test:  [5, 8, 11, 14, 17, 20, ...]     ← 20%
```

---

## 💡 IDs Recomendados para Probar

### Casos de ejemplo con JSONs completos:

| ID | Win Prob | Tipo | Descripción |
|-----|----------|------|-------------|
| **102** | 99.1% | Win | Alta confianza, sin competencia |
| **3414** | 13.5% | Loss | Baja engagement, necesita intervención |
| **12121** | 1.9% | Loss | Oportunidad muy vieja (outlier) |
| **13701** | 78.6% | Win | Caso con recomendaciones AI |
| **14992** | 97.5% | Win | High hitrate, quality score alto |

---

## 📂 Archivos Generados

### JSONs individuales
```bash
ls output/json/*.json | wc -l
# Output: 301 archivos (300 casos + global_insights.json)
```

Solo los **primeros 300 IDs del test set** tienen JSONs con análisis completo:
- `output/json/102.json` ✅
- `output/json/3414.json` ✅
- `output/json/12121.json` ✅
- ...hasta 300 casos

### Todos los 7,180 casos del test set
Tienen predicciones disponibles en:
- `output/X_test.pkl` ← Features
- `output/y_test.pkl` ← Target real
- `output/shap_values.pkl` ← SHAP values

---

## 🚀 Cómo Ver los IDs Disponibles

### En el Dashboard:
```bash
streamlit run app_final.py
```

1. Ve a **Case Explorer**
2. Verás un mensaje azul explicando los IDs disponibles
3. El selector muestra los 7,180 IDs ordenados
4. Selector por defecto abre en ID **102** (caso interesante)

### En Python:
```python
import joblib

X_test = joblib.load("output/X_test.pkl")
available_ids = sorted(X_test.index.tolist())

print(f"Total IDs: {len(available_ids)}")
print(f"Primer ID: {available_ids[0]}")
print(f"Último ID: {available_ids[-1]}")
print(f"Primeros 10: {available_ids[:10]}")
```

Output:
```
Total IDs: 7180
Primer ID: 5
Último ID: 35898
Primeros 10: [5, 20, 23, 26, 33, 35, 42, 43, 44, 56]
```

---

## ✅ Conclusión

**No es un error**: Los IDs 1-4 están en el training set por diseño del split aleatorio.

El dashboard muestra **7,180 oportunidades reales del test set** con IDs del sistema de Schneider Electric (no son IDs ficticios o consecutivos).
