from mundo import TAMANO, OBSTACULO, DEPOSITO, AVIONETA

CAP_FERTILIZANTE = 2
COMBUSTIBLE = 30
COSTO_MOVIMIENTO = 1
COSTO_MOV_AVIONETA = 0.5

#operadores del mundo, define como nos movemos y que significa esto dentro de la matriz.
operadores = [("arriba", (-1, 0)), ("abajo", (1, 0)), ("izquierda", (0, -1)), ("derecha", (0, 1))] # nombre del operador y el cambio en la fila y columna que produce

#definimos el estado inicial de la partida
def estado_inicial(mundo):
    agrobot = mundo["inicio"]
    fila = agrobot[0]
    columna = agrobot[1]
    fertilizante = 0
    cultivos_secos = mundo["cultivos"]
    combustible_inicial = 0
    avioneta_usada = False

    return (fila, columna, fertilizante, cultivos_secos, combustible_inicial, avioneta_usada)

# Funcion para validar si un determinado nodo es meta.
def es_meta(estado):
    cultivos_secos = estado[3]

    if len(cultivos_secos) == 0:
        return True
    else:
        return False


# Funion que nos genera los hijos POSIBLES. 
def movimientos_y_efectos(estado, mundo):
    # Sacamos todo del estado actual donde llamamos movimientos_y_efectos
    fila, columna, fertilizante, cultivos_secos, combustible_inicial, avioneta_usada = estado
    # Sacamos datos de la partida
    matriz_mundo = mundo["matriz"] 
    deposito = mundo["deposito"]
    avioneta = mundo["avioneta"]

    movimientos_posibles = []

    # Prueba con operadores (la lista de tuplas de arriba, osea prueba en orden: arriba, abajo, izquierda, derecha XD)
    for operador in operadores:
        # ahora recorremos cada operador: primer tupla, segunda tupla, tercer tupla y cuarta tupla..
        # Anotacion para comprender mejor! operador[1][0] hace que para cada tupla operador[m][n], entramos a la parte [m] de la tupla (es decir)
        #los valores (-1,0 o 1,1 etc etc), y [n] es CUAL TOMAMOS dentro de esta parte [m]. entonces [1][0] es: entramos a parte [m] (valores)
        # y tomamos [0], que en nuestro caso como se define en operadores sera el valor de fila (por eso arriba y abajo se maneja con esto).
        # para el caso de columna es [1][1], pues accedemos al segundo elemendo! 

        # fila nueva sera: posicion de fila actual + desplazamiento.
        fila_nueva = fila + operador[1][0]
        # columna nueva sera: posicion de col actual + 
        columna_nueva = columna + operador[1][1]

        #probamos si el movimiento es valido
        # no puede aplicar este operador porque lo dejaria fuera del mundo o por que lo moveria a un obstaculo, sigue con el siguiente operador
        if fila_nueva < 0 or fila_nueva >= TAMANO or columna_nueva < 0 or columna_nueva >= TAMANO or matriz_mundo[fila_nueva][columna_nueva] == OBSTACULO:
            continue

        # descontamos uso de avioneta si se dio y contamos el costo de desplazamiento por la mitad. (uso el avion brr brr)
        if combustible_inicial > 0:  # si esta usando la avioneta
            combustible_nuevo = combustible_inicial - 1
            costo_mov = COSTO_MOV_AVIONETA
        else: #sino, sencillamente no usa la avioneta
            combustible_nuevo = combustible_inicial
            costo_mov = COSTO_MOVIMIENTO


        fertilizante_nuevo = fertilizante
        cultivos_secos_nuevo = cultivos_secos
        avioneta_usada_nueva = avioneta_usada

        if (fila_nueva, columna_nueva) == deposito:  # si llego a el deposito, recarga fertilizante
            fertilizante_nuevo = CAP_FERTILIZANTE
        elif (fila_nueva, columna_nueva) == avioneta and avioneta_usada == False:  # si llego a la avioneta, recarga combustible
            combustible_nuevo = COMBUSTIBLE
            avioneta_usada_nueva = True
        elif (fila_nueva, columna_nueva) in cultivos_secos:  # si esta en un cultivo seco y tiene fertilizante, lo riega y lo quita de la lista de cultivos secos
            if fertilizante > 0:
                fertilizante_nuevo = fertilizante - 1

                # lo quitamos de la lista
                cultivos_restantes = []
                for cultivo in cultivos_secos:
                    if cultivo != (fila_nueva, columna_nueva):
                        cultivos_restantes.append(cultivo)
                cultivos_secos_nuevo = tuple(cultivos_restantes)

        # almacenamos este nuevo estado despues de probar los movimientos.
        nuevo_estado = (fila_nueva, columna_nueva, fertilizante_nuevo, cultivos_secos_nuevo, combustible_nuevo, avioneta_usada_nueva)
        movimientos_posibles.append((operador[0], nuevo_estado, costo_mov))  #devolvemos el nombre del movimiento, su estado y costo tras este. :3

    return movimientos_posibles #volvemos la lista con el informe de que movimientos puede hacer ese turno