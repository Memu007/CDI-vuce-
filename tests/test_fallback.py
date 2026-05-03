#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/Emi/CDI')

from dotenv import load_dotenv
load_dotenv('/Users/Emi/CDI/.env')

from proyecto_maria.routers.pdf_router import _fallback_extraction

# Test with Synergy text
synergy_text = """COMMERCIAL INVOICE
Invoice No: 1680
Date: 2025-01-15

Item  Description                NCM        Qty    Unit Price    Total
1     Plate Heat Exchanger      84195000    2      689.00       1378.00
2     Plate Heat Exchanger      84195000    2      3950.00      7900.00
3     SPARE PART KITS           84199000    248    2.66         659.68
"""

print("=== Testing Enhanced Fallback ===")
print("Text:", synergy_text[:200] + "...")

items = _fallback_extraction(synergy_text)
print(f"\n✅ Items extracted: {len(items)}")
for i, item in enumerate(items, 1):
    print(f"\nItem {i}:")
    for k, v in item.items():
        if v not in [0.0, '', 0]:
            print(f"  {k}: {v}")