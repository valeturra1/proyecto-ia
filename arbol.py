import sys


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


def describir_estado(estado):
    fila, columna, fertilizante, cultivos_secos, combustible, avioneta_usada = estado
    texto = ("(" + str(fila) + "," + str(columna) + ") fert=" + str(fertilizante)
             + " secos=" + str(len(cultivos_secos)) + " comb=" + str(combustible))
    if avioneta_usada:
        texto += " avioneta-usada"
    return texto


def describir_nodo(nodo, en_camino, marca):
    if nodo["orden"] is None:
        etiqueta = "[-]"
    else:
        etiqueta = "[" + str(nodo["orden"]) + "]"
    if nodo["operador"] is None:
        operador = "INICIO"
    else:
        operador = nodo["operador"]
    texto = (etiqueta + " " + operador + " " + describir_estado(nodo["estado"])
             + " g=" + str(nodo["costo"]))
    if nodo["h"] is not None:
        texto += " h=" + str(nodo["h"]) + " f=" + str(nodo["costo"] + nodo["h"])
    if nodo["nota"] != "":
        texto += " (" + nodo["nota"] + ")"
    if id(nodo) in en_camino:
        texto += marca
    return texto


def ids_del_camino(meta):
    ids = set()
    nodo = meta
    while nodo is not None:
        ids.add(id(nodo))
        nodo = nodo["padre"]
    return ids


def lineas_del_arbol(raiz, meta=None, max_profundidad=None, max_nodos=None,
                     solo_expandidos=False, solo_ascii=False):
    if solo_ascii:
        t_medio, t_final, t_barra, t_vacio = "|-- ", "`-- ", "|   ", "    "
        marca = " <== SOLUCION"
    else:
        t_medio, t_final, t_barra, t_vacio = "├── ", "└── ", "│   ", "    "
        marca = " ★"

    en_camino = ids_del_camino(meta)
    lineas = ["[n] = orden de expansión, [-] = generado y no expandido, "
              "g = costo acumulado, h = heurística, f = g + h"]
    if meta is not None:
        lineas.append(marca.strip() + " = camino hasta la solución")
    lineas.append("")

    pila = [(raiz, "", "")]
    impresos = 0
    while pila:
        nodo, prefijo_linea, prefijo_hijos = pila.pop()
        if max_nodos is not None and impresos >= max_nodos:
            lineas.append("... (se cortó la impresión en " + str(max_nodos) + " nodos)")
            break
        lineas.append(prefijo_linea + describir_nodo(nodo, en_camino, marca))
        impresos += 1

        hijos = nodo["hijos"]
        if solo_expandidos:
            hijos = [hijo for hijo in hijos if hijo["orden"] is not None]
        if len(hijos) == 0:
            continue
        if max_profundidad is not None and nodo["profundidad"] >= max_profundidad:
            lineas.append(prefijo_hijos + t_final + "... (" + str(len(hijos)) + " hijos ocultos)")
            continue

        for k in range(len(hijos) - 1, -1, -1):
            es_ultimo = k == len(hijos) - 1
            if es_ultimo:
                nuevo_prefijo_linea = prefijo_hijos + t_final
                nuevo_prefijo_hijos = prefijo_hijos + t_vacio
            else:
                nuevo_prefijo_linea = prefijo_hijos + t_medio
                nuevo_prefijo_hijos = prefijo_hijos + t_barra
            pila.append((hijos[k], nuevo_prefijo_linea, nuevo_prefijo_hijos))
    return lineas


def imprimir_arbol(raiz, meta=None, **opciones):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass
    for linea in lineas_del_arbol(raiz, meta, **opciones):
        print(linea)


def guardar_arbol(raiz, ruta, meta=None, **opciones):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for linea in lineas_del_arbol(raiz, meta, **opciones):
            archivo.write(linea + "\n")