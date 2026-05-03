#!/usr/bin/env python3
"""
Simple test de Gemini extraction
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

os.environ['GEMINI_API_KEY'] = 'AIzaSyBi-JgR5zF2J1xpC9_PuNGT0dgg7_2E1rI'
os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash'
os.environ['ENABLE_PDF_LLM_FALLBACK'] = 'true'

from proyecto_maria.pdf_extractor import _llm_extract_pdf_items

# Texto de prueba simple
test_text = """
COMMERCIAL INVOICE
Invoice No: 12345
Date: 2025-01-15

Item  Description                NCM        Qty    Unit Price    Total
1     Laptop Computer Dell      84713010    5      800.00       4000.00
2     Wireless Mouse Logitech   84716070    20     25.00        500.00  
3     USB Keyboard HP           84716060    10     35.00        350.00
"""

print("🧪 Test Simple de Gemini 2.0 Flash")
print("="*60)
print("\n📝 Texto de entrada:")
print(test_text)
print("\n🤖 Extrayendo con Gemini...")

try:
    items = _llm_extract_pdf_items(test_text)
    
    if items:
        print(f"\n✅ Extraídos {len(items)} items!\n")
        for i, item in enumerate(items, 1):
            print(f"Item {i}:")
            print(f"  NCM: {item.get('pieza', 'N/A')}")
            print(f"  Descripción: {item.get('descripcion', 'N/A')}")
            print(f"  Cantidad: {item.get('cantidad', 'N/A')}")
            print(f"  Precio: {item.get('valor_unitario', 'N/A')}")
            print()
        print("✅ Gemini funcionando correctamente!")
    else:
        print("❌ No se extrajeron items")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

