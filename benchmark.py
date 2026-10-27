#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark.py - Banco de pruebas de AgroBot (Proyecto 1, Inteligencia Artificial)
=================================================================================

Corre los algoritmos de busqueda del proyecto sobre cada .txt de la carpeta
`pruebas/` y comprueba que los resultados sean validos, coherentes y que
cumplan con el enunciado del proyecto y con lo visto en las diapositivas
(Tema 4: busqueda no informada, Tema 5: busqueda informada).

Uso (desde la carpeta del proyecto, donde viven mundo.py, algoritmos.py, ...):

    python benchmark.py                       # todas las pruebas, todos los algoritmos
    python benchmark.py -v                    # con notas y camino optimo de referencia
    python benchmark.py --solo tablero_04     # solo tableros cuyo nombre contenga el texto
    python benchmark.py --algoritmo "A*"      # solo algoritmos cuyo nombre contenga el texto
    python benchmark.py --timeout 120         # limite por ejecucion (segundos, def. 60)
    python benchmark.py --estricto            # los AVISOS tambien hacen fallar (codigo 1)
    python benchmark.py --csv resultados.csv  # guarda las metricas (para el informe)

Codigo de salida:  0 = todo bien (o solo avisos),  1 = hay FALLAS,
                   2 = no se pudo ejecutar el banco (sin carpeta pruebas, sin mundo.py...).

Que valida
----------
Para cada tablero:
  P1  El tablero es valido (10x10, valores 0-5, 1 AgroBot, 1 deposito, 1 avioneta)
      y `mundo.leer_mundo` lo lee igual que un parser independiente.
  M1  El modelo del proyecto (`estado.py`: estado inicial, es_meta, operadores,
      costos, efectos de deposito/avioneta/cultivo) coincide con un simulador
      independiente escrito aqui, comparando transiciones sobre los estados
      alcanzables.
  H1  La heuristica `algoritmos.heuristica` vale 0 en toda meta, es >= 0 y
      finita (diapositiva: "h(n) debe ser 0 cuando n es un nodo meta").
  H2  La heuristica es ADMISIBLE: h(n) <= costo real restante h*(n), comprobado en
      TODOS los estados alcanzables (h* por Dijkstra inverso). Tambien se informa si
      es consistente (no es obligatorio) y que tan informada es (h/h*).
  T1  El tablero cumple lo que dice su nombre (sin_solucion, sin_cultivos,
      dos_cultivos, avioneta_ahorra, ...), segun el oraculo.

Para cada algoritmo (Amplitud, Costo uniforme, Profundidad evitando ciclos,
Avara, A*), cada uno en un proceso aparte con limite de tiempo y de memoria:
  E1  Termina sin excepcion, sin pasar el limite de tiempo/memoria.
  S1  Encuentra solucion si existe (BFS exhaustivo sobre el espacio de estados) y
      no inventa una si no existe.
  V1-V4  La solucion es VALIDA al reproducirla en el simulador independiente:
      movimientos legales, termina con todos los cultivos tratados, el costo
      reportado = costo simulado, y los estados/costos de cada nodo coinciden.
  O1  Costo uniforme y A* devuelven el costo OPTIMO (Dijkstra sobre estados).
  O2  Amplitud devuelve la solucion de MENOR PROFUNDIDAD (BFS).
      Ningun algoritmo puede superar el optimo (sanidad).
  R1  Evitar ciclos (enunciado): en la ruta no se repite una celda salvo despues de
      llegar a avioneta, deposito o cultivo tratado con fertilizante.
  C1  Reporte coherente (enunciado): nodos expandidos, profundidad del arbol,
      tiempo de computo (y costo en Costo uniforme y A*); expandidos >= longitud
      de la solucion, profundidad >= longitud, expandidos = nodos con "orden", etc.

Supuestos del modelo (los mismos del codigo del proyecto):
  * Mover a una casilla cuesta 1; con avioneta con combustible cuesta 1/2.
    El movimiento que ENTRA a la casilla de la avioneta cuesta 1 y desde el
    siguiente el robot va montado durante 30 movimientos.
  * La avioneta se aborda una sola vez (despues de gastar el combustible no se
    vuelve a cargar).
  * Llegar al deposito siempre recarga a 2 unidades. Entrar a un cultivo seco con
    fertilizante lo trata; sin fertilizante el robot solo pasa por encima.

Lo que NO puede verificar un script (revisar a mano): la interfaz grafica y la
animacion, y el informe (explicacion de la heuristica y justificacion de su
admisibilidad). Solo se revisa de forma estatica que `interfaz.py` conecte las
opciones del menu con las funciones y muestre los campos del reporte.

