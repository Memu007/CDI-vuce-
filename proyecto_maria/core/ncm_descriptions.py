"""
Diccionario de descripciones NCM para auto-completar
Actualizado: 2025-10-02
Fuente: MERCOSUR, VUCE, experiencia
"""

# Top 50 NCMs más usados en importación/exportación
NCM_DESCRIPTIONS = {
    # Capítulo 73: Hierro y acero
    "73066100": "Tubo de hierro o acero",
    "73089010": "Estructura metálica",
    "73181500": "Tornillo de hierro o acero",
    "73269090": "Manufactura de hierro o acero",

    # Capítulo 84: Máquinas y aparatos mecánicos
    "84713010": "Computadora portátil",
    "84714100": "Computadora de escritorio",
    "84715000": "Unidad de procesamiento digital",
    "84733090": "Parte de máquina de procesamiento de datos",

    # Capítulo 85: Aparatos eléctricos y electrónicos
    "85287210": "Receptor de televisión",
    "85171200": "Teléfono móvil",
    "85176200": "Receptor para radiodifusión",
    "85182100": "Altavoz",
    "85258000": "Cámara de video",

    # Capítulo 39: Plásticos
    "39202010": "Lámina de polímero de propileno",
    "39269090": "Artículo de plástico",
    "39232100": "Bolsa de plástico",

    # Capítulo 40: Caucho
    "40111000": "Neumático nuevo para automóvil",
    "40169300": "Junta o empaquetadura de caucho",
    "40151900": "Guante de caucho",

    # Capítulo 87: Vehículos y partes
    "87089100": "Radiador para vehículo",
    "87081000": "Paragolpe para vehículo",
    "87087090": "Parte de vehículo",

    # Capítulo 94: Muebles
    "94036000": "Mueble de madera",
    "94018000": "Asiento",
    "94032000": "Mueble de metal",

    # Capítulo 70: Vidrio
    "70109010": "Envase de vidrio",
    "70132800": "Copa de vidrio",

    # Capítulo 61/62: Textil y prendas
    "61091000": "Camiseta de algodón",
    "62046200": "Pantalón de algodón para mujer",

    # Capítulo 64: Calzado
    "64029900": "Calzado",
    "64039900": "Calzado deportivo",

    # Capítulo 42: Cuero
    "42021200": "Bolso de mano con superficie exterior de plástico",
    "42023100": "Cartera para bolsillo",

    # Capítulo 90: Instrumentos de óptica y medida
    "90183100": "Jeringa",
    "90189090": "Instrumento médico",

    # Capítulo 95: Juguetes y artículos para deporte
    "95030090": "Juguete",
    "95062900": "Artículo para deporte",

    # NCMs de los ejemplos del usuario (de la imagen)
    "4559948": "Producto industrial",
    "4568452": "Producto industrial",
    "4568456": "Producto industrial",
}

