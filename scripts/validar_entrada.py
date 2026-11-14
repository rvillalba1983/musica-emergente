#!/usr/bin/env python3
"""Valida una entrada suelta (JSON) antes de publicarla.

Útil para validar la salida de ia_generar.py o del buzón antes de meterla
en data/diario.json. Comprueba los mismos criterios que revisar.py pero
para una sola entrada (o para un diario completo, si se le pasa uno).

Uso:
  python3 scripts/validar_entrada.py /tmp/entrada_ia.json
  python3 scripts/validar_entrada.py data/diario.json

Sale con código 1 si hay errores; 0 si solo hay avisos o todo está bien.
"""
import argparse
import datetime as dt
import json
import re
import sys

import comun as c

CAMPOS_ENTRADA = ("id", "numero", "fecha", "titulo", "intro", "artistas")
CAMPOS_ARTISTA = ("nombre", "estilo", "porQue")
REDES = {"spotify", "youtube", "instagram", "tiktok", "facebook", "bandcamp", "web"}
PROHIBIDO = re.compile(r"no he encontrado|no encontr[eé]|sin verificar|no verificad|"
                       r"tus gustos|que escuchas|tu spotify|el dueño", re.I)


def fecha_ok(s):
    try:
        dt.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def validar_entrada(e, errores, avisos):
    n = e.get("numero")
    for k in CAMPOS_ENTRADA:
        if not e.get(k):
            errores.append(f"Nº {n}: falta «{k}»")
    if not fecha_ok(e.get("fecha")):
        errores.append(f"Nº {n}: fecha no válida «{e.get('fecha')}»")
    v = e.get("ventana")
    if v and not (fecha_ok(v.get("desde")) and fecha_ok(v.get("hasta"))):
        errores.append(f"Nº {n}: ventana no válida")
    for campo in ("titulo", "intro"):
        if PROHIBIDO.search(e.get(campo, "")):
            avisos.append(f"Nº {n}: el {campo} parece hablar del proceso o de los gustos del dueño")
    for a in e.get("artistas") or []:
        nom = a.get("nombre", "?")
        for k in CAMPOS_ARTISTA:
            if not a.get(k):
                errores.append(f"Nº {n} · {nom}: falta «{k}»")
        if not a.get("origen"):
            avisos.append(f"Nº {n} · {nom}: sin origen")
        if PROHIBIDO.search(a.get("porQue", "")):
            avisos.append(f"Nº {n} · {nom}: el texto parece hablar del proceso o de los gustos del dueño")
        if a.get("spotifyId") and not re.fullmatch(r"[A-Za-z0-9]{22}", a["spotifyId"]):
            errores.append(f"Nº {n} · {nom}: spotifyId con formato raro")
        for r in (a.get("redes") or {}):
            if r not in REDES:
                avisos.append(f"Nº {n} · {nom}: red desconocida «{r}» (la web no la pinta)")
        for x in a.get("conciertos") or []:
            if not fecha_ok(x.get("fecha")):
                errores.append(f"Nº {n} · {nom}: concierto con fecha no válida «{x.get('fecha')}»")
            if not x.get("lugar"):
                errores.append(f"Nº {n} · {nom}: concierto sin lugar")
        if v and a.get("conciertos") and not any(v["desde"] <= x.get("fecha", "") <= v["hasta"] for x in a["conciertos"]):
            avisos.append(f"Nº {n} · {nom}: ningún concierto dentro de la ventana")
        vids = a.get("videos") or []
        for x in vids:
            if not re.fullmatch(r"[\w-]{11}", x.get("id", "")):
                errores.append(f"Nº {n} · {nom}: id de vídeo no válido «{x.get('id')}»")
        if len({x.get("id") for x in vids}) < len(vids):
            errores.append(f"Nº {n} · {nom}: vídeo repetido")
        if not vids and not a.get("youtubeChannelId"):
            avisos.append(f"Nº {n} · {nom}: sin vídeos")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", help="JSON con una entrada o con el diario completo")
    args = ap.parse_args()

    errores, avisos = [], []
    try:
        with open(args.archivo, encoding="utf-8") as f:
            datos = json.load(f)
    except ValueError as e:
        print(f"ERROR: {args.archivo} no es un JSON válido: {e}")
        sys.exit(1)

    if "entradas" in datos:  # es un diario completo
        entradas = datos["entradas"]
    else:  # es una entrada suelta
        entradas = [datos]

    for e in entradas:
        validar_entrada(e, errores, avisos)

    lineas = [f"**Validación de {args.archivo}:** {len(entradas)} entrada(s), "
              f"{len(errores)} error(es), {len(avisos)} aviso(s)."]
    lineas += [f"- ❌ {x}" for x in errores] + [f"- ⚠️ {x}" for x in avisos]
    texto = "\n".join(lineas)
    print(texto)
    c.resumen_github(texto)
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()