No modifica ningun archivo del proyecto (solo escribe el CSV si se pide).
"""
from __future__ import annotations

import argparse
import csv
import heapq
import importlib
import math
import multiprocessing as mp
import os
import random
import re
import sys
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# ============================================================================
# Constantes del enunciado
# ============================================================================
TAMANO = 10
LIBRE, OBSTACULO, AGROBOT, CULTIVO, DEPOSITO, AVIONETA = range(6)
CAP_FERTILIZANTE = 2
COMBUSTIBLE = 30
DELTAS = {"arriba": (-1, 0), "abajo": (1, 0), "izquierda": (0, -1), "derecha": (0, 1)}
OPERADORES = tuple(DELTAS)
INF = float("inf")
EPS = 1e-9

# Costos en "medios" para trabajar con enteros exactos: 2 = normal, 1 = avioneta.
W_NORMAL, W_AVIONETA = 2, 1

# Algoritmos del enunciado. `candidatos`: (modulo, funcion) donde se espera hallarlos.
ALGORITMOS = [
    dict(nombre="Amplitud", candidatos=[("algoritmos", "amplitud")],
         optimo_costo=False, optimo_pasos=True, ciclos_celda=True, muestra_costo=False),
    dict(nombre="Costo uniforme",
         candidatos=[("algoritmos", "coste_uniforme"), ("algoritmos", "costo_uniforme")],
         optimo_costo=True, optimo_pasos=False, ciclos_celda=True, muestra_costo=True),
    dict(nombre="Profundidad evitando ciclos",
         candidatos=[("algoritmos", "profundidad"), ("algoritmos", "profundidad_evitando_ciclos"),
                     ("algoritmos", "busqueda_profundidad"), ("algoritmos", "dfs")],
         optimo_costo=False, optimo_pasos=False, ciclos_celda=True, muestra_costo=False),
    dict(nombre="Avara",
         candidatos=[("algoritmos", "busqueda_avara"), ("algoritmos", "avara")],
         optimo_costo=False, optimo_pasos=False, ciclos_celda=False, muestra_costo=False),
    dict(nombre="A*",
         candidatos=[("algoritmos", "busqueda_a_estrella"), ("algoritmos", "a_estrella")],
         optimo_costo=True, optimo_pasos=False, ciclos_celda=False, muestra_costo=True),
]
MODULOS_BUSQUEDA = ("algoritmos", "algoritmos")

CLAVES_META = ("nodo_meta", "meta")
CLAVES_EXPANDIDOS = ("expandidos", "nodos_expandidos")


# ============================================================================
# Salida con colores (opcional)
# ============================================================================
class Estilo:
    activo = False
    CODIGOS = {"verde": "32", "rojo": "31", "amarillo": "33", "gris": "90", "negrita": "1", "cian": "36"}

    @classmethod
    def c(cls, texto, color):
        if not cls.activo:
            return texto
        return f"\033[{cls.CODIGOS[color]}m{texto}\033[0m"


def color_estado(estado):
    return {"OK": "verde", "AVISO": "amarillo", "FALLA": "rojo", "N/D": "gris"}.get(estado, "gris")


def fmt_num(x, nd=2):
    if x is None:
        return "-"
    if isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
        return str(x)
    if isinstance(x, float):
        return f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return str(x)


def fmt_tiempo(s):
    if s is None:
        return "-"
    if s < 1:
        return f"{s * 1000:.1f} ms"
    return f"{s:.2f} s"


# ============================================================================
# Parser independiente del tablero
# ============================================================================
class TableroInvalido(Exception):
    pass


@dataclass
class Tablero:
    nombre: str
    matriz: list
    inicio: tuple
    deposito: tuple
    avioneta: tuple
    cultivos: tuple  # en orden de lectura (fila a fila), igual que mundo.leer_mundo


def parsear_tablero(ruta: Path) -> Tablero:
    try:
        texto = ruta.read_text(encoding="utf-8-sig")
    except OSError as e:
        raise TableroInvalido(f"no se pudo leer el archivo: {e}")
    filas = [ln.split() for ln in texto.splitlines() if ln.strip()]
    if len(filas) != TAMANO:
        raise TableroInvalido(f"se esperaban {TAMANO} filas y hay {len(filas)}")
    matriz = []
    for i, fila in enumerate(filas):
        if len(fila) != TAMANO:
            raise TableroInvalido(f"fila {i}: se esperaban {TAMANO} columnas y hay {len(fila)}")
        vals = []
        for j, tok in enumerate(fila):
            if not tok.isdigit() or int(tok) > 5:
                raise TableroInvalido(f"casilla ({i},{j}): valor invalido '{tok}' (debe ser 0-5)")
            vals.append(int(tok))
        matriz.append(vals)
    pos = {k: [] for k in range(6)}
    for i in range(TAMANO):
        for j in range(TAMANO):
            pos[matriz[i][j]].append((i, j))
    for cod, nom in ((AGROBOT, "AgroBot"), (DEPOSITO, "deposito"), (AVIONETA, "avioneta")):
        if len(pos[cod]) != 1:
            raise TableroInvalido(f"debe haber exactamente 1 {nom} y hay {len(pos[cod])}")
    return Tablero(ruta.name, matriz, pos[AGROBOT][0], pos[DEPOSITO][0], pos[AVIONETA][0],
                   tuple(pos[CULTIVO]))


# ============================================================================
# Simulador independiente
# estado = (fila, col, fertilizante, mascara_cultivos_secos, combustible, avioneta_usada)
# ============================================================================
class Simulador:
    def __init__(self, t: Tablero, avioneta_activa: bool = True):
        self.t = t
        self.activa = avioneta_activa
        self.idx_cultivo = {p: i for i, p in enumerate(t.cultivos)}
        self.obstaculo = [[v == OBSTACULO for v in fila] for fila in t.matriz]
        self._cult_cache = {}

    def inicial(self):
        return (self.t.inicio[0], self.t.inicio[1], 0, (1 << len(self.t.cultivos)) - 1, 0, False)

    @staticmethod
    def meta(s):
        return s[3] == 0

    def mover(self, s, op):
        """Devuelve (nuevo_estado, costo_en_medios, evento) o None si el movimiento es ilegal.
        `evento` = llego a deposito, a la avioneta o trato un cultivo (reinicia el historial de ciclos)."""
        dr, dc = DELTAS[op]
        r, c, f, m, fu, us = s
        nr, nc = r + dr, c + dc
        if not (0 <= nr < TAMANO and 0 <= nc < TAMANO) or self.obstaculo[nr][nc]:
            return None
        if fu > 0:
            w, fu = W_AVIONETA, fu - 1
        else:
            w = W_NORMAL
        evento = False
        p = (nr, nc)
        if p == self.t.deposito:
            f, evento = CAP_FERTILIZANTE, True
        elif p == self.t.avioneta and self.activa:
            evento = True
            if not us:
                fu, us = COMBUSTIBLE, True
        elif p in self.idx_cultivo:
            bit = 1 << self.idx_cultivo[p]
            if (m & bit) and f > 0:
                f, m, evento = f - 1, m & ~bit, True
        return (nr, nc, f, m, fu, us), w, evento

    def cultivos_de(self, m):
        if m not in self._cult_cache:
            self._cult_cache[m] = tuple(p for p, i in self.idx_cultivo.items() if m & (1 << i))
        return self._cult_cache[m]

    def a_repo(self, s):
        """Estado en el formato del proyecto (estado.py)."""
        return (s[0], s[1], s[2], self.cultivos_de(s[3]), s[4], s[5])

    def norm(self, s):
        return (s[0], s[1], s[2], frozenset(self.cultivos_de(s[3])), s[4], bool(s[5]))


def norm_repo(e):
    return (e[0], e[1], e[2], frozenset(e[3]), e[4], bool(e[5]))


def reproducir(sim: Simulador, ops):
    """Reproduce una lista de operadores. Devuelve dict con estados, costos acumulados (en
    medios), eventos y, si algo falla, `error`."""
    s = sim.inicial()
    estados, cum, eventos = [s], [0], [False]
    for k, op in enumerate(ops, 1):
        if op not in DELTAS:
            return dict(error=f"paso {k}: operador desconocido {op!r}", estados=estados, cum=cum, eventos=eventos)
        r = sim.mover(s, op)
        if r is None:
            return dict(error=f"paso {k}: '{op}' desde {(s[0], s[1])} sale del tablero o choca con un obstaculo",
                        estados=estados, cum=cum, eventos=eventos)
        s, w, ev = r
        estados.append(s)
        cum.append(cum[-1] + w)
        eventos.append(ev)
    return dict(error=None, estados=estados, cum=cum, eventos=eventos)


def primer_ciclo(estados, eventos):
    """Primera repeticion de celda sin reinicio de historial (misma regla que el proyecto:
    el historial arranca en la raiz y se reinicia, quedando solo la celda actual, al llegar a
    deposito, avioneta o al tratar un cultivo). Devuelve (paso, celda) o None."""
    hist = {(estados[0][0], estados[0][1])}
    for k in range(1, len(estados)):
        celda = (estados[k][0], estados[k][1])
        if celda in hist:
            return k, celda
        hist = {celda} if eventos[k] else hist | {celda}
    return None


# ============================================================================
# Oraculo: verdad por BFS / Dijkstra sobre el espacio de estados completo
# ============================================================================
class Oraculo:
    def __init__(self, sim: Simulador, max_estados: int):
        self.sim = sim
        self.truncado = False
        self.estados, self.prof, self.adj = [], [], []
        self._explorar(max_estados)
        self.metas = [i for i, s in enumerate(self.estados) if sim.meta(s)]
        self.min_pasos = min((self.prof[i] for i in self.metas), default=None)
        self.opt2, self.ops_optimas = self._dijkstra()
        self._hstar = None

    def _explorar(self, max_estados):
        sim = self.sim
        ini = sim.inicial()
        self.estados, self.prof, self.adj = [ini], [0], [None]
        idx = {ini: 0}
        cola = deque([0])
        while cola:
            i = cola.popleft()
            s = self.estados[i]
            if sim.meta(s):  # una meta no se expande (diapositivas)
                self.adj[i] = ()
                continue
            lista = []
            for op in OPERADORES:
                r = sim.mover(s, op)
                if r is None:
                    continue
                s2, w, _ = r
                j = idx.get(s2)
                if j is None:
                    if len(self.estados) >= max_estados:
                        self.truncado = True
                        continue
                    j = len(self.estados)
                    idx[s2] = j
                    self.estados.append(s2)
                    self.prof.append(self.prof[i] + 1)
                    self.adj.append(None)
                    cola.append(j)
                lista.append((j, w, op))
            self.adj[i] = lista
        for i, a in enumerate(self.adj):  # estados sin expandir por truncamiento
            if a is None:
                self.adj[i] = ()

    def _dijkstra(self):
        n = len(self.estados)
        dist = [INF] * n
        padre = [None] * n
        dist[0] = 0
        pq = [(0, 0)]
        while pq:
            d, i = heapq.heappop(pq)
            if d > dist[i]:
                continue
            if self.sim.meta(self.estados[i]):
                ops = []
                while padre[i] is not None:
                    i, op = padre[i]
                    ops.append(op)
                ops.reverse()
                return d, ops
            for j, w, op in self.adj[i]:
                nd = d + w
                if nd < dist[j]:
                    dist[j] = nd
                    padre[j] = (i, op)
                    heapq.heappush(pq, (nd, j))
        return None, None

    @property
    def solucionable(self):
        return self.opt2 is not None

    @property
    def optimo(self):
        return None if self.opt2 is None else self.opt2 / 2

    def hstar(self):
        """Costo real restante (en medios) desde cada estado alcanzable hasta la meta mas cercana."""
        if self._hstar is None:
            n = len(self.estados)
            radj = [[] for _ in range(n)]
            for i, lista in enumerate(self.adj):
                for j, w, _ in lista:
                    radj[j].append((i, w))
            h = [INF] * n
            pq = []
            for i in self.metas:
                h[i] = 0
                pq.append((0, i))
            heapq.heapify(pq)
            while pq:
                d, i = heapq.heappop(pq)
                if d > h[i]:
                    continue
                for p, w in radj[i]:
                    nd = d + w
                    if nd < h[p]:
                        h[p] = nd
                        heapq.heappush(pq, (nd, p))
            self._hstar = h
        return self._hstar


# ============================================================================
# Ejecucion aislada de cada algoritmo (proceso aparte, con limite de tiempo/memoria)
# ============================================================================
def _extraer(r):
    if not isinstance(r, dict):
        raise TypeError(f"el algoritmo devolvio {type(r).__name__}, se esperaba un dict")
    out = dict(claves=sorted(r.keys()), faltantes=[])
    meta, hay_meta_clave = None, False
    for k in CLAVES_META:
        if k in r:
            meta, hay_meta_clave = r[k], True
            break
    if not hay_meta_clave:
        out["faltantes"].append("nodo_meta/meta")
    for etiqueta, claves in (("expandidos", CLAVES_EXPANDIDOS), ("profundidad", ("profundidad",)),
                             ("tiempo", ("tiempo",))):
        for k in claves:
            if k in r:
                out[etiqueta] = r[k]
                break
        else:
            out["faltantes"].append("/".join(claves))
    out["costo_clave"] = r.get("costo")
    out["tiene_meta"] = meta is not None
    out["costo_nodo"] = meta.get("costo") if isinstance(meta, dict) else None

    camino, n = [], meta
    while isinstance(n, dict) and n.get("padre") is not None:
        camino.append((n.get("operador"), n.get("estado"), n.get("costo")))
        n = n["padre"]
    camino.reverse()
    out["camino"] = camino
    raiz = n if isinstance(n, dict) else r.get("raiz")
    out["raiz_estado"] = raiz.get("estado") if isinstance(raiz, dict) else None
    out["raiz_costo"] = raiz.get("costo") if isinstance(raiz, dict) else None

    # recorrido iterativo del arbol (para comparar contra los contadores reportados)
    if isinstance(raiz, dict) and "hijos" in raiz:
        creados = con_orden = prof_max = 0
        pila = [raiz]
        while pila:
            nodo = pila.pop()
            creados += 1
            if nodo.get("orden") is not None:
                con_orden += 1
            prof_max = max(prof_max, nodo.get("profundidad", 0) or 0)
            pila.extend(nodo.get("hijos", ()))
        out["arbol"] = dict(creados=creados, con_orden=con_orden, prof_max=prof_max)
    return out


def _trabajador(modulo, funcion, ruta, limite_mb, conn):
    try:
        if limite_mb:
            try:
                import resource
                lim = int(limite_mb) * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
            except Exception:
                pass
        mod = importlib.import_module(modulo)
        from mundo import leer_mundo
        mundo = leer_mundo(ruta)
        fn = getattr(mod, funcion)
        t0 = time.perf_counter()
        r = fn(mundo)
        t_fn = time.perf_counter() - t0
        salida = _extraer(r)
        salida["t_fn"] = t_fn
        conn.send(("ok", salida))
    except MemoryError:
        conn.send(("memoria", "MemoryError (se agoto el limite de memoria)"))
    except BaseException as e:  # noqa: BLE001
        tb = traceback.format_exc().strip().splitlines()
        conn.send(("error", f"{type(e).__name__}: {e}  [{tb[-3].strip() if len(tb) >= 3 else ''}]"))
    finally:
        conn.close()


def ejecutar_aislado(modulo, funcion, ruta, timeout, limite_mb):
    padre, hijo = mp.Pipe(duplex=False)
    p = mp.Process(target=_trabajador, args=(modulo, funcion, str(ruta), limite_mb, hijo), daemon=True)
    t0 = time.perf_counter()
    p.start()
    hijo.close()
    resultado = ("timeout", f"supero el limite de {timeout:g} s")
    try:
        if padre.poll(timeout):
            try:
                resultado = padre.recv()
            except EOFError:
                resultado = ("error", "el proceso termino de forma inesperada (¿memoria agotada?)")
    finally:
        p.join(0.5)
        if p.is_alive():
            p.terminate()
            p.join(2)
        padre.close()
    return resultado, time.perf_counter() - t0


# ============================================================================
# Estructuras de resultado
# ============================================================================
@dataclass
class Fila:
    nombre: str
    estado: str = "OK"
    costo: object = None
    pasos: object = None
    expandidos: object = None
    profundidad: object = None
    tiempo: object = None
    resuelto: object = None
    fallas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    notas: list = field(default_factory=list)

    def falla(self, cod, msg):
        self.fallas.append(f"{cod}: {msg}")

    def aviso(self, cod, msg):
        self.avisos.append(f"{cod}: {msg}")

    def nota(self, msg):
        self.notas.append(msg)

    def cerrar(self):
        self.estado = "FALLA" if self.fallas else ("AVISO" if self.avisos else "OK")


@dataclass
class ResTablero:
    nombre: str
    info: dict = field(default_factory=dict)
    fallas: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    notas: list = field(default_factory=list)
    filas: list = field(default_factory=list)


# ============================================================================
# Verificaciones a nivel de tablero
# ============================================================================
def comparar_parsers(t: Tablero, mundo):
    difs = []
    if mundo["matriz"] != t.matriz:
        difs.append("matriz")
    if tuple(mundo["inicio"]) != t.inicio:
        difs.append(f"inicio ({mundo['inicio']} vs {t.inicio})")
    if tuple(mundo["deposito"]) != t.deposito:
        difs.append("deposito")
    if tuple(mundo["avioneta"]) != t.avioneta:
        difs.append("avioneta")
    if set(map(tuple, mundo["cultivos"])) != set(t.cultivos):
        difs.append("cultivos")
    return difs


def verificar_modelo(sim, orac, mundo, estado_mod, muestra, semilla=12345):
    """M1: compara estado.py con el simulador sobre estados alcanzables."""
    n = len(orac.estados)
    if n <= muestra:
        indices = list(range(n))
    else:
        indices = [0] + random.Random(semilla).sample(range(1, n), muestra - 1)
    errores, ejemplos = 0, []

    def reg(msg):
        nonlocal errores
        errores += 1
        if len(ejemplos) < 3:
            ejemplos.append(msg)

    try:
        ini_repo = estado_mod.estado_inicial(mundo)
        if norm_repo(ini_repo) != sim.norm(sim.inicial()):
            reg(f"estado_inicial {ini_repo} != esperado {sim.a_repo(sim.inicial())} "
                "(el robot debe iniciar sin fertilizante, con 0 combustible y todos los cultivos secos)")
        for i in indices:
            s = orac.estados[i]
            e = sim.a_repo(s)
            if bool(estado_mod.es_meta(e)) != sim.meta(s):
                reg(f"es_meta({e}) = {estado_mod.es_meta(e)}, esperado {sim.meta(s)}")
            esperado = {}
            for op in OPERADORES:
                r = sim.mover(s, op)
                if r is not None:
                    esperado[op] = (sim.norm(r[0]), r[1] / 2)
            obtenido = {}
            for op, nuevo, costo in estado_mod.movimientos_y_efectos(e, mundo):
                obtenido[op] = (norm_repo(nuevo), costo)
            for op in sorted(set(esperado) | set(obtenido)):
                if op not in obtenido:
                    reg(f"desde {e}: falta el operador '{op}'")
                elif op not in esperado:
                    reg(f"desde {e}: '{op}' no deberia ser posible (obstaculo/borde)")
                elif obtenido[op][0] != esperado[op][0]:
                    reg(f"desde {e} con '{op}': estado {sorted(obtenido[op][0], key=str)[:6]}... "
                        f"!= esperado {esperado[op][0][:3]}...")
                elif abs(obtenido[op][1] - esperado[op][1]) > EPS:
                    reg(f"desde {e} con '{op}': costo {obtenido[op][1]} != esperado {esperado[op][1]}")
    except Exception as ex:  # noqa: BLE001
        return dict(error=f"{type(ex).__name__}: {ex}", comparados=0, errores=0, ejemplos=[])
    return dict(error=None, comparados=len(indices), errores=errores, ejemplos=ejemplos)


def verificar_heuristica(sim, orac, heur):
    """H1/H2: valor en meta, no negatividad, admisibilidad y consistencia sobre todos los estados."""
    hs = orac.hstar()
    n = len(orac.estados)
    hv = [None] * n
    inval, meta_mal, no_adm = [], [], []
    suma_ratio, cuenta_ratio = 0.0, 0
    for i, s in enumerate(orac.estados):
        e = sim.a_repo(s)
        try:
            h = heur(e)
        except Exception as ex:  # noqa: BLE001
            return dict(error=f"la heuristica lanzo {type(ex).__name__}: {ex} en el estado {e}")
        if isinstance(h, bool) or not isinstance(h, (int, float)) or math.isnan(h) or math.isinf(h) or h < 0:
            inval.append((e, h))
            continue
        hv[i] = h
        if sim.meta(s) and abs(h) > EPS:
            meta_mal.append((e, h))
        real = hs[i] / 2 if hs[i] < INF else INF
        if real < INF:
            if h > real + EPS:
                no_adm.append((e, h, real))
            if real > 0:
                suma_ratio += h / real
                cuenta_ratio += 1
    incons, ej_inc = 0, []
    for i, lista in enumerate(orac.adj):
        if hv[i] is None:
            continue
        for j, w, _ in lista:
            if hv[j] is not None and hv[i] > w / 2 + hv[j] + EPS:
                incons += 1
                if len(ej_inc) < 2:
                    ej_inc.append((sim.a_repo(orac.estados[i]), hv[i], w / 2, hv[j]))
    h0 = hv[0]
    real0 = hs[0] / 2 if hs[0] < INF else None
    return dict(error=None, invalidos=inval, meta_mal=meta_mal, no_adm=no_adm, inconsistentes=incons,
                ej_inconsistente=ej_inc, h_inicial=h0, real_inicial=real0,
                razon_media=(suma_ratio / cuenta_ratio) if cuenta_ratio else None,
                estados=n)


PALABRAS_NUM = {"un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}


def verificar_nombre(t: Tablero, orac: Oraculo, opt_sin_avioneta, orac_sin_truncado):
    """T1: el tablero hace lo que dice su nombre. Devuelve lista de avisos."""
    avisos = []
    nombre = t.nombre.lower()
    n = len(t.cultivos)
    if "sin_solucion" in nombre and orac.solucionable:
        avisos.append(f"el nombre dice 'sin solucion' pero existe solucion (costo optimo {fmt_num(orac.optimo)})")
    if "sin_cultivos" in nombre and n != 0:
        avisos.append(f"el nombre dice 'sin cultivos' pero hay {n}")
    # solo palabras (un, dos, ...): los numeros iniciales como "tablero_08_" son indices, no cantidades
    m = re.search(r"_(uno|un|dos|tres|cuatro|cinco|seis)_cultivos?", nombre)
    if m:
        esperado = PALABRAS_NUM[m.group(1)]
        if esperado != n:
            avisos.append(f"el nombre dice {esperado} cultivo(s) y el tablero tiene {n}")
    m = re.search(r"_(uno|un|dos|tres|cuatro)_recargas?", nombre)
    if m:
        esperado = PALABRAS_NUM[m.group(1)]
        necesarias = math.ceil(n / CAP_FERTILIZANTE)
        if necesarias != esperado:
            avisos.append(f"el nombre dice {esperado} recarga(s); con {n} cultivos y capacidad "
                          f"{CAP_FERTILIZANTE} se necesitan {necesarias}")
    if "avioneta_ahorra" in nombre and not orac_sin_truncado:
        if orac.solucionable and not (opt_sin_avioneta is None or orac.optimo < opt_sin_avioneta - EPS):
            avisos.append(f"el nombre dice que la avioneta ahorra, pero el optimo con avioneta "
                          f"({fmt_num(orac.optimo)}) no mejora al optimo sin ella ({fmt_num(opt_sin_avioneta)})")
    if "avioneta_no_conviene" in nombre and not orac_sin_truncado:
        if orac.solucionable and (opt_sin_avioneta is None or abs(orac.optimo - opt_sin_avioneta) > EPS):
            avisos.append(f"el nombre dice que la avioneta no conviene, pero el optimo con avioneta es "
                          f"{fmt_num(orac.optimo)} y sin ella {fmt_num(opt_sin_avioneta)}")
    if "cultivo_junto_a_deposito" in nombre:
        if not any(abs(c[0] - t.deposito[0]) + abs(c[1] - t.deposito[1]) == 1 for c in t.cultivos):
            avisos.append("el nombre dice 'cultivo junto a deposito' pero ningun cultivo es adyacente al deposito")
    return avisos


# ============================================================================
# Verificaciones por algoritmo
# ============================================================================
def evaluar_algoritmo(spec, res_ejec, wall, t: Tablero, sim: Simulador, orac: Oraculo, timeout) -> Fila:
    f = Fila(spec["nombre"])
    tipo, payload = res_ejec
    if tipo != "ok":
        f.falla("E1", {"timeout": "TIEMPO: ", "memoria": "MEMORIA: ", "error": "EXCEPCION: "}[tipo] + str(payload))
        f.resuelto = None
        f.cerrar()
        return f
    d = payload
    n_cultivos = len(t.cultivos)

    # --- campos del reporte (enunciado) ---------------------------------------------
    if d["faltantes"]:
        f.falla("E2", "el resultado no trae: " + ", ".join(d["faltantes"]))
    f.expandidos, f.profundidad, f.tiempo = d.get("expandidos"), d.get("profundidad"), d.get("tiempo")
    resuelto = d["tiene_meta"]
    f.resuelto = resuelto
    camino = d["camino"]
    f.pasos = len(camino) if resuelto else None

    # --- S1: existencia de solucion ---------------------------------------------------
    if not orac.truncado:
        if resuelto and not orac.solucionable:
            f.falla("S1", "devolvio una solucion pero el tablero NO tiene solucion (BFS exhaustivo)")
        elif not resuelto and orac.solucionable:
            f.falla("S1", f"no encontro solucion, pero existe una con costo optimo {fmt_num(orac.optimo)}")
    elif not resuelto:
        f.aviso("S1", "no se pudo confirmar si hay solucion (oraculo truncado por --max-estados)")

    # --- V1..V4: validez de la solucion ------------------------------------------------
    costo_sim = None
    if resuelto:
        ops = [c[0] for c in camino]
        rep = reproducir(sim, ops)
        if rep["error"]:
            f.falla("V1", "camino invalido: " + rep["error"])
        else:
            if not sim.meta(rep["estados"][-1]):
                faltan = [p for p in sim.cultivos_de(rep["estados"][-1][3])]
                f.falla("V2", f"el camino NO deja todos los cultivos tratados; siguen secos: {faltan}")
            costo_sim = rep["cum"][-1] / 2
            f.costo = costo_sim
            # costo reportado
            costo_rep = d["costo_clave"] if d["costo_clave"] is not None else d["costo_nodo"]
            if costo_rep is None:
                if spec["muestra_costo"]:
                    f.falla("C2", "no hay costo de la solucion (el enunciado lo exige en este algoritmo)")
            elif not isinstance(costo_rep, (int, float)) or abs(costo_rep - costo_sim) > EPS:
                f.falla("V3", f"costo reportado {costo_rep} != costo simulado {fmt_num(costo_sim)}")
            if d["costo_clave"] is not None and d["costo_nodo"] is not None \
                    and abs(d["costo_clave"] - d["costo_nodo"]) > EPS:
                f.falla("V3", f"resultado['costo']={d['costo_clave']} != costo del nodo meta={d['costo_nodo']}")
            # V4: estados y costos acumulados nodo a nodo
            if d["raiz_estado"] is not None and len(d["raiz_estado"]) == 6 \
                    and norm_repo(d["raiz_estado"]) != sim.norm(sim.inicial()):
                f.falla("V4", f"estado de la raiz {d['raiz_estado']} != estado inicial esperado")
            for k, (op, est, cst) in enumerate(camino, 1):
                s = rep["estados"][k]
                if est is None or (est[0], est[1]) != (s[0], s[1]):
                    f.falla("V4", f"paso {k}: el nodo dice posicion {None if est is None else (est[0], est[1])}, "
                                  f"el simulador {(s[0], s[1])}")
                    break
                if len(est) == 6 and norm_repo(est) != sim.norm(s):
                    f.falla("V4", f"paso {k} ({op}): estado del nodo {est} != simulador {sim.a_repo(s)}")
                    break
                if isinstance(cst, (int, float)) and abs(cst - rep["cum"][k] / 2) > EPS:
                    f.falla("V4", f"paso {k}: costo acumulado del nodo {cst} != simulador {rep['cum'][k] / 2}")
                    break
            # R1: evitar ciclos
            ciclo = primer_ciclo(rep["estados"], rep["eventos"])
            if ciclo:
                msg = (f"la ruta repite la celda {ciclo[1]} en el paso {ciclo[0]} sin haber pasado por "
                       "avioneta, deposito o cultivo tratado en medio (el enunciado pide evitar ciclos)")
                if spec["ciclos_celda"]:
                    f.falla("R1", msg)
                else:
                    f.aviso("R1", msg + ". Este algoritmo evita repetidos por ESTADO completo, no por celda")

    # --- O1/O2: optimalidad y sanidad ------------------------------------------------
    if resuelto and costo_sim is not None and not orac.truncado and orac.solucionable:
        if costo_sim < orac.optimo - EPS:
            f.falla("O1", f"costo {fmt_num(costo_sim)} MENOR que el optimo {fmt_num(orac.optimo)}: "
                          "imposible, el simulador y el algoritmo no coinciden en las reglas")
        elif spec["optimo_costo"] and costo_sim > orac.optimo + EPS:
            extra = (" Con una heuristica admisible A* debe ser optimo (Tema 5)." if spec["nombre"] == "A*"
                     else " Costo uniforme debe devolver la solucion mas barata (Tema 4).")
            f.falla("O1", f"costo {fmt_num(costo_sim)} > optimo {fmt_num(orac.optimo)}." + extra)
        if f.pasos is not None and f.pasos < orac.min_pasos:
            f.falla("O2", f"{f.pasos} pasos < minimo posible {orac.min_pasos}: imposible")
        elif spec["optimo_pasos"] and f.pasos > orac.min_pasos:
            f.falla("O2", f"{f.pasos} pasos > minimo {orac.min_pasos}. Amplitud debe hallar la solucion "
                          "menos profunda (Tema 4)")
        if not spec["optimo_costo"] and costo_sim > orac.optimo + EPS:
            f.nota(f"no optimo (costo {fmt_num(costo_sim)} vs {fmt_num(orac.optimo)}): esperado en este algoritmo")

    # --- C1: coherencia del reporte --------------------------------------------------
    exp, prof, tmp = d.get("expandidos"), d.get("profundidad"), d.get("tiempo")
    if "expandidos" in d:
        if isinstance(exp, bool) or not isinstance(exp, int) or exp < 1:
            f.falla("C1", f"nodos expandidos = {exp!r}: debe ser un entero >= 1 (al menos se expande la raiz)")
        elif resuelto and exp < len(camino) + 1:
            f.falla("C1", f"expandidos ({exp}) < longitud de su propia solucion + 1 ({len(camino) + 1})")
    if "profundidad" in d:
        if isinstance(prof, bool) or not isinstance(prof, int) or prof < 0:
            f.falla("C1", f"profundidad = {prof!r}: debe ser un entero >= 0")
        elif resuelto and prof < len(camino):
            f.falla("C1", f"profundidad del arbol ({prof}) < longitud de la solucion ({len(camino)})")
    if "tiempo" in d:
        if isinstance(tmp, bool) or not isinstance(tmp, (int, float)) or math.isnan(tmp) or tmp < 0:
            f.falla("C1", f"tiempo = {tmp!r}: debe ser un numero >= 0 (segundos)")
        else:
            t_fn = d["t_fn"]
            if tmp > t_fn + 0.05:
                f.aviso("C1", f"tiempo reportado {fmt_tiempo(tmp)} > tiempo real de la llamada {fmt_tiempo(t_fn)} "
                              "(¿unidades distintas?)")
            elif t_fn > 0.2 and tmp < 0.5 * t_fn - 0.02:
                f.aviso("C1", f"tiempo reportado {fmt_tiempo(tmp)} muy inferior al real {fmt_tiempo(t_fn)} "
                              "(¿se esta midiendo solo una parte?)")
    arb = d.get("arbol")
    if arb:
        if isinstance(exp, int) and arb["con_orden"] != exp:
            f.aviso("C1", f"{arb['con_orden']} nodos del arbol tienen 'orden' pero se reportan {exp} expandidos")
        if isinstance(exp, int) and arb["creados"] < exp:
            f.falla("C1", f"el arbol tiene {arb['creados']} nodos pero se reportan {exp} expandidos")
        if isinstance(prof, int) and arb["prof_max"] != prof:
            f.aviso("C1", f"resultado['profundidad']={prof} pero la profundidad real del arbol es "
                          f"{arb['prof_max']} (la interfaz recalcula la del arbol)")
    elif resuelto and d.get("raiz_estado") is not None:
        f.nota("los nodos no guardan 'hijos': no se pudo contrastar el tamano del arbol")

    # Raiz = meta (sin cultivos secos)
    if n_cultivos == 0:
        if resuelto and (len(camino) != 0 or (costo_sim not in (None, 0))):
            f.falla("C1", "sin cultivos secos la raiz ya es meta: la solucion debe ser vacia con costo 0")
        if isinstance(exp, int) and exp != 1:
            f.aviso("C1", f"con la raiz como meta se esperaba 1 nodo expandido, se reportan {exp}")
        if isinstance(prof, int) and prof != 0:
            f.aviso("C1", f"con la raiz como meta se esperaba profundidad 0, se reporta {prof}")

    if not resuelto:
        if d["costo_clave"] is not None:
            f.falla("C1", f"sin solucion pero reporta costo {d['costo_clave']}")
    f.cerrar()
    return f


def notas_cruzadas(filas, orac):
    """Comparaciones entre algoritmos del mismo tablero (informativas)."""
    notas = []
    por = {f.nombre: f for f in filas if f.resuelto}
    ucs, ast = por.get("Costo uniforme"), por.get("A*")
    if ucs and ast and isinstance(ucs.expandidos, int) and isinstance(ast.expandidos, int):
        if ast.expandidos > ucs.expandidos:
            notas.append(f"A* expandio mas nodos ({ast.expandidos}) que Costo uniforme ({ucs.expandidos}); con una "
                         "buena heuristica deberia ser menos (los dos manejan repetidos de forma distinta)")
    return notas


# ============================================================================
# Verificacion estatica de interfaz.py
# ============================================================================
def revisar_interfaz(raiz: Path):
    avisos, notas = [], []
    ruta = raiz / "interfaz.py"
    if not ruta.exists():
        return ["no se encontro interfaz.py"], notas
    txt = ruta.read_text(encoding="utf-8", errors="replace")
    low = txt.lower()
    for etiqueta in ("No informada", "Informada", "Amplitud", "Costo uniforme",
                     "Profundidad evitando ciclos", "Avara", "A*"):
        if f'"{etiqueta}"' not in txt and f"'{etiqueta}'" not in txt:
            avisos.append(f"interfaz.py: falta la opcion de menu '{etiqueta}' (enunciado)")
    for etiqueta in ("Amplitud", "Costo uniforme", "Profundidad evitando ciclos", "Avara", "A*"):
        if not re.search(r'["\']' + re.escape(etiqueta) + r'["\']\s*:', txt):
            avisos.append(f"interfaz.py: la opcion '{etiqueta}' no esta conectada a ninguna funcion "
                          "(no aparece como clave de FUNCIONES/CLAVES_RESULTADO)")
    for campo, clave in (("nodos expandidos", "nodos expandidos"), ("profundidad", "profundidad"),
                         ("tiempo", "tiempo"), ("costo", "costo")):
        if clave not in low:
            avisos.append(f"interfaz.py: no se ve el campo de reporte '{campo}' (enunciado)")
    informes = [p.name for p in raiz.iterdir()
                if p.is_file() and "informe" in p.name.lower() and p.suffix.lower() in (".pdf", ".docx", ".doc", ".md", ".txt")]
    if informes:
        notas.append("informe encontrado: " + ", ".join(informes) + " (revisar a mano heuristica y admisibilidad)")
    else:
        notas.append("no se encontro un archivo de informe en la carpeta del proyecto (el enunciado pide explicar "
                     "la heuristica y justificar su admisibilidad); revisar a mano")
    return avisos, notas


# ============================================================================
# Orquestacion por tablero
# ============================================================================
def descubrir_algoritmos(filtro):
    """Devuelve (lista de (spec, (modulo, funcion) | None), errores de importacion)."""
    modulos, errores = {}, {}
    for nombre in MODULOS_BUSQUEDA:
        try:
            modulos[nombre] = importlib.import_module(nombre)
        except Exception as e:  # noqa: BLE001
            errores[nombre] = f"{type(e).__name__}: {e}"
    resultado = []
    for spec in ALGORITMOS:
        if filtro and filtro.lower() not in spec["nombre"].lower():
            continue
        hallado = None
        for mod, fn in spec["candidatos"]:
            if mod in modulos and callable(getattr(modulos[mod], fn, None)):
                hallado = (mod, fn)
                break
        if hallado is None and spec["nombre"] == "Profundidad evitando ciclos":
            for mod, m in modulos.items():  # busqueda flexible por nombre
                for nombre_f in dir(m):
                    if "profundidad" in nombre_f.lower() and callable(getattr(m, nombre_f)) \
                            and not nombre_f.startswith("_") and "arbol" not in nombre_f.lower():
                        hallado = (mod, nombre_f)
                        break
                if hallado:
                    break
        resultado.append((spec, hallado))
    return resultado, errores, modulos


def evaluar_tablero(ruta: Path, algs, modulos, args) -> ResTablero:
    rt = ResTablero(ruta.name)
    try:
        t = parsear_tablero(ruta)
    except TableroInvalido as e:
        rt.fallas.append(f"P1: tablero invalido: {e}")
        return rt
    sim = Simulador(t)
    t0 = time.perf_counter()
    orac = Oraculo(sim, args.max_estados)
    orac_sin = Oraculo(Simulador(t, avioneta_activa=False), args.max_estados)
    opt_sin = orac_sin.optimo
    rt.info = dict(cultivos=len(t.cultivos), estados=len(orac.estados), solucionable=orac.solucionable,
                   optimo=orac.optimo, min_pasos=orac.min_pasos, opt_sin_avioneta=opt_sin,
                   t_oraculo=time.perf_counter() - t0, truncado=orac.truncado or orac_sin.truncado,
                   ops_optimas=orac.ops_optimas)
    if rt.info["truncado"]:
        rt.avisos.append(f"el oraculo se trunco en {args.max_estados} estados: las verdades pueden ser parciales "
                         "(sube --max-estados)")

    # P1: lectura del proyecto vs parser independiente
    mundo = None
    try:
        from mundo import leer_mundo
        mundo = leer_mundo(str(ruta))
        difs = comparar_parsers(t, mundo)
        if difs:
            rt.fallas.append("P1: mundo.leer_mundo difiere del parser independiente en: " + ", ".join(difs))
    except Exception as e:  # noqa: BLE001
        rt.fallas.append(f"P1: mundo.leer_mundo no pudo leer un tablero valido: {type(e).__name__}: {e}")

    # T1: coherencia con el nombre
    for a in verificar_nombre(t, orac, opt_sin, orac_sin.truncado):
        rt.avisos.append("T1: " + a)

    # M1: modelo estado.py
    estado_mod = modulos.get("estado") or _importar_opcional("estado")
    if mundo is not None and estado_mod is not None and all(
            hasattr(estado_mod, n) for n in ("estado_inicial", "es_meta", "movimientos_y_efectos")):
        m1 = verificar_modelo(sim, orac, mundo, estado_mod, args.muestra)
        rt.info["m1"] = m1
        if m1["error"]:
            rt.avisos.append(f"M1: no se pudo comparar el modelo: {m1['error']}")
        elif m1["errores"]:
            rt.fallas.append(f"M1: estado.py difiere del simulador en {m1['errores']} transicion(es). Ejemplos: "
                             + " | ".join(m1["ejemplos"]))
    else:
        rt.avisos.append("M1: no se encontro estado.estado_inicial/es_meta/movimientos_y_efectos; modelo sin verificar")

    # H1/H2: heuristica
    bi = modulos.get("algoritmos")
    heur = getattr(bi, "heuristica", None) if bi else None
    if heur is None:
        rt.avisos.append("H: no se encontro algoritmos.heuristica; heuristica sin verificar")
    elif not orac.truncado:
        h = verificar_heuristica(sim, orac, heur)
        rt.info["h"] = h
        if h["error"]:
            rt.fallas.append("H1: " + h["error"])
        else:
            if h["invalidos"]:
                e, v = h["invalidos"][0]
                rt.fallas.append(f"H1: heuristica con valor invalido ({v!r}) en {len(h['invalidos'])} estado(s), "
                                 f"p. ej. {e} (debe ser un numero finito >= 0)")
            if h["meta_mal"]:
                e, v = h["meta_mal"][0]
                rt.fallas.append(f"H1: h(meta) != 0 en {len(h['meta_mal'])} estado(s) meta, p. ej. h({e}) = {v} "
                                 "(Tema 5: h(n) debe ser 0 en un nodo meta)")
            if h["no_adm"]:
                e, v, real = h["no_adm"][0]
                rt.fallas.append(f"H2: heuristica NO admisible en {len(h['no_adm'])} de {h['estados']} estados; p. ej. "
                                 f"h({e}) = {fmt_num(v)} > costo real restante {fmt_num(real)} (Tema 5)")
            if h["inconsistentes"]:
                rt.notas.append(f"heuristica no consistente en {h['inconsistentes']} arco(s) (no es obligatorio; "
                                "A* sigue siendo optimo si reabre nodos, como hace el proyecto)")

    # Algoritmos
    for spec, hallado in algs:
        if hallado is None:
            f = Fila(spec["nombre"], estado="N/D")
            rt.filas.append(f)
            continue
        res, wall = ejecutar_aislado(hallado[0], hallado[1], ruta, args.timeout, args.memoria)
        rt.filas.append(evaluar_algoritmo(spec, res, wall, t, sim, orac, args.timeout))
    rt.notas.extend(notas_cruzadas(rt.filas, orac))
    return rt


def _importar_opcional(nombre):
    try:
        return importlib.import_module(nombre)
    except Exception:  # noqa: BLE001
        return None


# ============================================================================
# Presentacion
# ============================================================================
def estado_tablero(rt: ResTablero):
    if rt.fallas or any(f.estado == "FALLA" for f in rt.filas):
        return "FALLA"
    if rt.avisos or any(f.estado == "AVISO" for f in rt.filas):
        return "AVISO"
    return "OK"


def imprimir_tablero(rt: ResTablero, verbose: bool):
    est = estado_tablero(rt)
    print()
    print(Estilo.c(f"=== {rt.nombre} ", "negrita") + Estilo.c(f"[{est}]", color_estado(est)))
    i = rt.info
    if i:
        sol = (f"optimo={fmt_num(i['optimo'])}  pasos_min={i['min_pasos']}" if i["solucionable"] else "SIN SOLUCION")
        sin = "" if not i["solucionable"] else f"  optimo_sin_avioneta={fmt_num(i['opt_sin_avioneta'])}"
        print(f"    cultivos={i['cultivos']}  {sol}{sin}  estados_alcanzables={i['estados']}")
        m1, h = i.get("m1"), i.get("h")
        partes = []
        if m1 and not m1["error"]:
            partes.append(f"modelo: {'OK' if not m1['errores'] else 'FALLA'} ({m1['comparados']} estados comparados)")
        if h and not h["error"]:
            adm = "admisible" if not h["no_adm"] else "NO admisible"
            con = "consistente" if not h["inconsistentes"] else "no consistente"
            extra = ""
            if h["real_inicial"] not in (None, 0):
                extra = f", h(inicial)/h*(inicial)={fmt_num(h['h_inicial'])}/{fmt_num(h['real_inicial'])}"
                if h["razon_media"] is not None:
                    extra += f", h/h* medio={h['razon_media']:.2f}"
            partes.append(f"heuristica: {adm}, {con}{extra}")
        if partes:
            print("    " + " | ".join(partes))
        if verbose and i["ops_optimas"] is not None:
            ops = "".join({"arriba": "↑", "abajo": "↓", "izquierda": "←", "derecha": "→"}[o] for o in i["ops_optimas"])
            print(f"    camino optimo de referencia: {ops if ops else '(vacio)'}")
    for m in rt.fallas:
        print("    " + Estilo.c("[FALLA] ", "rojo") + m)
    for m in rt.avisos:
        print("    " + Estilo.c("[AVISO] ", "amarillo") + m)

    if rt.filas:
        enc = ("Algoritmo", "Estado", "Costo", "vs optimo", "Pasos", "Expandidos", "Prof.", "Tiempo")
        filas = []
        for f in rt.filas:
            if f.estado == "N/D":
                filas.append((f.nombre, "N/D", "no implementado", "", "", "", "", ""))
                continue
            if f.resuelto is False:
                costo, gap = "sin sol.", ""
            else:
                costo = fmt_num(f.costo)
                gap = ""
                if f.costo is not None and i and i.get("optimo") is not None:
                    d = f.costo - i["optimo"]
                    gap = "=" if abs(d) <= EPS else f"{d:+g}"
            filas.append((f.nombre, f.estado, costo, gap, fmt_num(f.pasos), fmt_num(f.expandidos),
                          fmt_num(f.profundidad), fmt_tiempo(f.tiempo if isinstance(f.tiempo, (int, float)) else None)))
        anchos = [max(len(str(x[k])) for x in filas + [enc]) for k in range(len(enc))]
        linea = "    " + "  ".join(str(h).ljust(anchos[k]) if k < 2 else str(h).rjust(anchos[k]) for k, h in enumerate(enc))
        print(Estilo.c(linea, "gris"))
        for fila in filas:
            celdas = []
            for k, v in enumerate(fila):
                v = str(v)
                celdas.append(v.ljust(anchos[k]) if k < 2 else v.rjust(anchos[k]))
            celdas[1] = Estilo.c(celdas[1], color_estado(fila[1]))
            print("    " + "  ".join(celdas))
        for f in rt.filas:
            for m in f.fallas:
                print("    " + Estilo.c("[FALLA] ", "rojo") + f"{f.nombre} · {m}")
            for m in f.avisos:
                print("    " + Estilo.c("[AVISO] ", "amarillo") + f"{f.nombre} · {m}")
            if verbose:
                for m in f.notas:
                    print("    " + Estilo.c("[nota]  ", "gris") + f"{f.nombre} · {m}")
    if verbose:
        for m in rt.notas:
            print("    " + Estilo.c("[nota]  ", "gris") + m)


def imprimir_resumen(resultados, algs, globales_fallas, globales_avisos, globales_notas, estricto):
    print()
    print(Estilo.c("=" * 78, "negrita"))
    print(Estilo.c("RESUMEN", "negrita"))
    print(Estilo.c("=" * 78, "negrita"))
    nombres = [s["nombre"] for s, _ in algs]
    ancho = max([len(n) for n in nombres] + [9])
    print("    " + "Algoritmo".ljust(ancho) + "    OK  AVISO  FALLA   N/D")
    total = {"OK": 0, "AVISO": 0, "FALLA": 0, "N/D": 0}
    for n in nombres:
        c = {"OK": 0, "AVISO": 0, "FALLA": 0, "N/D": 0}
        for rt in resultados:
            for f in rt.filas:
                if f.nombre == n:
                    c[f.estado] += 1
        for k in c:
            total[k] += c[k]
        print("    " + n.ljust(ancho) + "".join(
            Estilo.c(str(c[k]).rjust(6 if k != "N/D" else 6), color_estado(k) if c[k] else "gris")
            for k in ("OK", "AVISO", "FALLA", "N/D")))
    tabs = {"OK": 0, "AVISO": 0, "FALLA": 0}
    for rt in resultados:
        tabs[estado_tablero(rt)] += 1
    n_fallas_tab = sum(len(rt.fallas) for rt in resultados)
    n_avisos_tab = sum(len(rt.avisos) for rt in resultados)
    print()
    print(f"    Tableros: {len(resultados)}  (OK {tabs['OK']}, AVISO {tabs['AVISO']}, FALLA {tabs['FALLA']})")
    print(f"    Verificaciones de tablero (lectura, modelo, heuristica, nombre): "
          f"{n_fallas_tab} falla(s), {n_avisos_tab} aviso(s)")
    print(f"    Ejecuciones de algoritmos: {sum(total.values()) - total['N/D']}  "
          f"(OK {total['OK']}, AVISO {total['AVISO']}, FALLA {total['FALLA']})")
    if globales_fallas or globales_avisos or globales_notas:
        print()
        for m in globales_fallas:
            print("    " + Estilo.c("[FALLA] ", "rojo") + m)
        for m in globales_avisos:
            print("    " + Estilo.c("[AVISO] ", "amarillo") + m)
        for m in globales_notas:
            print("    " + Estilo.c("[nota]  ", "gris") + m)

    hay_fallas = bool(globales_fallas) or n_fallas_tab > 0 or total["FALLA"] > 0
    hay_avisos = bool(globales_avisos) or n_avisos_tab > 0 or total["AVISO"] > 0
    codigo = 1 if (hay_fallas or (estricto and hay_avisos)) else 0
    print()
    if hay_fallas:
        veredicto = Estilo.c("REPROBADO", "rojo") + " - hay FALLAS que corregir"
    elif hay_avisos:
        if estricto:
            veredicto = Estilo.c("REPROBADO (modo estricto)", "rojo") + " - hay AVISOS sin resolver"
        else:
            veredicto = Estilo.c("APROBADO CON AVISOS", "amarillo") + " - revisa los [AVISO]"
    else:
        veredicto = Estilo.c("APROBADO", "verde")
    print(f"    RESULTADO: {veredicto}      (codigo de salida: {codigo})")
    return codigo


def guardar_csv(ruta, resultados):
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["tablero", "algoritmo", "estado", "resuelto", "costo", "optimo", "pasos", "expandidos",
                    "profundidad", "tiempo_s", "mensajes"])
        for rt in resultados:
            opt = rt.info.get("optimo") if rt.info else None
            for f in rt.filas:
                w.writerow([rt.nombre, f.nombre, f.estado, f.resuelto, f.costo, opt, f.pasos, f.expandidos,
                            f.profundidad, f.tiempo, " | ".join(f.fallas + f.avisos)])


# ============================================================================
# main
# ============================================================================
def parsear_args(argv):
    p = argparse.ArgumentParser(description="Banco de pruebas de AgroBot (ver el encabezado del archivo).")
    p.add_argument("--pruebas", default=None, help="carpeta con los .txt (por defecto ./pruebas junto a este script)")
    p.add_argument("--solo", default=None, help="solo tableros cuyo nombre contenga este texto")
    p.add_argument("--algoritmo", default=None, help="solo algoritmos cuyo nombre contenga este texto")
    p.add_argument("--timeout", type=float, default=60.0, help="segundos maximos por ejecucion (def. 60)")
    p.add_argument("--memoria", type=int, default=2048, help="MB maximos por ejecucion, solo Linux/macOS (def. 2048)")
    p.add_argument("--max-estados", type=int, default=1_500_000, help="tope de estados del oraculo")
    p.add_argument("--muestra", type=int, default=5000, help="estados a comparar en la verificacion del modelo (M1)")
    p.add_argument("--estricto", action="store_true", help="los AVISOS tambien provocan codigo de salida 1")
    p.add_argument("-v", "--verbose", action="store_true", help="muestra notas y el camino optimo de referencia")
    p.add_argument("--csv", default=None, help="guarda las metricas en este archivo CSV")
    p.add_argument("--sin-color", action="store_true", help="sin colores ANSI")
    return p.parse_args(argv)


def main(argv=None):
    args = parsear_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    Estilo.activo = sys.stdout.isatty() and not args.sin_color and "NO_COLOR" not in os.environ
    if Estilo.activo and os.name == "nt":
        os.system("")  # habilita secuencias ANSI en consolas de Windows 10+

    raiz = Path(__file__).resolve().parent
    sys.path.insert(0, str(raiz))
    carpeta = Path(args.pruebas) if args.pruebas else raiz / "pruebas"
    if not carpeta.is_dir():
        print(f"ERROR: no existe la carpeta de pruebas: {carpeta}", file=sys.stderr)
        return 2
    archivos = sorted(carpeta.glob("*.txt"))
    if args.solo:
        archivos = [a for a in archivos if args.solo.lower() in a.name.lower()]
    if not archivos:
        print(f"ERROR: no hay archivos .txt en {carpeta}" + (f" que contengan '{args.solo}'" if args.solo else ""),
              file=sys.stderr)
        return 2
    try:
        importlib.import_module("mundo")
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: no se pudo importar mundo.py desde {raiz}: {e}", file=sys.stderr)
        return 2

    algs, errores_import, modulos = descubrir_algoritmos(args.algoritmo)
    if not algs:
        print(f"ERROR: ningun algoritmo coincide con '{args.algoritmo}'", file=sys.stderr)
        return 2
    estado_mod = _importar_opcional("estado")
    if estado_mod:
        modulos["estado"] = estado_mod

    globales_fallas, globales_avisos, globales_notas = [], [], []
    for mod, msg in errores_import.items():
        globales_fallas.append(f"no se pudo importar {mod}.py: {msg}")
    for spec, hallado in algs:
        if hallado is None and not (spec["candidatos"][0][0] in errores_import):
            texto = (f"'{spec['nombre']}' no esta implementado (el enunciado lo exige; se buscaron: "
                     + ", ".join(f"{m}.{fn}" for m, fn in spec["candidatos"]) + ")")
            (globales_fallas if args.estricto else globales_avisos).append(texto)
    a_interfaz, n_interfaz = revisar_interfaz(raiz)
    if args.algoritmo is None:
        globales_avisos.extend(a_interfaz)
    globales_notas.extend(n_interfaz)

    print(Estilo.c("AgroBot · benchmark de busqueda", "negrita"))
    print(f"Proyecto: {raiz}")
    print(f"Pruebas : {carpeta}  ({len(archivos)} tablero(s))   timeout={args.timeout:g}s   "
          f"algoritmos: " + ", ".join(s["nombre"] + ("" if h else " (N/D)") for s, h in algs))

    resultados = []
    t0 = time.perf_counter()
    for ruta in archivos:
        rt = evaluar_tablero(ruta, algs, modulos, args)
        resultados.append(rt)
        imprimir_tablero(rt, args.verbose)
        sys.stdout.flush()
    print(f"\nTiempo total del banco: {time.perf_counter() - t0:.1f} s")

    if args.csv:
        guardar_csv(args.csv, resultados)
        print(f"CSV guardado en {args.csv}")
    return imprimir_resumen(resultados, algs, globales_fallas, globales_avisos, globales_notas, args.estricto)


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())