# Descripciones genéricas por capítulo (fallback cuando NCM exacto no existe)
CHAPTER_DESCRIPTIONS = {
    "01": "Animal vivo",
    "02": "Carne y despojos comestibles",
    "03": "Pescado o crustáceo",
    "04": "Producto lácteo",
    "05": "Producto de origen animal",
    "06": "Planta viva",
    "07": "Hortaliza o legumbre",
    "08": "Fruta comestible",
    "09": "Café, té o especias",
    "10": "Cereal",
    "11": "Producto de la molinería",
    "12": "Semilla o fruto oleaginoso",
    "13": "Goma o resina",
    "14": "Materia trenzable",
    "15": "Grasa o aceite",
    "16": "Preparación de carne o pescado",
    "17": "Azúcar o artículo de confitería",
    "18": "Cacao y sus preparaciones",
    "19": "Preparación de cereales",
    "20": "Preparación de hortalizas o frutas",
    "21": "Preparación alimenticia diversa",
    "22": "Bebida",
    "23": "Residuo de industria alimentaria",
    "24": "Tabaco y sucedáneos",
    "25": "Producto mineral",
    "26": "Mineral metalífero",
    "27": "Combustible mineral",
    "28": "Producto químico inorgánico",
    "29": "Producto químico orgánico",
    "30": "Producto farmacéutico",
    "31": "Abono",
    "32": "Extracto curtiente o tintóreo",
    "33": "Aceite esencial o perfume",
    "34": "Jabón o preparación de limpieza",
    "35": "Materia albuminoidea",
    "36": "Pólvora y explosivos",
    "37": "Producto fotográfico o cinematográfico",
    "38": "Producto químico diverso",
    "39": "Plástico y sus manufacturas",
    "40": "Caucho y sus manufacturas",
    "41": "Pieles y cueros",
    "42": "Artículo de cuero",
    "43": "Peletería",
    "44": "Madera y sus manufacturas",
    "45": "Corcho y sus manufacturas",
    "46": "Manufactura de espartería",
    "47": "Pasta de madera",
    "48": "Papel o cartón",
    "49": "Libro o impreso",
    "50": "Seda",
    "51": "Lana o pelo fino",
    "52": "Algodón",
    "53": "Fibra textil vegetal",
    "54": "Filamento sintético o artificial",
    "55": "Fibra sintética o artificial",
    "56": "Guata y fieltro",
    "57": "Alfombra",
    "58": "Tejido especial",
    "59": "Tejido impregnado o recubierto",
    "60": "Tejido de punto",
    "61": "Prenda de vestir de punto",
    "62": "Prenda de vestir",
    "63": "Artículo textil confeccionado",
    "64": "Calzado",
    "65": "Sombrero",
    "66": "Paraguas y bastón",
    "67": "Pluma preparada",
    "68": "Manufactura de piedra o cemento",
    "69": "Producto cerámico",
    "70": "Vidrio y sus manufacturas",
    "71": "Piedra preciosa o metal precioso",
    "72": "Fundición, hierro o acero",
    "73": "Manufactura de hierro o acero",
    "74": "Cobre y sus manufacturas",
    "75": "Níquel y sus manufacturas",
    "76": "Aluminio y sus manufacturas",
    "78": "Plomo y sus manufacturas",
    "79": "Cinc y sus manufacturas",
    "80": "Estaño y sus manufacturas",
    "81": "Metal común diverso",
    "82": "Herramienta de metal",
    "83": "Manufactura diversa de metal",
    "84": "Máquina o aparato mecánico",
    "85": "Aparato eléctrico o electrónico",
    "86": "Vehículo y material ferroviario",
    "87": "Vehículo automóvil o parte",
    "88": "Aeronave y aparato espacial",
    "89": "Barco y estructura flotante",
    "90": "Instrumento de óptica o medida",
    "91": "Relojería",
    "92": "Instrumento musical",
    "93": "Arma y munición",
    "94": "Mueble",
    "95": "Juguete o artículo para deporte",
    "96": "Manufactura diversa",
    "97": "Objeto de arte o antigüedad",
}


def get_ncm_description(ncm: str) -> dict:
    """
    Obtiene descripción del NCM desde múltiples fuentes

    Prioridad de fuentes:
    1. Diccionario exacto (NCM completo)
    2. Descripción por capítulo (2 primeros dígitos)
    3. Descripción genérica (fallback)

    Args:
        ncm: Código NCM (6-8 dígitos)

    Returns:
        dict con keys:
            - ncm: NCM limpio
            - descripcion: Descripción del producto
            - fuente: "dict" | "chapter" | "generic"

    Examples:
        >>> get_ncm_description("73066100")
        {'ncm': '73066100', 'descripcion': 'Tubo de hierro o acero', 'fuente': 'dict'}

        >>> get_ncm_description("73999999")
        {'ncm': '73999999', 'descripcion': 'Manufactura de hierro o acero', 'fuente': 'chapter'}

        >>> get_ncm_description("99999999")
        {'ncm': '99999999', 'descripcion': 'Producto NCM 99999999', 'fuente': 'generic'}
    """
    # Limpiar y normalizar NCM
    ncm_clean = str(ncm).strip()[:8]

    # Fuente 1: Diccionario exacto (más específico)
    if ncm_clean in NCM_DESCRIPTIONS:
        return {
            "ncm": ncm_clean,
            "descripcion": NCM_DESCRIPTIONS[ncm_clean],
            "fuente": "dict"
        }

    # Fuente 2: Por capítulo (2 primeros dígitos)
    chapter = ncm_clean[:2]
    if chapter in CHAPTER_DESCRIPTIONS:
        return {
            "ncm": ncm_clean,
            "descripcion": CHAPTER_DESCRIPTIONS[chapter],
            "fuente": "chapter"
        }

    # Fuente 3: Genérico (siempre funciona)
    return {
        "ncm": ncm_clean,
        "descripcion": f"Producto NCM {ncm_clean}",
        "fuente": "generic"
    }
