TAMANO = 10

# codigos de los diferentes elementos del mundo
LIBRE = 0
OBSTACULO = 1
AGROBOT = 2
CULTIVO_SECO = 3
DEPOSITO = 4
AVIONETA = 5

# el que adivine que hace la funcion se gana un chocobreak
def leer_mundo(ruta):
    lineas = []  # en esta lista se van a guardar las filas del archivo de texto, algo como [1 1 4 1 1 1 5 1 1 1]

    with open(ruta, encoding="utf-8") as f: # abre el archivo y lo cierra al terminar de leer
        for linea in f:
            linea = linea.strip()           # le quita espacios en blanco y saltos de linea al principio y al final
            if linea != "":                 # ignora si esta vacio
                lineas.append(linea)

    if len(lineas) != TAMANO:
        raise ValueError(f"Se esperaban {TAMANO} filas y hay {len(lineas)}.")

    matriz = []  # una lista de listas, donde se va a guardar la lista con cada elemento de la fila separado por comas, es decir, algo como [[1, 1, 4, 1, 1, 1, 5, 1, 1, 1], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], ...]
    
    for i, linea in enumerate(lineas): # enumerate devuelve el indice y el valor de la fila, es decir, (0, "1 1 4 1 1 1 5 1 1 1"), (1, "0 0 0 0 0 0 0 0 0 0"), ...
        fila = []   # guarda los elementos separados por comas, ej [1, 1, 4, 1, 1, 1, 5, 1, 1, 1]
        try:
            for num in linea.split():
                fila.append(int(num))   # separa los elementos con comas y se asegura de que solo sean enteros
        except ValueError:
            raise ValueError(f"Fila {i} tiene valores que no son numeros enteros.")
        
        if len(fila) != TAMANO:
            raise ValueError(f"Fila {i}: se esperaban {TAMANO} columnas y hay {len(fila)}.")
        
        for j, valor in enumerate(fila):
            if valor not in range(6):   # si alguna casilla tiene un numero que no este entre 0 y 5, lanza un error
                raise ValueError(f"Casilla ({i},{j}): valor {valor} fuera del rango.")
            
        matriz.append(fila)

    posiciones = {}  # un diccionario que guarda las posiciones de cada elemento del mundo, siendo la clave el codigo y el valor la  lista de posiciones,
                     # ej {0: [(1, 0), (1, 1), ...], 1: [(0, 0), (0, 1), ...], 2: [(0, 2)], 3: [(2, 2), (2, 3), ...], 4: [(0, 6)], 5: [(0, 7)]}
    for codigo in range(6):
        posiciones[codigo] = []  # inicializa la lista de posiciones para cada codigo

    for i, fila in enumerate(matriz):
        for j, valor in enumerate(fila):
            posiciones[valor].append((i, j))  # recorre cada casilla de la matriz y guarda la posicion de cada elemento en el diccionario

    
    for codigo, nombre in ((AGROBOT, "AgroBot"), (DEPOSITO, "deposito"), (AVIONETA, "avioneta")):  # verifica que haya solo 1 agrobot, 1 deposito y 1 avioneta
        if len(posiciones[codigo]) != 1:
            raise ValueError(f"Debe haber exactamente 1 {nombre} y hay {len(posiciones[codigo])}.")

    return {
        "matriz": matriz,                                # la matriz con los codigos de cada elemento del mundo
        "inicio": posiciones[AGROBOT][0],                # devuelve la posicion inicial del agrobot, que es la unica que hay pq solo hay un agrobot jaja
        "deposito": posiciones[DEPOSITO][0],             # devuelve la posicion del deposito, que es la unica que hay pq solo hay un deposito jaja
        "avioneta": posiciones[AVIONETA][0],             # devuelve la posicion de la avioneta, que es la unica que hay pq solo hay una avioneta jaja
        "cultivos": tuple(posiciones[CULTIVO_SECO]),     # devuelve la tupla de posiciones de los cultivos secos
    }


if __name__ == "__main__":
    # PRUEBA PA VERIFICAR QUE EFECTIVAMENTE TRIPI Y SE LEE EL MUNDO BIEN
    import sys
    m = leer_mundo(sys.argv[1] if len(sys.argv) > 1 else "Prueba1.txt")
    print("AgroBot :", m["inicio"])
    print("Deposito:", m["deposito"])
    print("Avioneta:", m["avioneta"])
    print("Cultivos secos:", sorted(m["cultivos"]))