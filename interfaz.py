"""Interfaz de AgroBot con pygame: muestra el mundo inicial y permite elegir el algoritmo."""
import sys
import pygame

from mundo import (leer_mundo, TAMANO, LIBRE, OBSTACULO, AGROBOT,
                   CULTIVO_SECO, DEPOSITO, AVIONETA)

# ---------- Medidas de la ventana ----------
TAM_CASILLA = 50
LADO_MUNDO = TAMANO * TAM_CASILLA
MARGEN = 24
ALTO_ENCABEZADO = 78
X_MUNDO = MARGEN
Y_MUNDO = ALTO_ENCABEZADO + 14
X_DIVISOR = X_MUNDO + LADO_MUNDO + 8 + 20
X_PANEL = X_DIVISOR + 20
ANCHO_PANEL = 320
Y_BARRA = Y_MUNDO + LADO_MUNDO + 8 + 14
ALTO_BARRA = 34
ANCHO_VENTANA = X_PANEL + ANCHO_PANEL + MARGEN
ALTO_VENTANA = Y_BARRA + ALTO_BARRA + 8

# ---------- Paleta ----------
FONDO = (225, 231, 221)          # gris verdoso fresco
FONDO_HOVER = (212, 220, 207)
TINTA = (33, 44, 36)             # texto principal
TINTA_SUAVE = (96, 108, 98)      # texto secundario
LINEA = (193, 202, 189)          # divisores finos
LINEA_FUERTE = (150, 163, 148)   # bordes de controles
BLANCO = (255, 255, 255)
HOJA = (38, 84, 56)              # verde profundo: lo activo
HOJA_HOVER = (52, 110, 74)
GRIS_BOTON = (176, 185, 173)
ROJO = (184, 56, 44)

SUELO = (219, 195, 154)          # tierra arenosa
SURCO = (200, 173, 130)          # líneas de arado
MADERA = (118, 88, 58)           # cerca de la parcela
VACIO = (234, 238, 230)
PAD = (226, 227, 218)            # base de concreto (depósito y avioneta)
PAD_BORDE = (178, 182, 170)
PIEDRA = (118, 124, 128)
PIEDRA_CLARA = (156, 162, 164)
PIEDRA_OSCURA = (80, 86, 90)
PAJA = (214, 168, 58)            # cultivo seco
PAJA_OSCURA = (142, 100, 32)
TALLO = (112, 80, 42)
ROBOT = (36, 112, 156)
ROBOT_OSCURO = (22, 70, 104)
BARRIL = (52, 140, 84)
BARRIL_OSCURO = (28, 88, 52)
CIELO = (120, 176, 220)

# Algoritmos que pide el enunciado, agrupados por tipo de búsqueda
ALGORITMOS = {
    "No informada": ["Amplitud", "Costo uniforme", "Profundidad evitando ciclos"],
    "Informada": ["Avara", "A*"],
}

LEYENDA = [
    (AGROBOT, "AgroBot"),
    (CULTIVO_SECO, "Cultivo seco"),
    (DEPOSITO, "Depósito"),
    (AVIONETA, "Avioneta"),
    (OBSTACULO, "Obstáculo"),
    (LIBRE, "Suelo libre"),
]


# =====================================================================
#  Utilidades
# =====================================================================
def crear_fuente(nombres, tamano, negrita=False):
    return pygame.font.SysFont(nombres, tamano, bold=negrita)


def recortar(texto, fuente, ancho):
    """Acorta el texto con '...' si no cabe en el ancho dado."""
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


def punto(rect, fx, fy):
    """Punto dentro de rect, dado como fracción del ancho y del alto."""
    return (rect.left + int(fx * rect.width), rect.top + int(fy * rect.height))


def caja(rect, fx, fy, fw, fh):
    """Rectángulo dentro de rect, dado como fracciones."""
    return pygame.Rect(rect.left + int(fx * rect.width), rect.top + int(fy * rect.height),
                       max(1, int(fw * rect.width)), max(1, int(fh * rect.height)))


def dibujar_rect_punteado(pantalla, rect, color):
    paso = 14
    for x in range(rect.left, rect.right, paso):
        fin = min(x + 8, rect.right)
        pygame.draw.line(pantalla, color, (x, rect.top), (fin, rect.top), 2)
        pygame.draw.line(pantalla, color, (x, rect.bottom - 1), (fin, rect.bottom - 1), 2)
    for y in range(rect.top, rect.bottom, paso):
        fin = min(y + 8, rect.bottom)
        pygame.draw.line(pantalla, color, (rect.left, y), (rect.left, fin), 2)
        pygame.draw.line(pantalla, color, (rect.right - 1, y), (rect.right - 1, fin), 2)


