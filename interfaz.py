import os
import sys
import pygame

from mundo import (leer_mundo, TAMANO, OBSTACULO, AGROBOT,
                   CULTIVO_SECO, DEPOSITO, AVIONETA)
from algoritmos import amplitud, coste_uniforme, profundidad, busqueda_avara, busqueda_a_estrella

TAM_CASILLA = 50
LADO_MUNDO = TAMANO * TAM_CASILLA
MARGEN = 24
ALTO_ENCABEZADO = 78
X_MUNDO = MARGEN
Y_MUNDO = ALTO_ENCABEZADO + 14
X_DIVISOR = X_MUNDO + LADO_MUNDO + 8 + 20
X_PANEL = X_DIVISOR + 20
ANCHO_PANEL = 550
Y_BARRA = Y_MUNDO + LADO_MUNDO + 8 + 14
ALTO_BARRA = 34
ANCHO_VENTANA = X_PANEL + ANCHO_PANEL + MARGEN
ALTO_VENTANA = Y_BARRA + ALTO_BARRA + 8

# Paleta: pergamino claro, tinta oscura, burdeos y oro apagado como únicos acentos
FONDO = (238, 226, 196)
FONDO_HOVER = (221, 202, 160)
VACIO = (228, 212, 176)
TINTA = (36, 24, 16)
TINTA_SUAVE = (84, 62, 42)
LINEA = (160, 130, 92)
LINEA_FUERTE = (110, 82, 52)
PERGAMINO = (248, 240, 221)
BURDEOS = (104, 22, 30)
BURDEOS_HOVER = (140, 42, 52)
GRIS_BOTON = (150, 136, 114)
ROJO = (150, 30, 30)
ORO = (190, 146, 52)
MADERA = (62, 44, 30)

ALGORITMOS = {
    "No informada": ["Amplitud", "Costo uniforme", "Profundidad evitando ciclos"],
    "Informada": ["Avara", "A*"],
}

NOMBRES_IMAGENES = ["persona", "persona_espada", "persona_mula", "persona_mula_espada",
                    "serpiente_enojada", "serpiente_domada",
                    "espada", "mula", "obstaculo", "tierra"]

NOMBRE_LOGO = "logo"
TAM_LOGO = 52
AJUSTE_TEXTO_BOTON = 4
ESCALA_CAMPESINO = 1.2
CARPETA_IMAGENES = "imagenes"
MS_POR_PASO = 220

ALGORITMOS_CON_COSTO = ["Costo uniforme", "A*"]

FUNCIONES = {
    "Amplitud": amplitud,
    "Costo uniforme": coste_uniforme,
    "Profundidad evitando ciclos": profundidad,
    "Avara": busqueda_avara,
    "A*": busqueda_a_estrella,
}

CLAVES_RESULTADO = {
    "Amplitud": ("nodo_meta", "expandidos"),
    "Costo uniforme": ("nodo_meta", "expandidos"),
    "Profundidad evitando ciclos": ("nodo_meta", "expandidos"),
    "Avara": ("nodo_meta", "expandidos"),
    "A*": ("nodo_meta", "expandidos"),
}

IMAGEN_DE_CODIGO = {
    OBSTACULO: "obstaculo",
    AGROBOT: "persona",
    CULTIVO_SECO: "serpiente_enojada",
    DEPOSITO: "espada",
    AVIONETA: "mula",
}

ELEMENTOS = [
    ("persona", "Campesino"),
    ("serpiente_enojada", "Bestia enojada"),
    ("serpiente_domada", "Bestia domada"),
    ("espada", "Domador de bestias"),
    ("mula", "Mula"),
    ("obstaculo", "Obstáculo"),
    ("tierra", "Suelo libre"),
]


def crear_fuente(nombres, tamano, negrita=False):
    return pygame.font.SysFont(nombres, tamano, bold=negrita)


def recortar(texto, fuente, ancho):
    if fuente.size(texto)[0] <= ancho:
        return texto
    while len(texto) > 3 and fuente.size(texto + "...")[0] > ancho:
        texto = texto[:-1]
    return texto + "..."


