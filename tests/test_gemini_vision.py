#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '/Users/Emi/CDI')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/Users/Emi/CDI/.env')

print(f"API Key loaded: {'YES' if os.getenv('GEMINI_API_KEY') else 'NO'}")

from proyecto_maria.pdf_extractor import robust_extract_pdf_items

# Test file
pdf_path = '/Users/Emi/CDI/samples/ejemplos/FAC 61 VERNOL.pdf'

print('=== Test Gemini Vision API ===')
print(f'Archivo: {pdf_path}')

try:
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    print(f'Tamaño: {len(data) / 1024:.1f} KB')
    
    items = robust_extract_pdf_items(data)
    
    print(f'\n✅ Items extraídos: {len(items)}')
    
    for i, item in enumerate(items[:5], 1):
        print(f'\nItem {i}:')
        for k, v in item.items():
            if v not in [0.0, '', 0]:
                print(f'  {k}: {v}')
                
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()