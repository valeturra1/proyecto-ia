# AgroBot — Proyecto 1 de Inteligencia Artificial (750022C)

Agente que recorre una cuadrícula de 10×10 para regar todos los cultivos secos usando **algoritmos de búsqueda no informada e informada**. El proyecto incluye la implementación de los algoritmos, una interfaz gráfica en `pygame` que anima la solución y un banco de pruebas que verifica automáticamente que los resultados sean correctos.

## Descripción del problema

El mundo es una matriz de **10×10** que se lee desde un archivo `.txt`. Cada casilla tiene un código:

| Código | Elemento | En la interfaz |
|:------:|----------|----------------|
| `0` | Casilla libre | Suelo libre |
| `1` | Obstáculo | Obstáculo |
| `2` | AgroBot (posición inicial) | Campesino |
| `3` | Cultivo seco | Bestia enojada (domada al regarla) |
| `4` | Depósito de fertilizante | Domador de bestias |
| `5` | Avioneta | Mula |

**Reglas del modelo** (definidas en `estado.py`):

- El AgroBot se mueve en 4 direcciones (`arriba`, `abajo`, `izquierda`, `derecha`) sin salirse del tablero ni atravesar obstáculos.
- Cada movimiento cuesta **1**.
- Al llegar al **depósito** recarga fertilizante hasta su capacidad máxima (**2 unidades**).
- Al llegar a un **cultivo seco con fertilizante** lo riega (gasta 1 unidad) y el cultivo deja de estar seco. Sin fertilizante solo pasa por encima.
- Al llegar a la **avioneta** (solo la primera vez) obtiene **30 unidades de combustible**. Mientras tenga combustible, cada movimiento cuesta **0.5** en lugar de 1.
- **Meta:** que no quede ningún cultivo seco.

**Estado del agente:** `(fila, columna, fertilizante, cultivos_secos, combustible, avioneta_usada)`

## Algoritmos implementados

Todos viven en `algoritmos.py` y devuelven un diccionario con `nodo_meta`, `expandidos`, `profundidad` y `tiempo`.

| Tipo | Algoritmo | Función | Estructura |
|------|-----------|---------|------------|
| No informada | Amplitud | `amplitud` | Cola (`deque`) |
| No informada | Costo uniforme | `coste_uniforme` | Cola de prioridad (`heapq`) |
| No informada | Profundidad evitando ciclos | `profundidad` | Pila |
| Informada | Avara | `busqueda_avara` | Cola de prioridad por `h(n)` |
| Informada | A* | `busqueda_a_estrella` | Cola de prioridad por `f(n) = g(n) + h(n)` |


**Orden de operadores:** arriba, abajo, izquierda, derecha.

### Evitar ciclos

- **Amplitud, Costo uniforme y Profundidad:** no se repite una celda dentro de la misma rama (`celda_en_historial`). El historial de la rama **se reinicia** cuando el agente llega al depósito (si recarga), a la avioneta (la primera vez) o riega un cultivo, ya que en esos casos volver a una celda previa sí es útil (`es_excepcion`).
- **Avara y A\*:** evitan repetidos a nivel de **estado completo** (conjunto de visitados / mejor costo conocido por estado).

## Estructura del repositorio

```
proyecto-ia/
├── algoritmos.py     # Los 5 algoritmos de búsqueda, heurística y reconstrucción del camino
├── arbol.py          # Creación de nodos del árbol de búsqueda
├── estado.py         # Modelo del problema: estado inicial, meta, operadores, costos y efectos
├── mundo.py          # Lectura y validación del archivo .txt del mundo
├── interfaz.py       # Interfaz gráfica (pygame) con animación de la solución
├── benchmark.py      # Banco de pruebas automático con oráculo independiente
├── pruebas/          # Tableros de prueba (.txt)
├── imagenes/         # Sprites usados por la interfaz (.png)
├── requirements.txt  # Dependencias de Python (pygame)
└── README.md
```

## Requisitos e instalación

- **Python 3.9+**
- **pygame** (interfaz gráfica)
- **tkinter** (selector de archivos; viene incluido con Python en Windows y macOS; en Linux: `sudo apt install python3-tk`)

### Pasos

1. **Clona el repositorio**

   ```bash
   git clone https://github.com/valeturra1/proyecto-ia.git
   cd proyecto-ia
   ```

2. **(Recomendado) Crea y activa un entorno virtual**

   ```bash
   # Windows (PowerShell / CMD)
   python -m venv venv
   venv\Scripts\activate

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instala las dependencias** con el archivo `Requirements.txt`

   ```bash
   pip install -r Requirements.txt
   ```

4. **Verifica la instalación**

   ```bash
   python -c "import pygame, tkinter; print('Todo listo')"
   ```

   Si `tkinter` falla en Linux, instálalo con `sudo apt install python3-tk`.

5. **Ejecuta el proyecto** (ver [Uso](#uso)):

   ```bash
   python interfaz.py
   ```

> Los algoritmos (`algoritmos.py`), el modelo y el `benchmark.py` solo usan la biblioteca estándar de Python; `pygame` únicamente es necesario para la interfaz.

## Uso

### 1. Interfaz gráfica

```bash
python interfaz.py                      # abre la ventana vacía
python interfaz.py pruebas/tablero.txt  # abre la ventana con un mundo ya cargado
```

1. Carga un mundo con el botón **«Cargar mundo»** o arrastrando el `.txt` a la ventana.
2. Elige el tipo de búsqueda (**No informada** / **Informada**) y el algoritmo.
3. Pulsa **«Iniciar búsqueda»**.
4. Se anima la solución paso a paso y en la parte superior aparece el reporte:
   - Nodos expandidos
   - Profundidad del árbol
   - Tiempo de cómputo
   - Costo de la solución (solo en Costo uniforme y A*)

### 2. Línea de comandos

Ejecuta los 5 algoritmos sobre un mundo e imprime las métricas y el camino:

```bash
python algoritmos.py pruebas/tablero.txt
```


## Formato del archivo de mundo

Archivo de texto con **10 filas** de **10 enteros** separados por espacios (valores del 0 al 5). Debe haber **exactamente 1 AgroBot, 1 depósito y 1 avioneta**. Ejemplo:

```
0 0 0 0 0 0 0 0 0 0
0 2 0 0 1 0 0 3 0 0
0 0 0 0 1 0 0 0 0 0
0 0 4 0 0 0 0 0 0 0
0 0 0 0 0 0 1 0 0 0
0 3 0 0 0 0 1 0 5 0
0 0 0 0 0 0 0 0 0 0
0 0 0 1 1 0 0 0 0 0
0 0 0 0 0 0 0 3 0 0
0 0 0 0 0 0 0 0 0 0
```

## Integrantes

- Samuel Banguero Ortega — 2418671
- Valeria Zamudio Arevalo — 2415210
- Juan José Rodríguez Lozano — 2419084
- Manuela Martinez Moncada — 2375458
