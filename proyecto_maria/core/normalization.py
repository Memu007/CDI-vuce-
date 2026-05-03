def to_float_strict(val, default=0.0):
    try:
        s = str(val).strip().replace(' ', '')
        if s == '':
            return default
        if ',' in s and '.' in s:
            s = s.replace('.', '').replace(',', '.')
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s)
    except Exception:
        return default


def normalize_origin(value: str) -> str:
    try:
        s = str(value or '').strip().upper()
        return s[:3] if s else 'XX'
    except Exception:
        return 'XX'


