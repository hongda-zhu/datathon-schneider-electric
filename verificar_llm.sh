#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         VERIFICACIÓN LLM - SCHNEIDER ELECTRIC DATATHON         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Conteo
echo "📊 1. ESTADÍSTICAS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
total_jsons=$(ls output/json/*.json 2>/dev/null | grep -v global | wc -l | tr -d ' ')
ai_jsons=$(grep -l "ai_generated" output/json/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "  Total de casos:           $total_jsons"
echo "  Con recomendaciones AI:   $ai_jsons"
echo "  Sin AI (reglas simples):  $((total_jsons - ai_jsons))"
echo ""

# 2. Global insights
echo "📋 2. GLOBAL INSIGHTS (Generados por LLM)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
import json
with open('output/json/global_insights.json') as f:
    data = json.load(f)
print('  ✅ Business Insights:')
for i, insight in enumerate(data['business_insights'][:2], 1):
    print(f'     {i}. {insight[:80]}...')
print()
print('  ✅ Recommendations:')
for i, rec in enumerate(data['recommendations'][:2], 1):
    print(f'     {i}. {rec[:80]}...')
"
echo ""

# 3. Comparación: CON AI vs SIN AI
echo "🔍 3. COMPARACIÓN: RECOMENDACIONES CON vs SIN AI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Caso CON AI
ai_file=$(grep -l "ai_generated" output/json/*.json 2>/dev/null | head -1)
if [ -n "$ai_file" ]; then
    echo "  ✅ CON AI - $(basename $ai_file)"
    python3 -c "
import json
with open('$ai_file') as f:
    data = json.load(f)
print(f\"     Opp ID:       {data['opportunity_id']}\")
print(f\"     Win Prob:     {data['prediction']['win_probability']:.1%}\")
print(f\"     Prediction:   {data['prediction']['predicted_outcome']}\")
print(f\"     AI Generated: {data['business_recommendation'].get('ai_generated', False)}\")
print()
print('     Next Steps (basadas en SHAP):')
for i, step in enumerate(data['business_recommendation']['next_steps'], 1):
    print(f'       {i}. {step[:70]}...')
"
fi

echo ""

# Caso SIN AI
no_ai_file=$(grep -L "ai_generated" output/json/*.json 2>/dev/null | head -1)
if [ -n "$no_ai_file" ]; then
    echo "  ⚠️  SIN AI - $(basename $no_ai_file) (reglas simples)"
    python3 -c "
import json
with open('$no_ai_file') as f:
    data = json.load(f)
print(f\"     Opp ID:       {data['opportunity_id']}\")
print(f\"     Win Prob:     {data['prediction']['win_probability']:.1%}\")
print(f\"     Prediction:   {data['prediction']['predicted_outcome']}\")
print(f\"     AI Generated: {data['business_recommendation'].get('ai_generated', False)}\")
print()
print('     Next Steps (reglas if/else):')
for i, step in enumerate(data['business_recommendation']['next_steps'], 1):
    print(f'       {i}. {step}')
"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                         DIFERENCIAS CLAVE                       ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  SIN AI: Frases genéricas (ej: 'Leverage existing engagement') ║"
echo "║  CON AI: Referencias SHAP específicas (ej: 'Address -0.73      ║"
echo "║          impact of customer_activity by scheduling meeting')    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