# =====================================================================
#  Íconos de las casillas (se dibujan con formas, sin imágenes)
# =====================================================================
def icono_robot(pantalla, rect):
    w = rect.width
    pygame.draw.line(pantalla, TINTA, punto(rect, 0.5, 0.26), punto(rect, 0.5, 0.1), 2)
    pygame.draw.circle(pantalla, ROJO, punto(rect, 0.5, 0.1), max(2, int(w * 0.06)))
    cuerpo = caja(rect, 0.2, 0.24, 0.6, 0.5)
    radio = max(2, int(w * 0.12))
    pygame.draw.rect(pantalla, ROBOT, cuerpo, border_radius=radio)
    pygame.draw.rect(pantalla, ROBOT_OSCURO, cuerpo, 2, border_radius=radio)
    for fx in (0.38, 0.62):
        pygame.draw.circle(pantalla, BLANCO, punto(rect, fx, 0.45), max(2, int(w * 0.09)))
        pygame.draw.circle(pantalla, TINTA, punto(rect, fx, 0.45), max(1, int(w * 0.04)))
    pygame.draw.line(pantalla, BLANCO, punto(rect, 0.4, 0.64), punto(rect, 0.6, 0.64), 2)
    for fx in (0.24, 0.6):
        pygame.draw.rect(pantalla, TINTA, caja(rect, fx, 0.8, 0.16, 0.1), border_radius=2)


def icono_cultivo(pantalla, rect):
    w = rect.width
    # grietas en la tierra seca
    pygame.draw.line(pantalla, PAJA_OSCURA, punto(rect, 0.18, 0.9), punto(rect, 0.4, 0.86), 1)
    pygame.draw.line(pantalla, PAJA_OSCURA, punto(rect, 0.6, 0.86), punto(rect, 0.84, 0.9), 1)
    # tallo
    pygame.draw.line(pantalla, TALLO, punto(rect, 0.5, 0.88), punto(rect, 0.52, 0.36), max(2, int(w * 0.06)))
    # hojas caídas
    hoja_izq = [punto(rect, 0.5, 0.64), punto(rect, 0.18, 0.56), punto(rect, 0.14, 0.76)]
    hoja_der = [punto(rect, 0.52, 0.52), punto(rect, 0.84, 0.44), punto(rect, 0.88, 0.64)]
    for hoja in (hoja_izq, hoja_der):
        pygame.draw.polygon(pantalla, PAJA, hoja)
        pygame.draw.polygon(pantalla, PAJA_OSCURA, hoja, 1)
    # espiga seca
    espiga = caja(rect, 0.42, 0.1, 0.2, 0.32)
    pygame.draw.ellipse(pantalla, PAJA, espiga)
    pygame.draw.ellipse(pantalla, PAJA_OSCURA, espiga, 1)


def icono_deposito(pantalla, rect):
    w = rect.width
    barril = caja(rect, 0.25, 0.14, 0.5, 0.72)
    radio = max(2, int(w * 0.1))
    pygame.draw.rect(pantalla, BARRIL, barril, border_radius=radio)
    pygame.draw.rect(pantalla, BARRIL_OSCURO, barril, 2, border_radius=radio)
    for fy in (0.28, 0.72):
        pygame.draw.line(pantalla, BARRIL_OSCURO, punto(rect, 0.25, fy), punto(rect, 0.75, fy), 2)
    # gota de fertilizante
    pygame.draw.polygon(pantalla, BLANCO, [punto(rect, 0.5, 0.36), punto(rect, 0.42, 0.52),
                                           punto(rect, 0.58, 0.52)])
    pygame.draw.circle(pantalla, BLANCO, punto(rect, 0.5, 0.55), max(2, int(w * 0.085)))