def dibujar_texto(pantalla, fuente, texto, x, y, color=TINTA):
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, (x, y))


def dibujar_texto_centrado(pantalla, fuente, texto, centro_x, y, color=TINTA):
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, (centro_x - imagen.get_width() // 2, y))


def dibujar_rombo(pantalla, centro, radio, color, grosor=0):
    cx, cy = centro
    puntos = [(cx, cy - radio), (cx + radio, cy), (cx, cy + radio), (cx - radio, cy)]
    pygame.draw.polygon(pantalla, color, puntos, grosor)


def dibujar_separador(pantalla, x1, x2, y):
    # línea fina con un único rombo central, como remate de manuscrito
    centro = (x1 + x2) // 2
    pygame.draw.line(pantalla, LINEA, (x1, y), (centro - 10, y), 1)
    pygame.draw.line(pantalla, LINEA, (centro + 10, y), (x2, y), 1)
    dibujar_rombo(pantalla, (centro, y), 3, ORO)


def ajustar_imagen(original, lado, rellenar=False):
    ancho, alto = original.get_size()
    if rellenar:
        escala = max(lado / ancho, lado / alto)
    else:
        escala = min(lado / ancho, lado / alto)
    nuevo_ancho = max(1, round(ancho * escala))
    nuevo_alto = max(1, round(alto * escala))
    escalada = pygame.transform.smoothscale(original, (nuevo_ancho, nuevo_alto))
    lienzo = pygame.Surface((lado, lado), pygame.SRCALPHA)
    lienzo.blit(escalada, ((lado - nuevo_ancho) // 2, (lado - nuevo_alto) // 2))
    return lienzo


def leer_png(carpeta, nombre):
    ruta = os.path.join(carpeta, CARPETA_IMAGENES, nombre + ".png")
    try:
        return pygame.image.load(ruta).convert_alpha()
    except (pygame.error, FileNotFoundError) as error:
        raise SystemExit("No se pudo cargar la imagen " + ruta + ": " + str(error))


def cargar_imagenes():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    grandes = {}
    chicas = {}
    for nombre in NOMBRES_IMAGENES:
        original = leer_png(carpeta, nombre)
        rellenar = nombre == "tierra"
        lado = TAM_CASILLA
        if nombre.startswith("persona"):
            lado = round(TAM_CASILLA * ESCALA_CAMPESINO)
        grandes[nombre] = ajustar_imagen(original, lado, rellenar)
        chicas[nombre] = ajustar_imagen(original, 30, rellenar)
    logo = ajustar_imagen(leer_png(carpeta, NOMBRE_LOGO), TAM_LOGO)
    return {"grandes": grandes, "chicas": chicas, "logo": logo}


def poner_imagen(pantalla, rect, imagen):
    pantalla.blit(imagen, (rect.centerx - imagen.get_width() // 2,
                           rect.centery - imagen.get_height() // 2))


def dibujar_casilla(pantalla, rect, codigo, imagenes, celda, vista):
    pantalla.blit(imagenes["grandes"]["tierra"], rect.topleft)
    if codigo == AGROBOT or codigo not in IMAGEN_DE_CODIGO:
        return
    nombre = IMAGEN_DE_CODIGO[codigo]
    if vista is not None:
        if codigo == CULTIVO_SECO and celda not in vista["pendientes"]:
            nombre = "serpiente_domada"
        if codigo == AVIONETA and vista["mula_usada"]:
            return
    poner_imagen(pantalla, rect, imagenes["grandes"][nombre])


def dibujar_agrobot(pantalla, rect, imagenes, en_mula, con_espada):
    if en_mula and con_espada:
        nombre = "persona_mula_espada"
    elif en_mula:
        nombre = "persona_mula"
    elif con_espada:
        nombre = "persona_espada"
    else:
        nombre = "persona"
    poner_imagen(pantalla, rect, imagenes["grandes"][nombre])


def formatear_tiempo(segundos):
    if segundos < 1:
        return str(round(segundos * 1000, 1)) + " ms"
    return str(round(segundos, 2)) + " s"


def formatear_costo(costo):
    if costo == int(costo):
        return str(int(costo))
    return str(costo)


def dibujar_reporte(pantalla, fuentes, reporte):
    datos = [
        ("Nodos expandidos", str(reporte["expandidos"])),
        ("Profundidad del árbol", str(reporte["profundidad"])),
        ("Tiempo de cómputo", formatear_tiempo(reporte["tiempo"])),
    ]
    if reporte["costo"] is not None:
        datos.append(("Costo de la solución", formatear_costo(reporte["costo"])))
    ancho_ficha = 165
    separacion = 8
    total = len(datos) * ancho_ficha + (len(datos) - 1) * separacion
    x = ANCHO_VENTANA - MARGEN - total
    for etiqueta, valor in datos:
        rect = pygame.Rect(x, 12, ancho_ficha, 50)
        pygame.draw.rect(pantalla, PERGAMINO, rect, border_radius=3)
        etiqueta = recortar(etiqueta, fuentes["etiqueta"], ancho_ficha - 10)
        dibujar_texto_centrado(pantalla, fuentes["etiqueta"], etiqueta, rect.centerx, rect.top + 5, TINTA_SUAVE)
        dibujar_texto_centrado(pantalla, fuentes["valor"], valor, rect.centerx, rect.top + 22, BURDEOS)
        x += ancho_ficha + separacion


def dibujar_encabezado(pantalla, fuentes, imagenes, reporte):
    pygame.draw.rect(pantalla, MADERA, (0, 0, ANCHO_VENTANA, ALTO_ENCABEZADO - 3))
    pygame.draw.line(pantalla, ORO, (0, ALTO_ENCABEZADO - 3), (ANCHO_VENTANA, ALTO_ENCABEZADO - 3), 2)
    pantalla.blit(imagenes["logo"], (MARGEN, 12))
    dibujar_texto(pantalla, fuentes["titulo"], "CampesinoBot", MARGEN + 68, 6, ORO)
    dibujar_texto(pantalla, fuentes["suave"], "Búsqueda para domar bestias",
                  MARGEN + 70, 50, PERGAMINO)
    if reporte is not None:
        dibujar_reporte(pantalla, fuentes, reporte)


def dibujar_mundo(pantalla, fuentes, matriz, imagenes, vista):
    mundo = pygame.Rect(X_MUNDO, Y_MUNDO, LADO_MUNDO, LADO_MUNDO)
    marco = mundo.inflate(16, 16)

    if matriz is None:
        pygame.draw.rect(pantalla, VACIO, marco, border_radius=4)
        pygame.draw.rect(pantalla, LINEA, marco, 1, border_radius=4)
        cx = marco.centerx
        cy = marco.centery - 14
        dibujar_rombo(pantalla, (cx, cy - 26), 7, ORO)
        dibujar_texto_centrado(pantalla, fuentes["seccion"], "Suelta aquí el archivo .txt del mundo", cx, cy)
        dibujar_texto_centrado(pantalla, fuentes["suave"], "o pulsa el botón «Cargar mundo»",
                               cx, cy + 30, TINTA_SUAVE)
        return

    pygame.draw.rect(pantalla, MADERA, marco, border_radius=4)
    for i in range(TAMANO):
        for j in range(TAMANO):
            rect = pygame.Rect(X_MUNDO + j * TAM_CASILLA, Y_MUNDO + i * TAM_CASILLA,
                               TAM_CASILLA, TAM_CASILLA)
            dibujar_casilla(pantalla, rect, matriz[i][j], imagenes, (i, j), vista)

    if vista is None:
        for i in range(TAMANO):
            for j in range(TAMANO):
                if matriz[i][j] == AGROBOT:
                    rect = pygame.Rect(X_MUNDO + j * TAM_CASILLA, Y_MUNDO + i * TAM_CASILLA,
                                       TAM_CASILLA, TAM_CASILLA)
                    dibujar_agrobot(pantalla, rect, imagenes, False, False)
    else:
        rect = pygame.Rect(X_MUNDO + vista["col"] * TAM_CASILLA, Y_MUNDO + vista["fila"] * TAM_CASILLA,
                           TAM_CASILLA, TAM_CASILLA)
        dibujar_agrobot(pantalla, rect, imagenes, vista["en_mula"], vista["con_espada"])


def dibujar_segmento(pantalla, fuente, rect, texto, activo, hover):
    if activo:
        pygame.draw.rect(pantalla, BURDEOS, rect, border_radius=3)
        color = PERGAMINO
    else:
        if hover:
            pygame.draw.rect(pantalla, FONDO_HOVER, rect, border_radius=3)
        pygame.draw.rect(pantalla, LINEA_FUERTE, rect, 1, border_radius=3)
        color = TINTA
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, imagen.get_rect(center=rect.center))


def dibujar_opcion(pantalla, fuente, rect, texto, activa, hover):
    if hover and not activa:
        pygame.draw.rect(pantalla, FONDO_HOVER, rect, border_radius=3)
    centro = (rect.left + 16, rect.centery)
    if activa:
        dibujar_rombo(pantalla, centro, 7, BURDEOS)
    else:
        dibujar_rombo(pantalla, centro, 6, LINEA_FUERTE, 1)
    texto = recortar(texto, fuente, rect.width - 40)
    imagen = fuente.render(texto, True, BURDEOS if activa else TINTA)
    pantalla.blit(imagen, (rect.left + 34, rect.centery - imagen.get_height() // 2))


def dibujar_boton_principal(pantalla, fuente, rect, texto, habilitado, hover):
    if not habilitado:
        color = GRIS_BOTON
    elif hover:
        color = BURDEOS_HOVER
    else:
        color = BURDEOS
    pygame.draw.rect(pantalla, color, rect, border_radius=3)
    imagen = fuente.render(texto, True, PERGAMINO)
    total = 12 + 10 + imagen.get_width()
    x0 = rect.centerx - total // 2
    pygame.draw.polygon(pantalla, PERGAMINO, [(x0, rect.centery - 8), (x0, rect.centery + 8),
                                              (x0 + 12, rect.centery)])
    pantalla.blit(imagen, (x0 + 22, rect.centery - imagen.get_height() // 2 + AJUSTE_TEXTO_BOTON))


def dibujar_panel(pantalla, fuentes, app, pos_mouse, imagenes):
    regiones = []
    x = X_PANEL
    ancho = ANCHO_PANEL
    y = Y_MUNDO

    pygame.draw.line(pantalla, LINEA, (X_DIVISOR, Y_MUNDO), (X_DIVISOR, Y_MUNDO + LADO_MUNDO), 1)

    dibujar_texto(pantalla, fuentes["seccion"], "Tipo de búsqueda", x, y, BURDEOS)
    y += 26
    ancho_mitad = (ancho - 8) // 2
    columna = 0
    for nombre in ALGORITMOS:
        rect = pygame.Rect(x + columna * (ancho_mitad + 8), y, ancho_mitad, 36)
        dibujar_segmento(pantalla, fuentes["normal"], rect, nombre,
                         app["tipo"] == nombre, rect.collidepoint(pos_mouse))
        regiones.append((rect, "tipo", nombre))
        columna += 1
    y += 36 + 18
    dibujar_separador(pantalla, x, x + ancho, y)
    y += 16

    dibujar_texto(pantalla, fuentes["seccion"], "Algoritmo", x, y, BURDEOS)
    y += 26
    inicio_opciones = y
    for nombre in ALGORITMOS[app["tipo"]]:
        rect = pygame.Rect(x, y, ancho, 34)
        dibujar_opcion(pantalla, fuentes["normal"], rect, nombre,
                       app["algoritmo"] == nombre, rect.collidepoint(pos_mouse))
        regiones.append((rect, "algoritmo", nombre))
        y += 38
    y = inicio_opciones + 3 * 38 + 6
    dibujar_separador(pantalla, x, x + ancho, y)
    y += 16

    ancho_cargar = 190
    rect_cargar = pygame.Rect(x, y, ancho_cargar, 44)
    if busqueda_en_curso(app):
        # deshabilitado: no se puede cargar otro mundo mientras se busca o se anima la solución
        pygame.draw.rect(pantalla, GRIS_BOTON, rect_cargar, border_radius=3)
        imagen = fuentes["normal"].render("Cargar mundo", True, PERGAMINO)
        pantalla.blit(imagen, imagen.get_rect(center=rect_cargar.center))
    else:
        dibujar_segmento(pantalla, fuentes["normal"], rect_cargar, "Cargar mundo",
                         False, rect_cargar.collidepoint(pos_mouse))
        regiones.append((rect_cargar, "cargar", None))

    rect = pygame.Rect(x + ancho_cargar + 8, y, ancho - ancho_cargar - 8, 44)
    dibujar_boton_principal(pantalla, fuentes["boton"], rect, "Iniciar búsqueda",
                            app["mundo"] is not None, rect.collidepoint(pos_mouse))
    regiones.append((rect, "iniciar", None))
    y += 44 + 18
    dibujar_separador(pantalla, x, x + ancho, y)
    y += 16

    dibujar_texto(pantalla, fuentes["seccion"], "Elementos", x, y, BURDEOS)
    y += 28
    ancho_columna = ancho // 2
    for k, (clave, nombre) in enumerate(ELEMENTOS):
        cx = x + (k % 2) * ancho_columna
        cy = y + (k // 2) * 34
        muestra = pygame.Rect(cx, cy, 30, 30)
        pantalla.blit(imagenes["chicas"]["tierra"], muestra.topleft)
        if clave != "tierra":
            pantalla.blit(imagenes["chicas"][clave], muestra.topleft)
        pygame.draw.rect(pantalla, LINEA, muestra, 1)
        texto = recortar(nombre, fuentes["chica"], ancho_columna - 44)
        dibujar_texto(pantalla, fuentes["chica"], texto, cx + 38, cy + 6, TINTA)

    return regiones


def dibujar_barra(pantalla, fuentes, mensaje):
    pygame.draw.line(pantalla, LINEA, (X_MUNDO - 8, Y_BARRA - 7),
                     (ANCHO_VENTANA - MARGEN + 8, Y_BARRA - 7), 1)
    es_error = mensaje.startswith("Error")
    dibujar_rombo(pantalla, (X_MUNDO + 6, Y_BARRA + ALTO_BARRA // 2 - 2), 4, ROJO if es_error else ORO)
    texto = recortar(mensaje, fuentes["normal"], ANCHO_VENTANA - 2 * MARGEN - 24)
    dibujar_texto(pantalla, fuentes["normal"], texto, X_MUNDO + 20, Y_BARRA + 5,
                  ROJO if es_error else TINTA)


def cargar(app, ruta):
    try:
        app["mundo"] = leer_mundo(ruta)
    except (ValueError, OSError) as error:
        app["mensaje"] = "Error: " + str(error)
        return
    app["animacion"] = None
    app["reporte"] = None
    app["carpeta_archivos"] = os.path.dirname(os.path.abspath(ruta))
    app["mensaje"] = "Mundo cargado: " + ruta


def elegir_archivo(carpeta_inicial):
    # Abre el selector de archivos del sistema (tkinter viene con Python).
    # Devuelve (ruta, error): ruta es "" si el usuario cancela; error es None salvo que no se pueda abrir el selector.
    try:
        import tkinter
        from tkinter import filedialog
        raiz = tkinter.Tk()
        raiz.withdraw()
        try:
            raiz.attributes("-topmost", True)
            ruta = filedialog.askopenfilename(
                parent=raiz,
                title="Selecciona el archivo del mundo",
                initialdir=carpeta_inicial,
                filetypes=[("Mundo (.txt)", "*.txt"), ("Todos los archivos", "*.*")],
            )
        finally:
            raiz.destroy()
    except Exception as error:
        return "", str(error)
    return (str(ruta) if ruta else ""), None


def hallar_raiz(resultado, meta):
    if "raiz" in resultado:
        return resultado["raiz"]
    if meta is None:
        return None
    nodo = meta
    while nodo["padre"] is not None:
        nodo = nodo["padre"]
    return nodo


def profundidad_del_arbol(raiz):
    maxima = 0
    pila = [raiz]
    while pila:
        nodo = pila.pop()
        if nodo["profundidad"] > maxima:
            maxima = nodo["profundidad"]
        for hijo in nodo["hijos"]:
            pila.append(hijo)
    return maxima


def camino_de_estados(meta):
    estados = []
    operadores = []
    nodo = meta
    while nodo is not None:
        estados.append(nodo["estado"])
        operadores.append(nodo["operador"])
        nodo = nodo["padre"]
    estados.reverse()
    operadores.reverse()
    return estados, operadores


def mensaje_animacion(animacion):
    indice = animacion["indice"]
    total = len(animacion["estados"]) - 1
    if indice == total:
        return animacion["nombre"] + ": solución completa en " + str(total) + " pasos"
    if indice == 0:
        return animacion["nombre"] + ": solución de " + str(total) + " pasos"
    estado = animacion["estados"][indice]
    return ("Paso " + str(indice) + " de " + str(total) + ": " + animacion["operadores"][indice]
            + " | fertilizante " + str(estado[2]) + " | combustible " + str(estado[4]))


def ejecutar_busqueda(app):
    nombre = app["algoritmo"]
    clave_meta, clave_expandidos = CLAVES_RESULTADO[nombre]
    resultado = FUNCIONES[nombre](app["mundo"])
    meta = resultado[clave_meta]

    raiz = hallar_raiz(resultado, meta)
    if raiz is None:
        profundidad = resultado["profundidad"]
    else:
        profundidad = profundidad_del_arbol(raiz)

    costo = None
    if nombre in ALGORITMOS_CON_COSTO and meta is not None:
        costo = meta["costo"]

    app["reporte"] = {
        "expandidos": resultado[clave_expandidos],
        "profundidad": profundidad,
        "tiempo": resultado["tiempo"],
        "costo": costo,
    }

    if meta is None:
        app["mensaje"] = nombre + ": no se encontró una solución"
        return

    estados, operadores = camino_de_estados(meta)
    app["animacion"] = {
        "nombre": nombre,
        "estados": estados,
        "operadores": operadores,
        "indice": 0,
        "ultimo": pygame.time.get_ticks(),
    }
    app["mensaje"] = mensaje_animacion(app["animacion"])


def avanzar_animacion(app):
    animacion = app["animacion"]
    if animacion is None:
        return
    if animacion["indice"] >= len(animacion["estados"]) - 1:
        return
    ahora = pygame.time.get_ticks()
    if ahora - animacion["ultimo"] >= MS_POR_PASO:
        animacion["indice"] += 1
        animacion["ultimo"] = ahora
        app["mensaje"] = mensaje_animacion(animacion)


def vista_actual(app):
    animacion = app["animacion"]
    if animacion is None:
        return None
    indice = animacion["indice"]
    estado = animacion["estados"][indice]
    # El ultimo movimiento hecho sobre la avioneta deja el combustible en 0 al llegar,
    # asi que tambien se dibuja la mula si el robot tenia combustible antes de ese movimiento.
    en_mula = estado[4] > 0 or (indice > 0 and animacion["estados"][indice - 1][4] > 0)
    return {
        "fila": estado[0],
        "col": estado[1],
        "pendientes": estado[3],
        "en_mula": en_mula,
        "con_espada": estado[2] > 0,
        "mula_usada": estado[5],
    }


def busqueda_en_curso(app):
    # True mientras se calcula la búsqueda o mientras se reproduce su animación
    if app["buscar"]:
        return True
    animacion = app["animacion"]
    return animacion is not None and animacion["indice"] < len(animacion["estados"]) - 1


def procesar_evento(app, evento, regiones):
    if evento.type == pygame.QUIT:
        return False

    if evento.type == pygame.DROPFILE:
        if busqueda_en_curso(app):
            app["mensaje"] = "Espera a que termine la búsqueda para cargar otro mundo."
        else:
            cargar(app, evento.file)

    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        for rect, clase, valor in regiones:
            if rect.collidepoint(evento.pos):
                if clase == "tipo":
                    app["tipo"] = valor
                    app["algoritmo"] = ALGORITMOS[valor][0]
                elif clase == "algoritmo":
                    app["algoritmo"] = valor
                elif clase == "cargar":
                    app["mensaje"] = "Selecciona el archivo .txt del mundo..."
                    app["elegir"] = True
                elif clase == "iniciar":
                    if app["mundo"] is None:
                        app["mensaje"] = "Primero carga un mundo: pulsa «Cargar mundo» o arrastra el archivo .txt a la ventana"
                    elif app["algoritmo"] not in FUNCIONES:
                        app["mensaje"] = app["algoritmo"] + " aún no está implementado"
                    else:
                        app["animacion"] = None
                        app["reporte"] = None
                        app["mensaje"] = "Buscando con " + app["algoritmo"] + "..."
                        app["buscar"] = True
    return True


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("CampesinoBot")

    imagenes = cargar_imagenes()

    serif = "palatinolinotype,bookantiqua,georgia,cambria,timesnewroman,dejavuserif"
    gotica = "blackadderitc,oldenglishtext,palatinolinotype,georgia,dejavuserif"
    fuentes = {
        "titulo": crear_fuente(gotica, 46, True),
        "suave": crear_fuente(serif, 18),
        "seccion": crear_fuente(serif, 19, True),
        "normal": crear_fuente(serif, 18),
        "boton": crear_fuente(serif, 19, True),
        "chica": crear_fuente(serif, 17),
        "etiqueta": crear_fuente(serif, 14),
        "valor": crear_fuente(serif, 22, True),
    }

    app = {
        "mundo": None,
        "tipo": "No informada",
        "algoritmo": ALGORITMOS["No informada"][0],
        "mensaje": "Pulse «Cargar mundo» o arrastre un archivo .txt a la ventana.",
        "buscar": False,
        "elegir": False,
        "carpeta_archivos": None,
        "animacion": None,
        "reporte": None,
    }

    if len(sys.argv) > 1:
        cargar(app, sys.argv[1])

    reloj = pygame.time.Clock()
    regiones = []
    cursor_mano = False
    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if not procesar_evento(app, evento, regiones):
                corriendo = False

        pos_mouse = pygame.mouse.get_pos()

        avanzar_animacion(app)

        pantalla.fill(FONDO)
        dibujar_encabezado(pantalla, fuentes, imagenes, app["reporte"])
        if app["mundo"] is None:
            dibujar_mundo(pantalla, fuentes, None, imagenes, None)
        else:
            dibujar_mundo(pantalla, fuentes, app["mundo"]["matriz"], imagenes, vista_actual(app))
        regiones = dibujar_panel(pantalla, fuentes, app, pos_mouse, imagenes)
        dibujar_barra(pantalla, fuentes, app["mensaje"])

        encima = any(rect.collidepoint(pos_mouse) for rect, clase, valor in regiones)
        if encima != cursor_mano:
            cursor_mano = encima
            try:
                if encima:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                else:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass

        pygame.display.flip()

        if app["elegir"] and busqueda_en_curso(app):
            app["elegir"] = False
        if app["elegir"]:
            app["elegir"] = False
            carpeta = app["carpeta_archivos"]
            if carpeta is None:
                carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pruebas")
                if not os.path.isdir(carpeta):
                    carpeta = os.path.dirname(os.path.abspath(__file__))
            ruta, error = elegir_archivo(carpeta)
            # descarta los clics que se acumularon mientras estaba abierto el selector
            pygame.event.clear([pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP])
            if error is not None:
                app["mensaje"] = "Error: no se pudo abrir el selector de archivos, arrastra el .txt a la ventana"
            elif ruta == "":
                app["mensaje"] = "Carga cancelada."
            else:
                cargar(app, ruta)

        if app["buscar"]:
            app["buscar"] = False
            ejecutar_busqueda(app)
            # descarta los clics y archivos soltados mientras la ventana estaba ocupada buscando
            pygame.event.clear([pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.DROPFILE])

        reloj.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
