#!/usr/bin/env python3
"""Genera el catálogo A–Z, la tabla periódica, la línea de tiempo y el banner del Atlas de Pruebas .NET.

Fuentes únicas de verdad:
  - data/equivalencias.csv   conceptos y su sintaxis en xUnit.net, NUnit y MSTest
  - data/hitos.csv           hitos históricos de los tres frameworks y de la plataforma
Salidas:
  - docs/17-catalogo-a-z.md
  - assets/atlas-pruebas-tabla-periodica.svg
  - assets/atlas-pruebas-linea-de-tiempo.svg
  - assets/atlas-pruebas-banner.svg

Uso:  python3 tools/generar_atlas.py   (solo biblioteca estándar, Python 3.9+)
"""
from __future__ import annotations

import csv
import unicodedata
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
EQUIVALENCIAS = RAIZ / "data" / "equivalencias.csv"
HITOS = RAIZ / "data" / "hitos.csv"
CATALOGO = RAIZ / "docs" / "17-catalogo-a-z.md"
POSTER = RAIZ / "assets" / "atlas-pruebas-tabla-periodica.svg"
LINEA = RAIZ / "assets" / "atlas-pruebas-linea-de-tiempo.svg"
BANNER = RAIZ / "assets" / "atlas-pruebas-banner.svg"

EDICION = "noviembre 2026"
SANS = "Segoe UI, Inter, Helvetica Neue, Arial, sans-serif"
MONO = "Cascadia Code, JetBrains Mono, SFMono-Regular, Menlo, Consolas, monospace"
FONDO, PANEL, TEXTO, TENUE = "#0B1020", "#121A33", "#F1F5F9", "#94A3B8"

# Colores de cada framework: los mismos que los logos de assets/logos.
FRAMEWORKS = [
    ("xunit", "xUnit.net", "x", "#F59E0B"),
    ("nunit", "NUnit", "N", "#818CF8"),
    ("mstest", "MSTest", "M", "#38BDF8"),
]
COLOR_FW = {k: c for k, _, _, c in FRAMEWORKS}

FAMILIAS = [
    ("definicion", "Definir pruebas", "#A78BFA"),
    ("datos", "Datos y parametrización", "#F472B6"),
    ("ciclo", "Ciclo de vida y fixtures", "#34D399"),
    ("aserciones", "Aserciones", "#60A5FA"),
    ("colecciones", "Colecciones y texto", "#2DD4BF"),
    ("excepciones", "Excepciones y asincronía", "#F87171"),
    ("control", "Omisión y metadatos", "#FACC15"),
    ("paralelo", "Paralelismo y tiempo", "#FB923C"),
    ("contexto", "Contexto y diagnóstico", "#A3E635"),
    ("plataforma", "Plataforma y herramientas", "#CBD5E1"),
]
NOMBRE_FAMILIA = {k: n for k, n, _ in FAMILIAS}
COLOR_FAMILIA = {k: c for k, _, c in FAMILIAS}

CARRILES = [
    ("ancestros", "Ancestros", "#E2E8F0"),
    ("nunit", "NUnit", COLOR_FW["nunit"]),
    ("mstest", "MSTest", COLOR_FW["mstest"]),
    ("xunit", "xUnit.net", COLOR_FW["xunit"]),
    ("plataforma", "Plataforma", "#34D399"),
]