def icono_avioneta(pantalla, rect):
    alas = caja(rect, 0.1, 0.34, 0.8, 0.15)
    cola = caja(rect, 0.34, 0.74, 0.32, 0.09)
    fuselaje = caja(rect, 0.4, 0.1, 0.2, 0.8)
    pygame.draw.rect(pantalla, ROJO, alas, border_radius=3)
    pygame.draw.rect(pantalla, ROJO, cola, border_radius=2)
    pygame.draw.ellipse(pantalla, BLANCO, fuselaje)
    pygame.draw.ellipse(pantalla, TINTA_SUAVE, fuselaje, 2)
    pygame.draw.ellipse(pantalla, CIELO, caja(rect, 0.44, 0.2, 0.12, 0.16))
    pygame.draw.line(pantalla, TINTA, punto(rect, 0.32, 0.1), punto(rect, 0.68, 0.1), 3)


def icono_obstaculo(pantalla, rect):
    sombra = [punto(rect, 0.16, 0.8), punto(rect, 0.9, 0.8), punto(rect, 0.86, 0.9), punto(rect, 0.2, 0.9)]
    pygame.draw.polygon(pantalla, SURCO, sombra)
    roca = [punto(rect, 0.12, 0.66), punto(rect, 0.2, 0.34), punto(rect, 0.42, 0.16),
            punto(rect, 0.68, 0.2), punto(rect, 0.88, 0.44), punto(rect, 0.9, 0.72),
            punto(rect, 0.7, 0.84), punto(rect, 0.28, 0.84)]
    pygame.draw.polygon(pantalla, PIEDRA, roca)
    brillo = [punto(rect, 0.26, 0.44), punto(rect, 0.4, 0.28), punto(rect, 0.58, 0.3),
              punto(rect, 0.44, 0.5)]
    pygame.draw.polygon(pantalla, PIEDRA_CLARA, brillo)
    pygame.draw.polygon(pantalla, PIEDRA_OSCURA, roca, 2)


ICONOS = {
    OBSTACULO: icono_obstaculo,
    AGROBOT: icono_robot,
    CULTIVO_SECO: icono_cultivo,
    DEPOSITO: icono_deposito,
    AVIONETA: icono_avioneta,
}


def dibujar_casilla(pantalla, rect, codigo):
    """Dibuja una casilla: suelo arado (o base de concreto) y el ícono encima."""
    if codigo == DEPOSITO or codigo == AVIONETA:
        pygame.draw.rect(pantalla, PAD, rect)
        pygame.draw.rect(pantalla, PAD_BORDE, rect, 1)
    else:
        pygame.draw.rect(pantalla, SUELO, rect)
        for fy in (0.25, 0.5, 0.75):     # surcos: quedan alineados entre casillas
            y = rect.top + int(fy * rect.height)
            pygame.draw.line(pantalla, SURCO, (rect.left, y), (rect.right - 1, y), 2)
    if codigo in ICONOS:
        ICONOS[codigo](pantalla, rect)


# =====================================================================
#  Zonas de la ventana
# =====================================================================
def dibujar_encabezado(pantalla, fuentes):
    icono_robot(pantalla, pygame.Rect(MARGEN, 14, 44, 44))
    dibujar_texto(pantalla, fuentes["titulo"], "AgroBot", MARGEN + 56, 8, HOJA)
    dibujar_texto(pantalla, fuentes["suave"], "Búsqueda para fertilizar cultivos secos",
                  MARGEN + 58, 48, TINTA_SUAVE)
    pygame.draw.line(pantalla, LINEA, (0, ALTO_ENCABEZADO - 1), (ANCHO_VENTANA, ALTO_ENCABEZADO - 1), 1)


def dibujar_mundo(pantalla, fuentes, matriz):
    """Dibuja la parcela casilla por casilla (o un recuadro de espera si no hay mundo)."""
    mundo = pygame.Rect(X_MUNDO, Y_MUNDO, LADO_MUNDO, LADO_MUNDO)
    marco = mundo.inflate(16, 16)

    if matriz is None:
        pygame.draw.rect(pantalla, VACIO, marco, border_radius=8)
        dibujar_rect_punteado(pantalla, marco, LINEA_FUERTE)
        cx = marco.centerx
        cy = marco.centery - 30
        pygame.draw.rect(pantalla, LINEA_FUERTE, (cx - 6, cy - 26, 12, 28))           # flecha: cuerpo
        pygame.draw.polygon(pantalla, LINEA_FUERTE, [(cx - 18, cy), (cx + 18, cy), (cx, cy + 20)])
        pygame.draw.line(pantalla, LINEA_FUERTE, (cx - 24, cy + 32), (cx + 24, cy + 32), 3)
        dibujar_texto_centrado(pantalla, fuentes["seccion"], "Suelte aquí el archivo .txt del mundo", cx, cy + 52)
        dibujar_texto_centrado(pantalla, fuentes["suave"], "o ábralo con: python interfaz.py mundo.txt",
                               cx, cy + 82, TINTA_SUAVE)
        return

    pygame.draw.rect(pantalla, MADERA, marco, border_radius=8)
    for i in range(TAMANO):
        for j in range(TAMANO):
            rect = pygame.Rect(X_MUNDO + j * TAM_CASILLA, Y_MUNDO + i * TAM_CASILLA,
                               TAM_CASILLA, TAM_CASILLA)
            dibujar_casilla(pantalla, rect, matriz[i][j])


