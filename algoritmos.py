#flipflip
#importamos collections deque para almacenar de manera eficiente
# como contexto, deque es lo mismo que usaban los worker procesos de la pool
# una colita de dos lados para manipulacion mas melita
from collections import deque
import heapq
import time # tiempo por las medidas obviamente cough cough
# Importamos elementos necesarios para hacer los algoritmos.
from estado import estado_inicial, es_meta, movimientos_y_efectos, operadores as OPERADORES
from arbol import crear_nodo

ORDEN_OPERADORES = {nombre: i for i, (nombre, _) in enumerate(OPERADORES)}

#========================= Funciones Generales =========================
# Estas vainas TECNICAMENTE las deberian de usar en algun punto en sus algoritmos

"""
Funcion validadora, que mira los casos de excepcion del codigo, cuando llegamos a:
- Avioneta
- Deposito de fertilizante
- Cultivo seco (TENIENDO FERTILIZANTE!!!!!!!!)
Si se cumple que estamos en estas celdas de excepcion retornamos un true para marcar
que debemos de limpiar el camino recorrido
util? -> es decir que si llega al fertilizante es por que tiene menos de 2, que solo reinicie
al tomar avioneta primer vez y ademas que solo si el cultivo fue regado.
(esto evita ciclos en el caso de profundidad, sino se podian dar casos como: avioneta->fertilizante->avioneta->ferti.... etc etc)
"""
def es_excepcion(estado_padre, estado_hijo, mundo):
    """True si el hijo llega a una celda que reinicia el historial de la rama.
    Ojo vivo, ahora solo ocurre si es de forma util"""
    celda = (estado_hijo[0], estado_hijo[1]) #almacenamos la posicion fila,columna
    #verificamos si estamos en la celda de deposito Y ADEMAS si la cantidad de fertilizante que obtenemos aumenta despues de tomarlo (fue util xd)
    if celda == mundo["deposito"] and estado_hijo[2] > estado_padre[2]: 
        return True
    #verificamos si estamos en la celda de avioneta y ADEMAS si el estado en el que estamos ya tiene marcada la avioneta como usada.
    #Asi, en caso de usarla, llegar a esta casilla no tiene ningun efecto pues no obtenemos nada.
    if celda == mundo["avioneta"] and not estado_padre[5]:
        return True
    # Si el numero de fertilizante dismiuye significa que REGAMOS un cultivos seeco
    if len(estado_hijo[3]) < len(estado_padre[3]): 
        return True
    return False #si no cayo en estas excepciones, es una celda ordinaria, continua el flip flip.

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

# funcion HEURISTICA para algoritmos de busqueda informada
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





#====================================================================================================
#========================= ALGORITMOS DE BUSQUEDA NO INFORMADA =========================
#====================================================================================================

#========================= 1. Algoritmo Amplitud =========================
def amplitud(mundo):
    inicio = time.perf_counter()

    raiz = crear_nodo(estado_inicial(mundo))
    raiz["reinicio"] = True  # la raiz abre el historial de la rama

    cola = deque([raiz])
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

    while cola and nodo_meta is None:
        nodo = cola.popleft()
        expandidos += 1
        nodo["orden"] = expandidos

        if es_meta(nodo["estado"]):
            nodo_meta = nodo
            break

        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo):
            celda = (estado_hijo[0], estado_hijo[1])
            if celda_en_historial(nodo, celda):
                continue

            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov)
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo)
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            cola.append(hijo)

    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "profundidad": profundidad_max,
        "tiempo": time.perf_counter() - inicio,
    }


#========================= 2. Algoritmo de Costo uniforme =========================
def coste_uniforme(mundo):
    inicio = time.perf_counter() #pa medir tiempo

    raiz = crear_nodo(estado_inicial(mundo)) # creamos el nodo inicial :>
    raiz["reinicio"] = True # es lo que habia implementado juan jose de reinicio cuando riega y asi

    contador = 0 # el desempate definitico 
    frontera = [(0, 0, contador, raiz)] # edtructura que vamos a usar para gaurdar todos los noddos que ya genere
    expandidos = 0 #el que adivine que significa esto se gana un premio
    profundidad_max = 0
    nodo_meta = None 


    while frontera: #mientras haya algo en frontera pues trin
        _,_,_,nodo = heapq.heappop(frontera) #cola de prioridad :3 es para que siempre saque el que tiene menor coste sin improtar el orden en el que se ingresan a la cola

        expandidos += 1 
        nodo["orden"] = expandidos

        if es_meta(nodo["estado"]): #si el nodo que sacamos de la frontera es la meta pues terminamos con lo que ya hay
            nodo_meta = nodo
            break

        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo): #recordemos que la funcion nos devuelve esos 3 valores, entonces por cada operador, nuevo estado y tales que nos devuevla la funcion vamos a hacer la validacion de recorrido 
            
            # lo que hizo juan jose para evitar ciclos
            celda = (estado_hijo[0], estado_hijo[1]) # definimos la celda 

            if celda_en_historial(nodo, celda):
                continue

            # creo el hijo con el operador ligado a su padre y me voy quedando con la profundidad maxima mientras voy expandiendo
            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov) #
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo)
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            # aqui meto el hijo a la cola de espera, o sea a la de frontera
            contador += 1 
            heapq.heappush(frontera, (hijo["costo"], ORDEN_OPERADORES[operador], contador, hijo))

    #retorno la meta para recontruir el arbol con las dema metricas
    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "profundidad": profundidad_max,
        "tiempo": time.perf_counter() - inicio,
    }



