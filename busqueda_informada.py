from time import perf_counter

from estado import (
    estado_inicial,
    es_meta,
    movimientos_y_efectos
)
from arbol import crear_nodo

def heuristica(estado):
    fila, columna, fertilizante, cultivos_secos, combustible, avioneta_usada = estado

    if len(cultivos_secos) == 0:
        return 0

    distancias = []

    for cultivo in cultivos_secos:
        fila_cultivo, columna_cultivo = cultivo

        distancia = (
            abs(fila - fila_cultivo)
            + abs(columna - columna_cultivo)
        )

        distancias.append(distancia)

    return 0.5 * max(distancias)


def busqueda_avara(mundo):
    inicio_tiempo = perf_counter()

    estado = estado_inicial(mundo)
    raiz = crear_nodo(estado, h=heuristica(estado))

    pendientes = [raiz]
    visitados = set()
    orden_expansion = 0
    profundidad_max = 0
    meta = None

    while pendientes:
        # Seleccionar el nodo con menor heurística
        mejor_indice = 0

        for i in range(1, len(pendientes)):
            if pendientes[i]["h"] < pendientes[mejor_indice]["h"]:
                mejor_indice = i

        nodo = pendientes.pop(mejor_indice)
        estado_actual = nodo["estado"]

        if estado_actual in visitados:
            continue

        visitados.add(estado_actual)

        orden_expansion += 1
        nodo["orden"] = orden_expansion

        if es_meta(estado_actual):
            meta = nodo
            break

        for operador, nuevo_estado, costo_mov in movimientos_y_efectos(
            estado_actual, mundo
        ):
            if nuevo_estado in visitados:
                continue

            nuevo_costo = nodo["costo"] + costo_mov

            hijo = crear_nodo(
                nuevo_estado,
                padre=nodo,
                operador=operador,
                costo=nuevo_costo,
                h=heuristica(nuevo_estado)
            )
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            pendientes.append(hijo)

    tiempo = perf_counter() - inicio_tiempo

    return {
        "raiz": raiz,
        "meta": meta,
        "nodos_expandidos": orden_expansion,
        "tiempo": tiempo,
        "profundidad": profundidad_max,
        "costo": meta["costo"] if meta else None
    }


def busqueda_a_estrella(mundo):
    inicio_tiempo = perf_counter()

    estado = estado_inicial(mundo)
    raiz = crear_nodo(estado, h=heuristica(estado))

    pendientes = [raiz]

    # Mejor costo conocido para llegar a cada estado
    mejores_costos = {estado: 0}

    # Mejor costo con el que ya se expandió cada estado
    costos_expandidos = {}

    orden_expansion = 0
    profundidad_max = 0
    meta = None

    while pendientes:
        # Seleccionar el nodo con menor f(n) = g(n) + h(n)
        mejor_indice = 0

        for i in range(1, len(pendientes)):
            f_actual = pendientes[i]["costo"] + pendientes[i]["h"]
            f_mejor = (
                pendientes[mejor_indice]["costo"]
                + pendientes[mejor_indice]["h"]
            )

            if f_actual < f_mejor:
                mejor_indice = i

        nodo = pendientes.pop(mejor_indice)
        estado_actual = nodo["estado"]
        costo_actual = nodo["costo"]

        # Ignorar caminos que ya fueron superados por uno más barato
        if costo_actual > mejores_costos.get(estado_actual, float("inf")):
            continue

        # No expandir otra vez si ya se procesó con un costo igual o menor
        if costo_actual >= costos_expandidos.get(
            estado_actual, float("inf")
        ):
            continue

        costos_expandidos[estado_actual] = costo_actual

        orden_expansion += 1
        nodo["orden"] = orden_expansion

        if es_meta(estado_actual):
            meta = nodo
            break

        for operador, nuevo_estado, costo_mov in movimientos_y_efectos(
            estado_actual, mundo
        ):
            nuevo_costo = costo_actual + costo_mov

            # Solo conservar el camino si mejora el costo conocido
            if nuevo_costo < mejores_costos.get(
                nuevo_estado, float("inf")
            ):
                mejores_costos[nuevo_estado] = nuevo_costo

                hijo = crear_nodo(
                    nuevo_estado,
                    padre=nodo,
                    operador=operador,
                    costo=nuevo_costo,
                    h=heuristica(nuevo_estado)
                )
                profundidad_max = max(profundidad_max, hijo["profundidad"])

                pendientes.append(hijo)

    tiempo = perf_counter() - inicio_tiempo

    return {
        "raiz": raiz,
        "meta": meta,
        "nodos_expandidos": orden_expansion,
        "tiempo": tiempo,
        "profundidad": profundidad_max,
        "costo": meta["costo"] if meta else None
    }


def reconstruir_camino(meta):
    if meta is None:
        return []

    camino = []
    nodo = meta

    while nodo["padre"] is not None:
        camino.append({
            "estado": nodo["estado"],
            "operador": nodo["operador"],
            "costo": nodo["costo"]
        })
        nodo = nodo["padre"]

    camino.reverse()

    return camino


if __name__ == "__main__":
    from mundo import leer_mundo

    mundo = leer_mundo("Prueba1.txt")
    resultado = busqueda_a_estrella(mundo)

    print("Nodos expandidos:", resultado["nodos_expandidos"])
    print("Tiempo:", resultado["tiempo"])
    print("Profundidad:", resultado["profundidad"])
    print("Costo:", resultado["costo"])

    if resultado["meta"] is None:
        print("No se encontró una solución.")
    else:
        print("¡Solución encontrada!")

    camino = reconstruir_camino(resultado["meta"])

    print("\nLongitud del camino:", len(camino))
    print("\nMovimientos de AgroBot:")

    for paso, movimiento in enumerate(camino, start=1):
        print(
            paso,
            movimiento["operador"],
            movimiento["estado"],
            "Costo acumulado:",
            movimiento["costo"]
        )
    costo_verificado = sum(
        movimiento["costo"] - (
            camino[i - 1]["costo"] if i > 0 else 0
        )
        for i, movimiento in enumerate(camino)
    )

    print("Costo verificado:", costo_verificado)