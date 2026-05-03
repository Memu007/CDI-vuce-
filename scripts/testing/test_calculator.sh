#!/bin/bash
# Script de prueba para la Calculadora de Valor en Plaza
# Ejecutar: bash test_calculator.sh

echo "🧮 PROBANDO CALCULADORA DE VALOR EN PLAZA"
echo "=========================================="
echo ""

# URL base del servidor
BASE_URL="http://localhost:8001"

echo "1️⃣ Probando cálculo simple: Laptop desde China"
echo "--------------------------------------------------"
curl -X POST "$BASE_URL/api/calculator/valor-plaza" \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "origen": "CN",
    "fob_unitario": 500,
    "cantidad": 10
  }' | python3 -m json.tool

echo ""
echo ""
echo "2️⃣ Probando cálculo MERCOSUR: Laptop desde Brasil"
echo "--------------------------------------------------"
curl -X POST "$BASE_URL/api/calculator/valor-plaza" \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "origen": "BR",
    "fob_unitario": 500,
    "cantidad": 10
  }' | python3 -m json.tool

echo ""
echo ""
echo "3️⃣ Comparando orígenes: ¿De dónde conviene importar?"
echo "--------------------------------------------------"
curl -X POST "$BASE_URL/api/calculator/comparar-origenes" \
  -H "Content-Type: application/json" \
  -d '{
    "ncm": "84713010",
    "fob_unitario": 500,
    "cantidad": 10
  }' | python3 -m json.tool

echo ""
echo ""
echo "4️⃣ Probando ejemplo pre-configurado: Celular Vietnam"
echo "--------------------------------------------------"
curl -X GET "$BASE_URL/api/calculator/test/celular_vietnam" | python3 -m json.tool

echo ""
echo ""
echo "5️⃣ Obteniendo info de MERCOSUR"
echo "--------------------------------------------------"
curl -X GET "$BASE_URL/api/calculator/mercosur-info" | python3 -m json.tool

echo ""
echo ""
echo "✅ TESTS COMPLETADOS"
echo "=========================================="