#========================= 3. Algoritmo Profundidad evitando ciclos =========================
def profundidad(mundo):
    inicio = time.perf_counter()

    raiz = crear_nodo(estado_inicial(mundo))
    raiz["reinicio"] = True  # la raiz abre el historial de la rama

    pila = [raiz]
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

    while pila and nodo_meta is None:
        nodo = pila.pop()
        expandidos += 1
        nodo["orden"] = expandidos

        if es_meta(nodo["estado"]):
            nodo_meta = nodo
            break

        hijos = []
        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo):
            celda = (estado_hijo[0], estado_hijo[1])
            if celda_en_historial(nodo, celda):
                continue

            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov)
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo)
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            hijos.append(hijo)

        # se apilan en orden inverso para que el primer operador
        # (el más a la izquierda del árbol) sea el primero en salir
        pila.extend(reversed(hijos))

    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "profundidad": profundidad_max,
        "tiempo": time.perf_counter() - inicio,
    }



#====================================================================================================
#========================= ALGORITMOS DE BUSQUEDA INFORMADA =========================
#====================================================================================================

#========================= 4. Algoritmo de Busqueda avara =========================
def busqueda_avara(mundo):
    inicio_tiempo = time.perf_counter()

    estado = estado_inicial(mundo)
    raiz = crear_nodo(estado, h=heuristica(estado))

    pendientes = [raiz]
    visitados = set()
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

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

        expandidos += 1
        nodo["orden"] = expandidos

        if es_meta(estado_actual):
            nodo_meta = nodo
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

    tiempo = time.perf_counter() - inicio_tiempo

    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "tiempo": tiempo,
        "profundidad": profundidad_max,
    }

#========================= 5. Algoritmo de busqueda Estrella =========================
def busqueda_a_estrella(mundo):
    inicio_tiempo = time.perf_counter()

    estado = estado_inicial(mundo)
    raiz = crear_nodo(estado, h=heuristica(estado))

    pendientes = [raiz]

    # Mejor costo conocido para llegar a cada estado
    mejores_costos = {estado: 0}

    # Mejor costo con el que ya se expandió cada estado
    costos_expandidos = {}

    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

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

        expandidos += 1
        nodo["orden"] = expandidos

        if es_meta(estado_actual):
            nodo_meta = nodo
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

    tiempo = time.perf_counter() - inicio_tiempo

    return {
        "nodo_meta": nodo_meta,
        "expandidos": expandidos,
        "tiempo": tiempo,
        "profundidad": profundidad_max,
    }


#========================= Funcion Principal Main =========================
if __name__ == "__main__":
    import sys
    from mundo import leer_mundo

    #definimos el mundo (junto al archivo de prueba dado por el profesor oskitar)
    mundo = leer_mundo(sys.argv[1] if len(sys.argv) > 1 else "Prueba1.txt")

    print("***********************************PRUEBA DE ALGORITMOS DE BUSQUEDA NO INFORMADA***********************************")

    # Prueba amplitud
    print("PRUEBA DE ALGORITMO AMPLITUD")
    r = amplitud(mundo)
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))

    #prueba costo uniforme
    print("PRUEBA DE ALGORITMO COSTO UNIFORME")
    r = coste_uniforme(mundo)
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion s")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))

# Prueba profundidad evitando ciclos
    print("PRUEBA DE ALGORITMO PROFUNDIDAD EVITANDO CICLOS")
    r = profundidad(mundo)
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))

    print("***********************************PRUEBA DE ALGORITMOS DE BUSQUEDA INFORMADA***********************************")

    print("PRUEBA DE ALGORITMO BUSQUEDA AVARA")
    r = busqueda_avara(mundo)
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))

    print("PRUEBA DE ALGORITMO BUSQUEDA A ESTRELLA")
    r = busqueda_a_estrella(mundo)
    print("Expandidos:", r["expandidos"])
    print("Profundidad:", r["profundidad"])
    print("Tiempo:", round(r["tiempo"], 4), "s")
    if r["nodo_meta"] is None:
        print("Sin solucion")
    else:
        print("Costo:", r["nodo_meta"]["costo"])
        print("Camino:", reconstruir_camino(r["nodo_meta"]))