def dibujar_segmento(pantalla, fuente, rect, texto, activo, hover):
    if activo:
        pygame.draw.rect(pantalla, HOJA, rect, border_radius=6)
        color = BLANCO
    else:
        pygame.draw.rect(pantalla, FONDO_HOVER if hover else FONDO, rect, border_radius=6)
        pygame.draw.rect(pantalla, LINEA_FUERTE, rect, 1, border_radius=6)
        color = TINTA
    imagen = fuente.render(texto, True, color)
    pantalla.blit(imagen, imagen.get_rect(center=rect.center))


def dibujar_opcion(pantalla, fuente, rect, texto, activa, hover):
    if hover and not activa:
        pygame.draw.rect(pantalla, FONDO_HOVER, rect, border_radius=6)
    centro = (rect.left + 16, rect.centery)
    if activa:
        pygame.draw.circle(pantalla, HOJA, centro, 8, 2)
        pygame.draw.circle(pantalla, HOJA, centro, 4)
    else:
        pygame.draw.circle(pantalla, LINEA_FUERTE, centro, 8, 2)
    texto = recortar(texto, fuente, rect.width - 40)
    imagen = fuente.render(texto, True, HOJA if activa else TINTA)
    pantalla.blit(imagen, (rect.left + 34, rect.centery - imagen.get_height() // 2))


def dibujar_boton_principal(pantalla, fuente, rect, texto, habilitado, hover):
    if not habilitado:
        color = GRIS_BOTON
    elif hover:
        color = HOJA_HOVER
    else:
        color = HOJA
    pygame.draw.rect(pantalla, color, rect, border_radius=6)
    imagen = fuente.render(texto, True, BLANCO)
    total = 12 + 10 + imagen.get_width()
    x0 = rect.centerx - total // 2
    pygame.draw.polygon(pantalla, BLANCO, [(x0, rect.centery - 8), (x0, rect.centery + 8),
                                           (x0 + 12, rect.centery)])
    pantalla.blit(imagen, (x0 + 22, rect.centery - imagen.get_height() // 2))


def dibujar_panel(pantalla, fuentes, app, pos_mouse):
    """Dibuja el selector y devuelve las zonas donde se puede hacer clic."""
    regiones = []   # cada elemento: (rect, clase, valor)
    x = X_PANEL
    ancho = ANCHO_PANEL
    y = Y_MUNDO

    pygame.draw.line(pantalla, LINEA, (X_DIVISOR, Y_MUNDO), (X_DIVISOR, Y_MUNDO + LADO_MUNDO), 1)

    # ---- Tipo de búsqueda
    dibujar_texto(pantalla, fuentes["seccion"], "Tipo de búsqueda", x, y)
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
    pygame.draw.line(pantalla, LINEA, (x, y), (x + ancho, y), 1)
    y += 16

    # ---- Algoritmo (se reservan 3 filas para que nada se mueva al cambiar de tipo)
    dibujar_texto(pantalla, fuentes["seccion"], "Algoritmo", x, y)
    y += 26
    inicio_opciones = y
    for nombre in ALGORITMOS[app["tipo"]]:
        rect = pygame.Rect(x, y, ancho, 34)
        dibujar_opcion(pantalla, fuentes["normal"], rect, nombre,
                       app["algoritmo"] == nombre, rect.collidepoint(pos_mouse))
        regiones.append((rect, "algoritmo", nombre))
        y += 38
    y = inicio_opciones + 3 * 38 + 6
    pygame.draw.line(pantalla, LINEA, (x, y), (x + ancho, y), 1)
    y += 16

    # ---- Botón principal
    rect = pygame.Rect(x, y, ancho, 44)
    dibujar_boton_principal(pantalla, fuentes["boton"], rect, "Iniciar búsqueda",
                            app["mundo"] is not None, rect.collidepoint(pos_mouse))
    regiones.append((rect, "iniciar", None))
    y += 44 + 18
    pygame.draw.line(pantalla, LINEA, (x, y), (x + ancho, y), 1)
    y += 16

    # ---- Leyenda: dos columnas de tres
    dibujar_texto(pantalla, fuentes["seccion"], "Leyenda", x, y)
    y += 28
    ancho_columna = ancho // 2
    for k, (codigo, nombre) in enumerate(LEYENDA):
        cx = x + (k % 2) * ancho_columna
        cy = y + (k // 2) * 34
        muestra = pygame.Rect(cx, cy, 30, 30)
        dibujar_casilla(pantalla, muestra, codigo)
        pygame.draw.rect(pantalla, LINEA_FUERTE, muestra, 1)
        dibujar_texto(pantalla, fuentes["chica"], nombre, cx + 38, cy + 7)

    return regiones


def dibujar_barra(pantalla, fuentes, mensaje):
    pygame.draw.line(pantalla, LINEA, (X_MUNDO - 8, Y_BARRA - 7),
                     (ANCHO_VENTANA - MARGEN + 8, Y_BARRA - 7), 1)
    if mensaje.startswith("Error"):
        color_punto = ROJO
    else:
        color_punto = HOJA
    pygame.draw.circle(pantalla, color_punto, (X_MUNDO + 6, Y_BARRA + ALTO_BARRA // 2 - 2), 5)
    texto = recortar(mensaje, fuentes["normal"], ANCHO_VENTANA - 2 * MARGEN - 24)
    dibujar_texto(pantalla, fuentes["normal"], texto, X_MUNDO + 20, Y_BARRA + 5,
                  ROJO if mensaje.startswith("Error") else TINTA)



def cargar(app, ruta):
    try:
        app["mundo"] = leer_mundo(ruta)
    except (ValueError, OSError) as error:
        app["mensaje"] = "Error: " + str(error)
        return
    app["mensaje"] = "Mundo cargado: " + ruta


def procesar_evento(app, evento, regiones):
    if evento.type == pygame.QUIT:
        return False

    if evento.type == pygame.DROPFILE:     # se arrastró un archivo a la ventana
        cargar(app, evento.file)

    if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
        for rect, clase, valor in regiones:
            if rect.collidepoint(evento.pos):
                if clase == "tipo":
                    app["tipo"] = valor
                    app["algoritmo"] = ALGORITMOS[valor][0]
                elif clase == "algoritmo":
                    app["algoritmo"] = valor
                elif clase == "iniciar":
                    if app["mundo"] is None:
                        app["mensaje"] = "Primero cargue un mundo: arrastre el archivo .txt a la ventana."
                    else:
                        # Aquí se llamará al algoritmo elegido cuando esté implementado.
                        app["mensaje"] = "Seleccionado: " + app["algoritmo"] + " (aún no implementado)"
    return True


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("AgroBot")

    sans = "segoeui,helveticaneue,arial,dejavusans"
    serif = "georgia,cambria,timesnewroman,dejavuserif"
    fuentes = {
        "titulo": crear_fuente(serif, 38, True),
        "suave": crear_fuente(sans, 17),
        "seccion": crear_fuente(sans, 18, True),
        "normal": crear_fuente(sans, 17),
        "boton": crear_fuente(sans, 18, True),
        "chica": crear_fuente(sans, 15),
    }

    app = {
        "mundo": None,                                   # el mundo cargado
        "tipo": "No informada",                          # tipo de búsqueda elegido
        "algoritmo": ALGORITMOS["No informada"][0],      # algoritmo elegido
        "mensaje": "Arrastre un archivo .txt a la ventana para cargar el mundo.",
    }

    # Si se pasa un archivo al ejecutar (python interfaz.py mundo.txt), se carga solo
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

        pantalla.fill(FONDO)
        dibujar_encabezado(pantalla, fuentes)
        if app["mundo"] is None:
            dibujar_mundo(pantalla, fuentes, None)
        else:
            dibujar_mundo(pantalla, fuentes, app["mundo"]["matriz"])
        regiones = dibujar_panel(pantalla, fuentes, app, pos_mouse)
        dibujar_barra(pantalla, fuentes, app["mensaje"])

        # Cursor de mano al pasar sobre un botón
        encima = False
        for rect, clase, valor in regiones:
            if rect.collidepoint(pos_mouse):
                encima = True
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
        reloj.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()