def clave_orden(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def leer_equivalencias() -> list[dict]:
    with EQUIVALENCIAS.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    desconocidas = {r["familia"] for r in filas} - set(NOMBRE_FAMILIA)
    if desconocidas:
        raise SystemExit(f"Familias desconocidas en el CSV: {desconocidas}")
    repetidos = [k for k, n in Counter(r["simbolo"] for r in filas).items() if n > 1]
    if repetidos:
        raise SystemExit(f"Símbolos repetidos en el CSV: {repetidos}")
    return filas


def leer_hitos() -> list[dict]:
    with HITOS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def celda(texto: str) -> str:
    texto = texto.replace("|", "\\|")
    if texto in ("", "—"):
        return "—"
    # Sintaxis de código entre comillas invertidas; texto descriptivo tal cual.
    if any(ch in texto for ch in "[]<>().=") or texto.startswith(("Assert", "Is.", "Has.", "Does.", "Throws", "TestContext", "I")):
        partes = [p.strip() for p in texto.split(" · ")]
        return " · ".join(f"`{p}`" if any(ch in p for ch in "[]<>().=_") or p[:1].isupper() and " " not in p else p for p in partes)
    return texto


def cobertura(filas: list[dict], fw: str) -> int:
    return sum(1 for r in filas if r[fw] not in ("—", "") and not r[fw].startswith(("nunca", "eliminado")))


# --------------------------------------------------------------------------- catálogo Markdown

def generar_catalogo(filas: list[dict]) -> str:
    total = len(filas)
    lineas = [
        '<div align="center">', "",
        "# 17 · Catálogo A–Z de equivalencias", "",
        f"**{total} conceptos con su sintaxis en xUnit.net, NUnit y MSTest · edición {EDICION}**", "",
        "[⬅ 16 · Migración](16-migracion.md) · [🏠 Índice](../README.md) · "
        "[18 · Referencia rápida ➡](18-referencia-rapida-y-glosario.md)", "",
        "</div>", "",
        "> [!NOTE]",
        "> Este archivo se **genera automáticamente** desde [`data/equivalencias.csv`](../data/equivalencias.csv) con",
        "> `python3 tools/generar_atlas.py`. Para corregir o añadir un concepto, edita el CSV y ejecuta el script.", "",
        '<a href="../assets/atlas-pruebas-tabla-periodica.svg"><img src="../assets/atlas-pruebas-tabla-periodica.svg" '
        'alt="Tabla periódica de las pruebas en .NET" width="100%"></a>', "",
        "## Cobertura por framework", "",
        "Cuántos de los conceptos del catálogo tienen una forma **nativa** en cada framework. Una cifra menor no significa un framework peor:",
        "xUnit.net omite a propósito varias capacidades (orden, reintentos, `[SetUp]`) por diseño. Consulta [07 · Piedra Rosetta](07-piedra-rosetta.md).", "",
        "| Framework | Conceptos nativos | Cobertura |",
        "|---|---:|---|",
    ]
    for k, nombre, _, _ in FRAMEWORKS:
        n = cobertura(filas, k)
        barra = "█" * round(20 * n / total) + "░" * (20 - round(20 * n / total))
        lineas.append(f"| **{nombre}** | {n} de {total} | `{barra}` {100 * n / total:.0f} % |")
    lineas += ["", "## Resumen por familia", "", "| Familia | Conceptos | xUnit.net | NUnit | MSTest |", "|---|---:|---:|---:|---:|"]
    for k, nombre, _ in FAMILIAS:
        grupo = [r for r in filas if r["familia"] == k]
        lineas.append(f"| [{nombre}](#{nombre.lower().replace(' ', '-')}) | {len(grupo)} | "
                      + " | ".join(str(cobertura(grupo, fw)) for fw, *_ in FRAMEWORKS) + " |")

    lineas += ["", "## Índice alfabético", ""]
    letras: dict[str, list[dict]] = {}
    for r in sorted(filas, key=lambda r: clave_orden(r["concepto"])):
        letras.setdefault(clave_orden(r["concepto"])[0].upper(), []).append(r)
    lineas.append(" · ".join(f"[{l}](#{l.lower()})" for l in letras))
    for letra, grupo in letras.items():
        lineas += ["", f"### {letra}", "", "| № | Símbolo | Concepto | xUnit.net | NUnit | MSTest |", "|---:|:---:|---|---|---|---|"]
        for r in grupo:
            lineas.append(f"| {r['numero']} | **{r['simbolo']}** | {r['concepto']} | {celda(r['xunit'])} | {celda(r['nunit'])} | {celda(r['mstest'])} |")

    lineas += ["", "## Por familia", ""]
    for k, nombre, _ in FAMILIAS:
        lineas += [f"### {nombre}", "", "| № | Concepto | xUnit.net | NUnit | MSTest | Nota |", "|---:|---|---|---|---|---|"]
        for r in (r for r in filas if r["familia"] == k):
            lineas.append(f"| {r['numero']} | {r['concepto']} | {celda(r['xunit'])} | {celda(r['nunit'])} | {celda(r['mstest'])} | {r['nota'] or ''} |")
        lineas.append("")

    lineas += [
        "## Cómo leer las celdas", "",
        "| Marca | Significado |", "|---|---|",
        "| `—` | Sin equivalente nativo: se resuelve con código propio, una biblioteca externa o no se recomienda |",
        "| `(4.0)`, `(4.3)`, `(5.0)` | Versión del framework en que apareció o cambió la característica |",
        "| `·` | Separa alternativas equivalentes |", "",
        "Todas las API del catálogo se comprobaron compilando contra `xunit.v3` 4.0.2, `NUnit` 5.0.0 y `MSTest` 4.5.2,",
        "salvo `--partition` de MSTest 5.0, que aún no se publica.", "",
        "---", "",
        '<div align="center">', "",
        "[⬅ 16 · Migración](16-migracion.md) · [🏠 Índice](../README.md) · "
        "[18 · Referencia rápida ➡](18-referencia-rapida-y-glosario.md)", "",
        "</div>", "",
    ]
    return "\n".join(lineas)


# --------------------------------------------------------------------------- utilidades SVG

def recortar(texto: str, maximo: int) -> str:
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


def envolver(texto: str, maximo: int) -> list[str]:
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        if len(actual) + len(p) + (1 if actual else 0) > maximo and actual:
            lineas.append(actual)
            actual = p
        else:
            actual = f"{actual} {p}".strip()
    lineas.append(actual)
    return lineas


def defs_comunes() -> list[str]:
    return [
        "<defs>",
        f'<linearGradient id="fondo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0B1020"/>'
        f'<stop offset="0.55" stop-color="#111739"/><stop offset="1" stop-color="#1B1040"/></linearGradient>',
        '<linearGradient id="arcoiris" x1="0" x2="1"><stop offset="0" stop-color="#F59E0B"/><stop offset="0.5" stop-color="#818CF8"/>'
        '<stop offset="1" stop-color="#38BDF8"/></linearGradient>',
        '<filter id="brillo" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '<pattern id="rejilla" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#FFFFFF" stroke-opacity="0.035"/></pattern>',
        "</defs>",
    ]


# --------------------------------------------------------------------------- tabla periódica

def generar_poster(filas: list[dict]) -> str:
    por_fila, ancho_t, alto_t, sep = 12, 178, 156, 8
    margen, etiqueta, cabecera = 48, 210, 250
    bandas = []
    for k, nombre, color in FAMILIAS:
        grupo = [r for r in filas if r["familia"] == k]
        bandas.append((k, nombre, color, [grupo[i:i + por_fila] for i in range(0, len(grupo), por_fila)]))
    filas_totales = sum(len(b[3]) for b in bandas)
    ancho = margen * 2 + etiqueta + por_fila * (ancho_t + sep) - sep
    alto = cabecera + filas_totales * (alto_t + sep) + (len(bandas) - 1) * 14 + 170

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" '
         f'font-family="{SANS}" role="img" aria-label="Tabla periódica de las pruebas en .NET">']
    s += defs_comunes()
    s.append(f'<rect width="{ancho}" height="{alto}" fill="url(#fondo)"/><rect width="{ancho}" height="{alto}" fill="url(#rejilla)"/>')
    s.append(f'<rect x="0" y="0" width="{ancho}" height="6" fill="url(#arcoiris)"/>')
    s.append(f'<text x="{margen}" y="92" font-size="54" font-weight="800" fill="{TEXTO}" letter-spacing="-1">Tabla periódica de las pruebas en .NET</text>')
    s.append(f'<text x="{margen}" y="136" font-size="22" fill="{TENUE}">{len(filas)} conceptos · su sintaxis en xUnit.net v3, NUnit 5 y MSTest 4 · edición {EDICION}</text>')
    # Leyenda de frameworks
    x = margen
    for k, nombre, letra, color in FRAMEWORKS:
        s.append(f'<circle cx="{x + 13}" cy="186" r="13" fill="{color}"/>')
        s.append(f'<text x="{x + 13}" y="191" font-size="14" font-weight="800" fill="{FONDO}" text-anchor="middle">{letra}</text>')
        s.append(f'<text x="{x + 34}" y="192" font-size="18" font-weight="600" fill="{TEXTO}">{nombre}</text>')
        s.append(f'<text x="{x + 34}" y="214" font-size="13" fill="{TENUE}">{cobertura(filas, k)} conceptos nativos</text>')
        x += 230
    s.append(f'<text x="{ancho - margen}" y="192" font-size="15" fill="{TENUE}" text-anchor="end">— = sin equivalente nativo</text>')

    y = cabecera
    for i, (k, nombre, color, renglones) in enumerate(bandas):
        alto_banda = len(renglones) * (alto_t + sep) - sep
        s.append(f'<rect x="{margen}" y="{y}" width="6" height="{alto_banda}" rx="3" fill="{color}"/>')
        for j, linea in enumerate(envolver(nombre, 16)):
            s.append(f'<text x="{margen + 22}" y="{y + 30 + j * 24}" font-size="20" font-weight="700" fill="{color}">{escape(linea)}</text>')
        n = sum(len(r) for r in renglones)
        s.append(f'<text x="{margen + 22}" y="{y + 30 + len(envolver(nombre, 16)) * 24 + 6}" font-size="14" fill="{TENUE}">{n} conceptos</text>')
        for fila_idx, renglon in enumerate(renglones):
            ty = y + fila_idx * (alto_t + sep)
            for col, r in enumerate(renglon):
                tx = margen + etiqueta + col * (ancho_t + sep)
                s.append(f'<g transform="translate({tx},{ty})">')
                s.append(f'<rect width="{ancho_t}" height="{alto_t}" rx="12" fill="{PANEL}" stroke="{color}" stroke-opacity="0.55"/>')
                s.append(f'<rect width="{ancho_t}" height="5" rx="2.5" fill="{color}"/>')
                s.append(f'<text x="12" y="25" font-size="12" fill="{TENUE}">{r["numero"]}</text>')
                s.append(f'<text x="12" y="58" font-size="32" font-weight="800" fill="{color}">{escape(r["simbolo"])}</text>')
                for j, linea in enumerate(envolver(r["concepto"], 15)[:3]):
                    s.append(f'<text x="{ancho_t - 10}" y="{24 + j * 16}" font-size="12.5" font-weight="600" fill="{TEXTO}" text-anchor="end">{escape(linea)}</text>')
                for m, (fw, _, letra, fcolor) in enumerate(FRAMEWORKS):
                    valor = r[fw]
                    vacio = valor in ("—", "") or valor.startswith(("nunca", "eliminado"))
                    yy = 86 + m * 22
                    s.append(f'<circle cx="19" cy="{yy - 4}" r="7.5" fill="{fcolor}" fill-opacity="{0.25 if vacio else 1}"/>')
                    s.append(f'<text x="19" y="{yy}" font-size="9.5" font-weight="800" fill="{FONDO}" text-anchor="middle">{letra}</text>')
                    s.append(f'<text x="32" y="{yy}" font-size="10" font-family="{MONO}" fill="{TENUE if vacio else TEXTO}" '
                             f'fill-opacity="{0.55 if vacio else 0.92}">{escape(recortar(valor, 24))}</text>')
                s.append("</g>")
        y += alto_banda + sep + 14

    y += 30
    s.append(f'<line x1="{margen}" y1="{y}" x2="{ancho - margen}" y2="{y}" stroke="#FFFFFF" stroke-opacity="0.08"/>')
    s.append(f'<text x="{margen}" y="{y + 42}" font-size="16" fill="{TENUE}">Generado desde data/equivalencias.csv con tools/generar_atlas.py · '
             f'cada API se compiló contra xunit.v3 4.0.2, NUnit 5.0.0 y MSTest 4.5.2</text>')
    s.append(f'<text x="{ancho - margen}" y="{y + 42}" font-size="16" font-weight="700" fill="url(#arcoiris)" text-anchor="end">Atlas de Pruebas .NET</text>')
    s.append("</svg>")
    return "\n".join(s)


