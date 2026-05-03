#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/Emi/CDI')

from dotenv import load_dotenv
load_dotenv('/Users/Emi/CDI/.env')

from proyecto_maria.routers.pdf_router import _fallback_extraction

# Test with Brazilian invoice (with NCM)
brazil_text = """FATURA
Nro: 61
Data: 10/11/2025

Item  Produto                               NCM        Quant  Preço Unit    Total
1     Parafuso Sextavado                    73181500   1000   0.50         500.00
2     Porca Rosa                           73181600   2000   0.25         500.00
3     Arruela de Pressão                   73182200   5000   0.10         500.00
"""

print("=== Testing Brazilian Invoice ===")
print("Text:", brazil_text[:300] + "...")

items = _fallback_extraction(brazil_text)
print(f"\n✅ Items extracted: {len(items)}")
for i, item in enumerate(items, 1):
    print(f"\nItem {i}:")
    for k, v in item.items():
        if v not in [0.0, '', 0]:
            print(f"  {k}: {v}")

# Test the quantity extraction specifically
print("\n\n=== Testing Quantity Extraction ===")
line = "1     Parafuso Sextavado                    73181500   1000   0.50         500.00"
print(f"Line: {line}")
import re
nums = re.findall(r'\d+[\.,]\d+|\d+', line)
print(f"Numbers: {nums}")

all_nums = []
for num in nums:
    num = num.replace(',', '')
    try:
        val = float(num)
        all_nums.append(val)
    except:
        pass

print(f"All numbers: {all_nums}")

# Filter NCM
valid_nums = []
for i, num in enumerate(all_nums):
    str_num = nums[i]
    if len(str_num.replace('.', '').replace(',', '')) >= 6 and '.' not in str_num and num > 10000:
        print(f"Skipping NCM: {str_num}")
        continue
    valid_nums.append(num)

print(f"Valid numbers: {valid_nums}")