#flipflip
#importamos collections deque para almacenar de manera eficiente
# como contexto, deque es lo mismo que usaban los worker procesos de la pool
# una colita de dos lados para manipulacion mas melita
from collections import deque
import time # tiempo por las medidas obviamente cough cough
# Importamos elementos necesarios para hacer los algoritmos.
from estado import estado_inicial, es_meta, movimientos_y_efectos
from arbol import crear_nodo

#========================= Funciones Generales =========================
# Estas vainas TECNICAMENTE las deberian de usar en algun punto en sus algoritmos

"""
Funcion validadora, que mira los casos de excepcion del codigo, cuando llegamos a:
- Avioneta
- Deposito de fertilizante
- Cultivo seco (TENIENDO FERTILIZANTE!!!!!!!!)
Si se cumple que estamos en estas celdas de excepcion retornamos un true para marcar
que debemos de limpiar el camino recorrido
"""
def es_excepcion(estado_padre, estado_hijo, mundo):
    """True si el hijo llega a una celda que reinicia el historial de la rama."""
    celda = (estado_hijo[0], estado_hijo[1])
    if celda == mundo["deposito"]:
        return True
    if celda == mundo["avioneta"]:
        return True
    if len(estado_hijo[3]) < len(estado_padre[3]):  # si pasa, rego un cultivo seco
        return True
    return False

"""

"""
def celda_en_historial(nodo, celda):
    """True si la celda ya fue recorrida en la rama de `nodo`, desde el ultimo reinicio."""
    actual = nodo
    while actual is not None:
        estado = actual["estado"]
        if (estado[0], estado[1]) == celda:
            return True
        if actual["reinicio"]:
            return False
        actual = actual["padre"]
    return False


def reconstruir_camino(nodo_meta):
    """Lista de operadores desde la raiz hasta nodo_meta."""
    operadores = []
    nodo = nodo_meta
    while nodo["padre"] is not None:
        operadores.append(nodo["operador"])
        nodo = nodo["padre"]
    operadores.reverse()
    return operadores










#========================= Algoritmo Amplitud =========================
def amplitud(mundo):
    inicio = time.perf_counter()

    raiz = crear_nodo(estado_inicial(mundo))
    raiz["reinicio"] = True  # la raiz abre el historial de la rama

    cola = deque([raiz])
    expandidos = 0
    profundidad_max = 0
    nodo_meta = raiz if es_meta(raiz["estado"]) else None

    while cola and nodo_meta is None:
        nodo = cola.popleft()
        expandidos += 1
        nodo["orden"] = expandidos

        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo):
            celda = (estado_hijo[0], estado_hijo[1])
            if celda_en_historial(nodo, celda):
                continue

            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov)
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo)
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            if es_meta(estado_hijo):
                nodo_meta = hijo
                break
            cola.append(hijo)

    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "profundidad": profundidad_max,
        "tiempo": time.perf_counter() - inicio,
    }




#========================= Funcion Principal Main =========================
if __name__ == "__main__":
    import sys
    from mundo import leer_mundo

    mundo = leer_mundo(sys.argv[1] if len(sys.argv) > 1 else "Prueba1.txt")
    # Prueba amplitud
    r = amplitud(mundo)
    #prueba otros algoritmos
    #r = costo(mundo)
    #r = .....
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))