"""
Procesador de PDFs para extraer datos de facturas y convertir a formato AVG
"""

import pdfplumber
import re
from typing import List, Dict, Any
from models.operations import Item

def extract_data_from_pdf(pdf_path: str) -> List[Item]:
    """
    Extrae datos de un PDF de factura e intenta convertirlos a Items.
    
    Esta es una implementación simple que busca patrones comunes en facturas.
    """
    items = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            
            # Extraer texto de todas las páginas
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            
            print(f"📄 Texto extraído del PDF (primeros 500 chars):")
            print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
            
            # Intentar extraer datos usando patrones comunes
            items = extract_items_from_text(full_text)
            
    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")
        
    return items

def extract_items_from_text(text: str) -> List[Item]:
    """
    Extrae items del texto usando patrones de regex y heurísticas.
    """
    items = []
    
    # Limpiar el texto
    text = text.replace('\n', ' ').replace('\t', ' ')
    
    # Patrones comunes para extraer datos
    patterns = {
        # Códigos NCM/HS (6-8 dígitos)
        'ncm': r'\b\d{6,8}\b',
        
        # Cantidades (número seguido de unidades)
        'quantity': r'(\d+(?:\.\d+)?)\s*(?:pcs|piezas|units|unidades|each|ea|qty)',
        
        # Precios (número con decimales, posiblemente con símbolo de moneda)
        'price': r'(?:USD|US\$|\$|€|EUR)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        
        # Pesos (número seguido de kg, g, lb)
        'weight': r'(\d+(?:\.\d+)?)\s*(?:kg|kilogram|g|gram|lb|pound)',
        
        # Descripciones (texto entre comillas o después de description)
        'description': r'(?:description|desc|producto|product)[:\s]+([A-Za-z\s]+?)(?:\s+\d|\s*$)',
    }
    
    # Buscar patrones en el texto
    found_data = {}
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_data[key] = matches
    
    print(f"🔍 Datos encontrados en PDF:")
    for key, values in found_data.items():
        print(f"   {key}: {values[:3]}{'...' if len(values) > 3 else ''}")
    
    # Intentar crear items con los datos encontrados
    if found_data.get('ncm') and found_data.get('description'):
        # Crear un item de ejemplo con los datos encontrados
        try:
            item = Item(
                pieza=found_data['ncm'][0] if found_data['ncm'] else "00000000",
                descripcion=found_data['description'][0] if found_data['description'] else "Producto extraído de PDF",
                origen="XX",  # Por defecto, se puede mejorar
                peso_unitario=float(found_data['weight'][0]) if found_data.get('weight') else 1.0,
                cantidad=float(found_data['quantity'][0]) if found_data.get('quantity') else 1.0,
                valor_unitario=float(found_data['price'][0].replace(',', '')) if found_data.get('price') else 100.0
            )
            items.append(item)
            print(f"✅ Item creado: {item.pieza} - {item.descripcion}")
            
        except Exception as e:
            print(f"⚠️  Error creando item: {e}")
    
    # Si no se pudo extraer automáticamente, crear item de ejemplo
    if not items:
        print("⚠️  No se pudieron extraer datos automáticamente")
        print("📝 Creando item de ejemplo basado en el PDF...")
        
        # Buscar cualquier número que pueda ser NCM
        numbers = re.findall(r'\b\d{6,8}\b', text)
        ncm = numbers[0] if numbers else "84713010"
        
        # Buscar cualquier texto que pueda ser descripción
        words = text.split()
        description = " ".join(words[:5]) if len(words) >= 5 else "Producto extraído de PDF"
        
        item = Item(
            pieza=ncm,
            descripcion=description[:50],  # Limitar longitud
            origen="XX",
            peso_unitario=1.0,
            cantidad=1.0,
            valor_unitario=100.0
        )
        items.append(item)
        print(f"📝 Item de ejemplo creado: {item.pieza} - {item.descripcion}")
    
    return items

def analyze_pdf_structure(pdf_path: str) -> Dict[str, Any]:
    """
    Analiza la estructura del PDF para entender mejor su contenido.
    """
    info = {
        'pages': 0,
        'tables': 0,
        'text_length': 0,
        'contains_numbers': False,
        'contains_currency': False,
        'sample_text': ''
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            info['pages'] = len(pdf.pages)
            
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    info['text_length'] += len(text)
                    info['sample_text'] += text[:200]
                    
                    # Buscar patrones
                    if re.search(r'\d{6,8}', text):
                        info['contains_numbers'] = True
                    if re.search(r'[$€£¥]|\bUSD\b|\bEUR\b', text):
                        info['contains_currency'] = True
                
                # Buscar tablas
                tables = page.extract_tables()
                if tables:
                    info['tables'] += len(tables)
    
    except Exception as e:
        print(f"Error analizando PDF: {e}")
    
    return info

