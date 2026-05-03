#!/usr/bin/env python3
"""
Test Gemini PDF extraction with multiple invoice types
NOTE: This is a manual test script, not a pytest test.
Run directly: python test_gemini_extraction.py <pdf_path>
"""
import pytest
pytestmark = pytest.mark.skip(reason="Manual test script - run directly with python, not pytest")

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

os.environ['GEMINI_API_KEY'] = 'AIzaSyBi-JgR5zF2J1xpC9_PuNGT0dgg7_2E1rI'
os.environ['GEMINI_MODEL'] = 'gemini-2.0-flash'
os.environ['ENABLE_PDF_LLM_FALLBACK'] = 'true'

from proyecto_maria.pdf_extractor import _llm_extract_pdf_items
import pdfplumber

def extract_pdf_text(pdf_path):
    """Extract text from PDF"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        return ""

def test_extraction(pdf_path):
    """Test extraction on a single PDF"""
    print(f"\n{'='*70}")
    print(f"📄 Testing: {Path(pdf_path).name}")
    print(f"{'='*70}")
    
    # Extract text
    text = extract_pdf_text(pdf_path)
    if not text:
        print("❌ No text extracted from PDF")
        return None
    
    print(f"📝 Extracted {len(text)} characters of text")
    
    # Extract items with Gemini
    print("🤖 Extracting with Gemini 2.0 Flash...")
    items = _llm_extract_pdf_items(text)
    
    if not items:
        print("❌ No items extracted")
        return None
    
    print(f"✅ Extracted {len(items)} items\n")
    
    # Show results
    for i, item in enumerate(items, 1):
        print(f"Item {i}:")
        print(f"  NCM/Pieza: {item.get('pieza', 'N/A')}")
        print(f"  Descripción: {item.get('descripcion', 'N/A')[:60]}")
        print(f"  Versión: {item.get('version', 'N/A')[:60] if item.get('version') else 'N/A'}")
        print(f"  Cantidad: {item.get('cantidad', 'N/A')}")
        print(f"  Precio Unit: {item.get('valor_unitario', 'N/A')}")
        print(f"  Origen: {item.get('origen', 'N/A')}")
        print()
    
    # Validate quality
    issues = []
    for i, item in enumerate(items, 1):
        desc = str(item.get('descripcion', ''))
        if 'sugerencia' in desc.lower():
            issues.append(f"Item {i}: Descripción contiene 'Sugerencias'")
        if not desc or len(desc) < 3:
            issues.append(f"Item {i}: Descripción muy corta o vacía")
        if item.get('cantidad', 0) == 0:
            issues.append(f"Item {i}: Cantidad es 0")
        if item.get('valor_unitario', 0) == 0:
            issues.append(f"Item {i}: Precio unitario es 0")
    
    if issues:
        print("⚠️  Issues encontrados:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Todos los items pasaron validación de calidad")
    
    return items

def main():
    """Main test function"""
    print("🧪 TEST DE EXTRACCIÓN GEMINI 2.0 FLASH")
    print("="*70)
    
    # Sample PDFs to test
    sample_dir = Path("/Users/Emi/CDI/samples/ejemplos")
    test_files = [
        "FAC 61 VERNOL.pdf",  # Brasil
        "Invoice_1680_from_Synergy_Global_Trading_LLC - intercambiador de calor - OK.pdf",  # USA
        "FC_2025-837 SHELL 3299.pdf",  # Shell
    ]
    
    results = {}
    
    for filename in test_files:
        pdf_path = sample_dir / filename
        if pdf_path.exists():
            try:
                items = test_extraction(str(pdf_path))
                results[filename] = {
                    'success': items is not None,
                    'item_count': len(items) if items else 0
                }
            except Exception as e:
                print(f"❌ Error procesando {filename}: {e}")
                results[filename] = {'success': False, 'error': str(e)}
        else:
            print(f"⚠️  Archivo no encontrado: {filename}")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 RESUMEN")
    print(f"{'='*70}")
    
    successful = sum(1 for r in results.values() if r.get('success'))
    total = len(results)
    
    print(f"\n✅ Exitosos: {successful}/{total}")
    
    for filename, result in results.items():
        status = "✅" if result.get('success') else "❌"
        count = result.get('item_count', 0)
        print(f"{status} {filename}: {count} items")
    
    return successful == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