# --------------------------------------------------------------------------- línea de tiempo

def anio(fecha: str) -> float:
    partes = fecha.split("-")
    return int(partes[0]) + ((int(partes[1]) - 0.5) / 12 if len(partes) > 1 else 0.5)


def generar_linea(hitos: list[dict]) -> str:
    ancho, margen, etiqueta = 2200, 60, 190
    alto_carril, cabecera = 200, 230
    alto = cabecera + len(CARRILES) * alto_carril + 120
    # Escala por tramos: 1994–2014 comprimido, 2014–2027 expandido, para que la era moderna respire.
    x0, x1 = margen + etiqueta, ancho - margen
    corte = x0 + (x1 - x0) * 0.24

    def px(a: float) -> float:
        if a < 2014:
            return x0 + (a - 1993) / (2014 - 1993) * (corte - x0)
        return corte + (a - 2014) / (2027.6 - 2014) * (x1 - corte)

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" '
         f'font-family="{SANS}" role="img" aria-label="Línea de tiempo de xUnit.net, NUnit y MSTest">']
    s += defs_comunes()
    s.append(f'<rect width="{ancho}" height="{alto}" fill="url(#fondo)"/><rect width="{ancho}" height="{alto}" fill="url(#rejilla)"/>')
    s.append(f'<rect x="0" y="0" width="{ancho}" height="6" fill="url(#arcoiris)"/>')
    s.append(f'<text x="{margen}" y="86" font-size="48" font-weight="800" fill="{TEXTO}" letter-spacing="-1">Tres décadas de pruebas unitarias en .NET</text>')
    s.append(f'<text x="{margen}" y="126" font-size="21" fill="{TENUE}">De SUnit (1994) a xUnit.net v3 4.0, NUnit 5 y MSTest 4.5 · '
             f'la escala se expande a partir de 2014</text>')

    # Eje de años
    for a in [1994, 1997, 2000, 2002, 2005, 2007, 2010, 2014, 2016, 2018, 2020, 2022, 2024, 2025, 2026]:
        x = px(a + 0.0)
        s.append(f'<line x1="{x:.1f}" y1="{cabecera - 20}" x2="{x:.1f}" y2="{alto - 90}" stroke="#FFFFFF" stroke-opacity="0.06"/>')
        s.append(f'<text x="{x:.1f}" y="{cabecera - 30}" font-size="15" fill="{TENUE}" text-anchor="middle">{a}</text>')
    s.append(f'<rect x="{corte:.1f}" y="{cabecera - 18}" width="{x1 - corte:.1f}" height="{alto - 90 - cabecera + 18}" fill="#FFFFFF" fill-opacity="0.018"/>')

    # Marca de "hoy"
    hoy = px(2026 + 10.25 / 12)
    s.append(f'<line x1="{hoy:.1f}" y1="{cabecera - 18}" x2="{hoy:.1f}" y2="{alto - 90}" stroke="#34D399" stroke-dasharray="6 6" stroke-width="2"/>')
    s.append(f'<text x="{hoy - 8:.1f}" y="{alto - 66}" font-size="15" font-weight="700" fill="#34D399" text-anchor="end">hoy · 8-nov-2026</text>')
    for i, (k, nombre, color) in enumerate(CARRILES):
        y = cabecera + i * alto_carril + alto_carril / 2
        s.append(f'<text x="{margen}" y="{y + 7}" font-size="22" font-weight="800" fill="{color}">{nombre}</text>')
        s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{color}" stroke-opacity="0.35" stroke-width="3" stroke-linecap="round"/>')
        propios = sorted((h for h in hitos if h["carril"] == k), key=lambda h: anio(h["fecha"]))
        ocupado: dict[tuple[bool, int], float] = {}  # (arriba, nivel) -> borde derecho de la última etiqueta
        for h in propios:
            x = px(anio(h["fecha"]))
            destacado = h["destacado"] == "1"
            media = max(len(h["hito"]) * (9.5 if destacado else 8.2), len(h["detalle"]) * 6.6) / 2 + 10
            opciones = [(True, 0), (False, 0), (True, 1), (False, 1)]
            arriba, nivel = next((o for o in opciones if ocupado.get(o, -1e9) < x - media), opciones[0])
            ocupado[(arriba, nivel)] = x + media
            desplazamiento = 30 + nivel * 44
            ty = y - desplazamiento if arriba else y + desplazamiento + 14
            r = 10 if destacado else 7
            if destacado:
                s.append(f'<circle cx="{x:.1f}" cy="{y}" r="{r + 6}" fill="{color}" fill-opacity="0.18" filter="url(#brillo)"/>')
            s.append(f'<line x1="{x:.1f}" y1="{y}" x2="{x:.1f}" y2="{ty + (6 if arriba else -20)}" stroke="{color}" stroke-opacity="0.5"/>')
            s.append(f'<circle cx="{x:.1f}" cy="{y}" r="{r}" fill="{FONDO}" stroke="{color}" stroke-width="3.5"/>')
            halo = f'stroke="{FONDO}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
            s.append(f'<text x="{x:.1f}" y="{ty}" font-size="{16 if destacado else 14}" font-weight="{800 if destacado else 600}" fill="{TEXTO}" text-anchor="middle" {halo}>{escape(h["hito"])}</text>')
            s.append(f'<text x="{x:.1f}" y="{ty + (-19 if arriba else 18)}" font-size="12" fill="{TENUE}" text-anchor="middle" {halo}>{escape(h["detalle"])}</text>')

    s.append(f'<text x="{margen}" y="{alto - 30}" font-size="15" fill="{TENUE}">Fechas de NuGet y notas de versión oficiales · generado desde data/hitos.csv</text>')
    s.append("</svg>")
    return "\n".join(s)


