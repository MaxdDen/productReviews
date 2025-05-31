
def to_int_or_none(value):
    # Если None — сразу вернуть None
    if value is None:
        return None
    # Если число — вернуть как int
    if isinstance(value, int):
        return value
    # Если строка — убрать пробелы и проверить пустоту
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return int(value)
    # Любой другой тип — попробовать привести к int (например, float)
    try:
        return int(value)
    except Exception:
        return None

def parse_int(val):
    if val in ("", None, "null"):
        return None
    try:
        return int(val)
    except Exception:
        return None  # или raise, если хочешь ловить баги данных

def parse_float(val):
    if val in ("", None, "null"):
        return None
    try:
        return float(val)
    except Exception:
        return None  # или raise, если хочешь ловить баги данных
    
def parse_str(val):
    if val is None:
        return ""
    return str(val)

def prettify_pydantic_error(err, row, row_num):
    loc = " → ".join(str(x) for x in err['loc'])
    msg = err['msg']
    typ = err['type']
    # Попробуем получить значение из строки по ключу поля, если поле только 1 уровня:
    if isinstance(err['loc'], (list, tuple)) and len(err['loc']) == 1:
        value = row.get(err['loc'][0], "")
    else:
        value = ""
    fix_hint = ""
    if typ == "int_parsing":
        fix_hint = "Ожидалось целое число, например: 1, 2, 3"
    elif typ == "float_parsing":
        fix_hint = "Ожидалось дробное число, например: 4.5 или 4,5"
    elif typ == "missing":
        fix_hint = "Поле обязательно, нельзя пропускать"
    print(f"Строка #{row_num}: поле '{loc}' — {msg}. {fix_hint}. В файле: «{value}»")

    return f"Строка #{row_num}: поле '{loc}' — {msg}. {fix_hint}. В файле: «{value}»"
