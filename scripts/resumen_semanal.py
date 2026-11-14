#!/usr/bin/env python3
"""Genera un resumen semanal del diario para revisión o para publicar en GitHub Issues.

Produce un informe con:
- Número de entradas publicadas
- Artistas totales y de la última entrada
- Ciudades cubiertas
- Conciertos por fechas (próximos y pasados)
- Estadísticas de verificación (si existe el archivo de candidatos verificados)

Uso: python3 scripts/resumen_semanal.py [--entrada data/diario.json] [--candidatos data/candidatos.json] [--salida resumen.md]
"""
import argparse
import datetime as dt
import json
import os
import sys

import comun as c

ENTRADA = os.path.join(c.RAIZ, "data", "diario.json")
CANDIDATOS = os.path.join(c.RAIZ, "data", "candidatos.json")
SALIDA = os.path.join(c.RAIZ, "resumen_semanal.md")


def cargar_datos(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def contar_ciudades(entrada):
    """Contar ciudades de los conciertos de una entrada."""
    ciudades = set()
    for artista in entrada.get("artistas", []):
        for conc in artista.get("conciertos", []):
            if conc.get("ciudad"):
                ciudades.add(conc["ciudad"])
    return sorted(ciudades)


def contar_conciertos_por_fecha(entrada, hoy):
    """Contar conciertos próximos (desde hoy) y pasados."""
    proximos = 0
    pasados = 0
    for artista in entrada.get("artistas", []):
        for conc in artista.get("conciertos", []):
            fecha = conc.get("fecha", "")
            if fecha >= hoy:
                proximos += 1
            else:
                pasados += 1
    return proximos, pasados


def generar_resumen(diario, candidatos=None):
    """Generar el texto del resumen semanal."""
    lineas = []
    entradas = diario.get("entradas", []) if diario else []
    total_artistas = sum(len(e.get("artistas", [])) for e in entradas)

    lineas.append("## Resumen semanal del diario Radar de salas")
    lineas.append("")
    lineas.append(f"**Fecha de generación:** {dt.datetime.now(dt.timezone.utc).isoformat(timespec='minutes')}")
    lineas.append("")
    lineas.append(f"- **Entradas publicadas:** {len(entradas)}")
    lineas.append(f"- **Artistas totales:** {total_artistas}")

    if entradas:
        ultima = entradas[0]  # La primera es la más reciente (ya ordenado)
        lineas.append(f"- **Última entrada:** Nº {ultima.get('numero', '?')} ({ultima.get('fecha', '')})")
        lineas.append(f"  - **Título:** {ultima.get('titulo', '')}")
        lineas.append(f"  - **Artistas:** {len(ultima.get('artistas', []))}")

        ciudades = contar_ciudades(ultima)
        if ciudades:
            lineas.append(f"  - **Ciudades:** {', '.join(ciudades)}")

        hoy = dt.date.today().isoformat()
        proximos, pasados = contar_conciertos_por_fecha(ultima, hoy)
        lineas.append(f"  - **Conciertos próximos:** {proximos}")
        lineas.append(f"  - **Conciertos pasados:** {pasados}")

    if candidatos:
        ver = candidatos.get("candidatos_verificados", [])
        if ver:
            total_ver = len(ver)
            ok_ver = sum(1 for v in ver if v.get("verificacion", {}).get("estado") == "ok")
            revisar_ver = total_ver - ok_ver
            lineas.append(f"- **Candidatos verificados:** {total_ver} ({ok_ver} ok, {revisar_ver} con avisos)")
        else:
            lineas.append(f"- **Candidatos pendientes de verificación:** {len(candidatos.get('candidatos', []))}")

    return "\n".join(lineas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=ENTRADA, help="Archivo del diario")
    ap.add_argument("--candidatos", default=CANDIDATOS, help="Archivo de candidatos (para estadísticas)")
    ap.add_argument("--salida", default=SALIDA, help="Archivo markdown de salida")
    args = ap.parse_args()

    diario = cargar_datos(args.entrada)
    candidatos = cargar_datos(args.candidatos)

    if not diario:
        print("::error::No se encontró data/diario.json")
        sys.exit(1)

    resumen = generar_resumen(diario, candidatos)

    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(resumen + "\n")

    c.log("Resumen semanal generado en " + args.salida)


if __name__ == "__main__":
    main()