# --------------------------------------------------------------------------- banner

def generar_banner(filas: list[dict]) -> str:
    ancho, alto = 1600, 460
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}" '
         f'font-family="{SANS}" role="img" aria-label="Atlas de Pruebas .NET: xUnit.net, NUnit y MSTest">']
    s += defs_comunes()
    s.append(f'<rect width="{ancho}" height="{alto}" rx="28" fill="url(#fondo)"/><rect width="{ancho}" height="{alto}" rx="28" fill="url(#rejilla)"/>')

    # Motivo: una ejecución de pruebas como mosaico de resultados (determinista, sin azar).
    cols, renglones, lado = 30, 19, 15
    ox, oy = ancho - cols * (lado + 5) - 30, 34
    s.append('<linearGradient id="fundido" x1="0" x2="1"><stop offset="0" stop-color="#FFF" stop-opacity="0"/>'
             '<stop offset="0.45" stop-color="#FFF" stop-opacity="1"/></linearGradient>'
             f'<mask id="mascara"><rect x="{ox}" y="0" width="{cols * (lado + 5)}" height="{alto}" fill="url(#fundido)"/></mask>')
    s.append('<g mask="url(#mascara)">')
    for c in range(cols):
        for r in range(renglones):
            v = (c * 7919 + r * 104729 + c * r * 31) % 97
            if v < 2:
                color, op = "#F87171", 0.95
            elif v < 4:
                color, op = "#FACC15", 0.9
            else:
                color, op = ["#F59E0B", "#818CF8", "#38BDF8"][(c // 10) % 3], 0.22 + (v % 11) / 18
            s.append(f'<rect x="{ox + c * (lado + 5)}" y="{oy + r * (lado + 5)}" width="{lado}" height="{lado}" rx="4" fill="{color}" fill-opacity="{min(op, 0.85):.2f}"/>')
    s.append("</g>")

    s.append(f'<text x="70" y="128" font-size="26" font-weight="700" fill="{TENUE}" letter-spacing="6">ATLAS DE</text>')
    s.append(f'<text x="66" y="212" font-size="92" font-weight="900" fill="{TEXTO}" letter-spacing="-3">Pruebas <tspan fill="url(#arcoiris)">.NET</tspan></text>')
    s.append(f'<text x="70" y="262" font-size="25" fill="#CBD5E1">xUnit.net · NUnit · MSTest — su historia, su filosofía y su código, lado a lado</text>')

    medallas = [("xunit", "xUnit.net", "v3 4.0", "x"), ("nunit", "NUnit", "5.0", "N"), ("mstest", "MSTest", "4.5", "M")]
    for i, (k, nombre, version, letra) in enumerate(medallas):
        cx = 112 + i * 250
        color = COLOR_FW[k]
        s.append(f'<circle cx="{cx}" cy="350" r="40" fill="{color}" fill-opacity="0.18" filter="url(#brillo)"/>')
        s.append(f'<circle cx="{cx}" cy="350" r="34" fill="{FONDO}" stroke="{color}" stroke-width="4"/>')
        s.append(f'<text x="{cx}" y="363" font-size="36" font-weight="900" fill="{color}" text-anchor="middle">{letra}</text>')
        s.append(f'<text x="{cx + 50}" y="345" font-size="24" font-weight="800" fill="{TEXTO}">{nombre}</text>')
        s.append(f'<text x="{cx + 50}" y="372" font-size="17" fill="{color}">{version}</text>')
    s.append(f'<text x="70" y="430" font-size="17" fill="{TENUE}">{len(filas)} equivalencias · 19 capítulos · 99 pruebas de laboratorio en verde · edición {EDICION}</text>')
    s.append("</svg>")
    return "\n".join(s)


def main() -> None:
    filas = leer_equivalencias()
    hitos = leer_hitos()
    CATALOGO.write_text(generar_catalogo(filas), encoding="utf-8")
    POSTER.write_text(generar_poster(filas), encoding="utf-8")
    LINEA.write_text(generar_linea(hitos), encoding="utf-8")
    BANNER.write_text(generar_banner(filas), encoding="utf-8")
    print(f"✅ {len(filas)} equivalencias · {len(hitos)} hitos")
    for p in (CATALOGO, POSTER, LINEA, BANNER):
        print(f"   {p.relative_to(RAIZ)}  ({p.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
