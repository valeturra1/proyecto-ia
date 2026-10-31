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
Funcion celda_en_historial:
Esta funcion en escencia sirve para confirmar si una celda ya se encuentra por la rama que me estoy moviendo en determinado
la logica es: estamos en un nodo, queremos ir a una celda, entonces lo que hacemos es en el while vemos: la posicion del nodo (aka el
nodo es la misma celda? (estan en el mismo sitio XD)), si NO, validamos si es un reinicio este nodo donde comenzamos busqueda (para si venimos
de reinicios por casos de excepcion o inicios no hacer toda la busqueda de golpe), ahora, si paso la primer tanda, nos devolvemos por el padre.
SOLO cambio el nodo, pues ahora el nodo es nodo_padre, con un estado y posicion diferente, PERO seguimos trabajando con la misma CELDA. de esta
manera nos devolvemos por todos los nodos y posiciones, comparando con la misma celda para corroborar que no la hemos recorrido.
"""
def celda_en_historial(nodo, celda): #recibe un nodo y una celda (candidata donde nos moveriamos)
    """True si la celda ya fue recorrida en la rama de `nodo`, desde el ultimo reinicio."""
    actual = nodo #definimos la posicion actual con el nodo recibido (donde tamos parados)
    # ahora en este bucle lo que hacemos es repetir el codigo hasta que sea None (y cuando es none tofi?) cuando llegamos a la raiz
    # debido a que el apdre de actual sera None (no existe papa de una raiz bruh) 
    while actual is not None:
        estado = actual["estado"] #copiamos el estado del nodo actual para sacar su posicion en fil y col
        if (estado[0], estado[1]) == celda: #comprobamos si en el estado del nodo, su posicion es la misma de la celda 
            return True #Si si, entonces devolvemos que ya se recorrio
        if actual["reinicio"]: #si estamos ante un arbol que apenas "nacio", es decir, su historial comienza desde 0 por caso excepcion
            return False # No esta en historial por que pues, reiniciamos!
        actual = actual["padre"] #cambiamos actual a su padre (nos devolvemos pa arriba), esto sigue hasta recorrer toooda la rama ;)
    return False #Si luego de recorrer toda la rama no encontramos nada, devolvemos un false.

"""
Funcion reconstruir_camino:
Funcion que permite como su nombre lo indica, reconstruir de movimientos a realizar para la solucion obtenida con determinado algoritmo.
Esta con un nodo meta (que encontramos y asignamos al hacer en cada algoritmo la validacion de es_meta) nos devolvemos por todos los padres
hasta llegar a la raiz (donde padre seria None), y vamos recopilando que operador se aplico para cada uo de estos nodos.
"""
def reconstruir_camino(nodo_meta):
    """Lista de operadores desde la raiz hasta nodo_meta."""
    operadores = [] 
    nodo = nodo_meta 
    while nodo["padre"] is not None: #recorremos padres hasta raiz
        operadores.append(nodo["operador"]) #almacenamos operador
        nodo = nodo["padre"] #nos movemos al siguiente padre
    operadores.reverse() #invertimos la lista, pues al ir de abajo a arriba tendremos de los ultimos movimientos a los primeros.
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
def amplitud(mundo): # recibimos el munddo como contexto
    inicio = time.perf_counter()

    # Se hace la inicializacion de variables. creamos la raiz del arbol, definimos el nodo raiz como reinicio pues comienza con un
    # historial nuevo.
    raiz = crear_nodo(estado_inicial(mundo))
    raiz["reinicio"] = True  # la raiz abre el historial de la rama

    # se crea una cola para guardar los nodos
    cola = deque([raiz])
    #Ademas, inicializamos las variables (expandidos, profundidad maxima y nodo_meta son plenamente para almacenar datos requeridos)
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None #None hasta que sepamos cual es (se sabra en la verificacion de es_meta)

    #ciclo while que se repite mientras que la cola de nodos NO este vacia y que NO hayamos encontrado el nodo solucion.
    while cola and nodo_meta is None:
        nodo = cola.popleft() #sacamos el nodo mas viejo en la cola, la primera vez sera raiz y lo cuenta como expandido.
        expandidos += 1 
        nodo["orden"] = expandidos #cada nodo va llevando el numero acumulado de nodos expandidos

        #Hacemos la validacion de este nodo que sacamos de la cola es la meta o no.
        if es_meta(nodo["estado"]):
            nodo_meta = nodo
            break #si lo es, salimos del bucle.

        # Ahora lo que haremos es la generacion de los nodos hijos como tal. 
        # para cada operador (arriba, abajo, izquierda o derehca)
        # para cada estado hijo (como queda el robot luego de hacer determinado operador)
        # tendremos el costo de hacer el movimiento de este determinado operador
        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo):
            # para cada movimienot posible (operador aplicable) nosotros sacamos su posicion en matriz
            celda = (estado_hijo[0], estado_hijo[1])

            # si ya lo recorrimos en esa rama (evitar ciclines) saltamos esta iteracion
            if celda_en_historial(nodo, celda):
                continue

            # si no lo recorrimos, creamos un nuevo nodo con: estado_hijo (sale de aplicar ese operador en mov_y_efect...)
            # con el nodo actual, el operador que acaba de hacer y el costo acumulado (+ el que se acaba de hacer con dicho operador que se hizo resien)
            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov)
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo) # miramos si esta posicion es causa de excepcion y reinicio
            profundidad_max = max(profundidad_max, hijo["profundidad"]) #aumentamos la profundidad

            cola.append(hijo) #la cola almacena este nuevo hijo.

    # una vez llegamos a la solucion en una de nuestras muchas ramas y nodos, salimos con ese break en es_meta
    # y devolvemos los valores requeridos en el taller, los q estan aqui abajito con el estatus del algoritmo actualmente.
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
    
    # inicializamos el mundo
    raiz = crear_nodo(estado_inicial(mundo))
    raiz["reinicio"] = True  # la raiz abre el historial de la rama

    # por que se maneja como una lista normal? no como deque?
    # basicamente aqui no necesitamos ir expandiendo por "niveles" del arbol cada generacion de nodos (como lo haciamos en amplitud)
    # en profundidad, la escencia de este algoritmo es agarrar una rama y comenzar a expandir a lo loco por esa misma rama hata que
    # lleguemos a un final o encontremos solucion. (por eso en clase veiamos que se ve "recargada a la izquierda"), por que profundizamos
    # al maximo con una rama y nodo y ya lueguito es que pasamos al otro hijo de por alla la primer generacion.
    pila = [raiz]
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

    #mientras tengamos nodos pendientes y no encontremos la meta
    while pila and nodo_meta is None:
        # sacamos el primer elemento y comenzamos a expandir
        nodo = pila.pop()
        expandidos += 1
        nodo["orden"] = expandidos

        # corroboramos si este es la solucion primero
        if es_meta(nodo["estado"]):
            nodo_meta = nodo
            break

        hijos = []
        # ahora calculamos los movimientos posibles que puede realizar este elemento
        for operador, estado_hijo, costo_mov in movimientos_y_efectos(nodo["estado"], mundo):
            celda = (estado_hijo[0], estado_hijo[1])
            
            #verificamos que este operador que intentamos aplicar no este en el historial como usado
            if celda_en_historial(nodo, celda):
                continue

            #si pasa como celda no usada, creamos el hijo con su informacion actualizada.                    
            hijo = crear_nodo(estado_hijo, nodo, operador, nodo["costo"] + costo_mov)
            hijo["reinicio"] = es_excepcion(nodo["estado"], estado_hijo, mundo)
            profundidad_max = max(profundidad_max, hijo["profundidad"])

            # metemos el hijo a la lista (va quedando a la derecha del todo como ultimo elemento añadido)
            hijos.append(hijo)  

        # se apilan en orden inverso para que el primer operador (el más a la izquierda del árbol) sea el primero en salir.
        # es decir, suponiendo que en la primer expansion de raiz podamos hacer arriba, abajo, izquierda y derecha tendriamos pila VACIA
        # de momento, y la lista de hijos = [A,I,D]. pero cuando termina for, si no hicieramos reversed,  la siguiente iteracion del while
        #saca con .pop() el ultimo (D), entonces seria profundidad PARA LA DERECHA XD. con el curso lo hacemos hacia izquierda, entonces basta
        # con almacenar todo en el orden inverso para obtener nuestro resultado del curso. quedando: pila = hijos = [D,I,A], y ahora si flip flip
        # cuando hagamos pop sacamos A, y nos vamos por esa profundidad a la izquierda!! esta logica sigue para el resto de generaciones
        # ejem ejem aclaracion esto es en base a como se definieron el orden de operadores: arriba, abajo, izquierda, derecha jejejjej
        # como guardamos hijos en una lista [], extend lo limpia para que al guardarlo en pila no queden () basura
        pila.extend(reversed(hijos))

    # devolvemos datos de resultados.
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

    # Cola de prioridad: menor h(n) primero.
    # El contador conserva el orden de inserción cuando hay empates.
    contador = 0
    pendientes = [(raiz["h"], contador, raiz)]

    visitados = set()
    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

    while pendientes:
        _, _, nodo = heapq.heappop(pendientes)
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

            profundidad_max = max(
                profundidad_max, hijo["profundidad"]
            )

            contador += 1
            heapq.heappush(
                pendientes, (hijo["h"], contador, hijo)
            )

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

    # Cola de prioridad: menor f(n) = g(n) + h(n) primero.
    # El contador conserva el orden de inserción cuando hay empates.
    contador = 0
    pendientes = [(raiz["costo"] + raiz["h"], contador, raiz)]

    # Mejor costo conocido para llegar a cada estado.
    mejores_costos = {estado: 0}

    # Mejor costo con el que ya se expandió cada estado.
    costos_expandidos = {}

    expandidos = 0
    profundidad_max = 0
    nodo_meta = None

    while pendientes:
        _, _, nodo = heapq.heappop(pendientes)

        estado_actual = nodo["estado"]
        costo_actual = nodo["costo"]

        # Ignorar caminos superados por uno más barato.
        if costo_actual > mejores_costos.get(
            estado_actual, float("inf")
        ):
            continue

        # No expandir otra vez con un costo igual o mayor.
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

            # Solo incorporar el estado si encontramos un costo mejor.
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

                profundidad_max = max(
                    profundidad_max, hijo["profundidad"]
                )

                contador += 1
                prioridad = hijo["costo"] + hijo["h"]

                heapq.heappush(
                    pendientes, (prioridad, contador, hijo)
                )

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