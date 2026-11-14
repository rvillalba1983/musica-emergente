#!/usr/bin/env python3
"""Verifica sin IA que el YouTube y el Spotify de cada candidato son del artista.

Compara el nombre del artista con:
- el título de la ficha de Spotify (oembed)
- el título del canal de YouTube

Marca cada candidato como «ok» o «revisar» (con los motivos). Es una ayuda para
la revisión editorial: no borra nada ni decide.

Uso: python3 scripts/verificar_candidatos.py [--entrada data/candidatos.json] [--salida data/candidatos_verificados.json]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

import comun as c

ENTRADA = os.path.join(c.RAIZ, "data", "candidatos.json")
SALIDA = os.path.join(c.RAIZ, "data", "candidatos_verificados.json")


def titulo_spotify(artist_id):
    """Título de la ficha de Spotify del artista (vía oembed)."""
    t = c.descargar("https://open.spotify.com/oembed?url=https://open.spotify.com/artist/" + artist_id)
    try:
        return (json.loads(t or "") or {}).get("title", "") or ""
    except ValueError:
        return ""


def titulo_youtube(channel_id):
    """Título del canal de YouTube."""
    p = c.descargar(f"https://www.youtube.com/channel/{channel_id}")
    if not p:
        return ""
    m = re.search(r"<title>(.*?)</title>", p, flags=re.S)
    if not m:
        return ""
    t = c.texto_plano(m.group(1))
    return re.sub(r"\s*-\s*YouTube\s*$", "", t).strip()


def coincide(a, b):
    """El nombre del candidato y el título de la ficha se contienen mutuamente."""
    na, nb = c.normalizar(a), c.normalizar(b)
    if not na or not nb:
        return True  # sin datos no se puede afirmar que NO coinciden
    return na in nb or nb in na


def verificar(candidato):
    avisos = []
    sp = (candidato.get("spotify") or {}).get("id")
    if sp:
        t = titulo_spotify(sp)
        if t and not coincide(t, candidato["nombre"]):
            avisos.append(f"Spotify: la ficha dice «{t}», el candidato es «{candidato['nombre']}»")
    yt = (candidato.get("youtube") or {}).get("channelId")
    if yt:
        t = titulo_youtube(yt)
        if t and not coincide(t, candidato["nombre"]):
            avisos.append(f"YouTube: el canal se llama «{t}»")
    return avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=ENTRADA, help="Candidatos del recolector")
    ap.add_argument("--salida", default=SALIDA, help="Archivo con el resultado de la verificación")
    args = ap.parse_args()

    if not os.path.exists(args.entrada):
        c.log(f"No existe {args.entrada}: lanza antes recolectar.py")
        sys.exit(2)

    with open(args.entrada, encoding="utf-8") as f:
        datos = json.load(f)
    candidatos = datos.get("candidatos", [])

    resultado, avisados = [], 0
    for i, a in enumerate(candidatos, 1):
        c.log(f"[{i}/{len(candidatos)}] {a['nombre']}")
        avisos = verificar(a)
        if avisos:
            avisados += 1
        resultado.append(dict(a, verificacion={"estado": "ok" if not avisos else "revisar", "avisos": avisos}))

    salida = {
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "entrada_original": os.path.basename(args.entrada),
        "fecha_entrada": datos.get("fecha_entrada"),
        "candidatos": resultado,
    }
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
        f.write("\n")

    msg = f"**Verificación de candidatos:** {len(resultado)} revisados, {avisados} con avisos."
    c.log(msg)
    c.resumen_github(msg)
    sys.exit(1 if avisados else 0)


if __name__ == "__main__":
    main()