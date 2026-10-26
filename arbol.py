def crear_nodo(estado, padre=None, operador=None, costo=0, h=None):
    nodo = {
        "estado": estado,
        "padre": padre,
        "operador": operador,
        "costo": costo,
        "h": h,
        "hijos": [],
        "orden": None,
        "nota": "",
        "profundidad": 0,
    }
    if padre is not None:
        nodo["profundidad"] = padre["profundidad"] + 1
        padre["hijos"].append(nodo)
    return nodo