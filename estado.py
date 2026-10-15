from mundo import TAMANO, OBSTACULO, DEPOSITO, AVIONETA

CAP_FERTILIZANTE = 2
COMBUSTIBLE = 30
COSTO_MOVIMIENTO = 1
COSTO_MOV_AVIONETA = 0.5

operadores = [("arriba", (-1, 0)), ("abajo", (1, 0)), ("izquierda", (0, -1)), ("derecha", (0, 1))] # nombre del operador y el cambio en la fila y columna que produce

def estado_inicial(mundo):
    agrobot = mundo["inicio"]
    fila = agrobot[0]
    columna = agrobot[1]
    fertilizante = 0
    cultivos_secos = mundo["cultivos"]
    combustible_inicial = 0
    avioneta_usada = False

    return (fila, columna, fertilizante, cultivos_secos, combustible_inicial, avioneta_usada)

def es_meta(estado):
    cultivos_secos = estado[3]

    if len(cultivos_secos) == 0:
        return True
    else:
        return False

def movimientos_y_efectos(estado, mundo):
    fila, columna, fertilizante, cultivos_secos, combustible_inicial, avioneta_usada = estado
    matriz_mundo = mundo["matriz"]
    deposito = mundo["deposito"]
    avioneta = mundo["avioneta"]

    movimientos_posibles = []

    for operador in operadores:
        fila_nueva = fila + operador[1][0]
        columna_nueva = columna + operador[1][1]

        # no puede aplicar este operador porque lo dejaria fuera del mundo o por que lo moveria a un obstaculo, sigue con el siguiente operador
        if fila_nueva < 0 or fila_nueva >= TAMANO or columna_nueva < 0 or columna_nueva >= TAMANO or matriz_mundo[fila_nueva][columna_nueva] == OBSTACULO:
            continue


        if combustible_inicial > 0:  # si esta usando la avioneta
            combustible_nuevo = combustible_inicial - 1
            costo_mov = COSTO_MOV_AVIONETA
        else:
            combustible_nuevo = combustible_inicial
            costo_mov = COSTO_MOVIMIENTO


        fertilizante_nuevo = fertilizante
        cultivos_secos_nuevo = cultivos_secos
        avioneta_usada_nueva = avioneta_usada

        if (fila_nueva, columna_nueva) == deposito:  # si esta en el deposito, recarga fertilizante
            fertilizante_nuevo = CAP_FERTILIZANTE
        elif (fila_nueva, columna_nueva) == avioneta and avioneta_usada == False:  # si esta en la avioneta, recarga combustible
            combustible_nuevo = COMBUSTIBLE
            avioneta_usada_nueva = True
        elif (fila_nueva, columna_nueva) in cultivos_secos:  # si esta en un cultivo seco y tiene fertilizante, lo riega y lo quita de la lista de cultivos secos
            if fertilizante > 0:
                fertilizante_nuevo = fertilizante - 1

                cultivos_restantes = []
                for cultivo in cultivos_secos:
                    if cultivo != (fila_nueva, columna_nueva):
                        cultivos_restantes.append(cultivo)
                cultivos_secos_nuevo = tuple(cultivos_restantes)

        nuevo_estado = (fila_nueva, columna_nueva, fertilizante_nuevo, cultivos_secos_nuevo, combustible_nuevo, avioneta_usada_nueva)
        movimientos_posibles.append((operador[0], nuevo_estado, costo_mov))

    return movimientos_posibles