#!/usr/bin/env python3
"""Genera un borrador de entrada a partir de candidatos seleccionados.

Esto proporciona una plantilla inicial basada en criterios sin IA y en los datos
existentes (candidatos, entradas anteriores). Claude puede revisar y editar
el resultado antes de publicar.

Uso: python3 scripts/generar_entrada.py \
  --entrada_borrador data/entrada_borrador.json \
  --salida data/diario_nuevo.json \
  --fecha AAAA-MM-DD
"""
import argparse
import datetime as dt
import json
import sys

import comun as c

# Estilos afines según el diario
ESTILOS_AFINES = {
    "Cantautores", "Mestizaje/Fusión", "Rumba", "Flamenco/Copla",
    "Folk", "Música Latina", "Pop Latino", "Canción de autor", "Música de Autor"
}


def generar_titulo(artistas):
    """Sugerir un título usando estilos y lugares destacados."""
    estilos = set()
    lugares = []
    for a in artistas:
        for est in a.get("estilos", []):
            if est in ESTILOS_AFINES:
                estilos.add(est)
        for conc in a.get("conciertos", []):
            if conc.get("ciudad") and conc["ciudad"] not in lugares:
                lugares.append(conc["ciudad"])
    estilos_str = ", ".join(sorted(estilos))
    lugar_str = lugares[0] if lugares else ""
    if estilos_str and lugar_str:
        return f"{estilos_str} en {lugar_str}"
    if estilos_str:
        return estilos_str
    return lugar_str or "Entrada del diario"


def generar_intro(artistas, ventana_desde, ventana_hasta):
    """Generar intro resumiendo los artistas y fechas."""
    nombres = ", ".join(a["nombre"] for a in artistas[:3])
    return (f"{len(artistas)} artistas con concierto entre el {ventana_desde} y el {ventana_hasta}. "
            f"Esta semana: {nombres}.")


def generar_porque(artista):
    """Crear un esqueleto para el campo porQué usando bio + concierto destacado + estilo."""
    nombre = artista.get("nombre", "")
    bio = artista.get("bio", "")
    estilo = (artista.get("estilos", [])[0] if artista.get("estilos") else "")
    conciertos = artista.get("conciertos", [])
    concierto = conciertos[0] if conciertos else {}
    fecha = concierto.get("fecha", "")
    lugar = concierto.get("lugar", "")
    ciudad = concierto.get("ciudad", "")

    partes = []
    if bio:
        partes.append(bio[:300])
    if fecha:
        lugar_txt = f"{lugar} ({ciudad})" if ciudad else lugar
        partes.append(f"Tocó el {fecha} en {lugar_txt}.")
    porQue = f"{nombre}: " + " ".join(partes) if partes else nombre
    return porQue.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada_borrador", required=True,
                    help="Archivo con candidatos (data/entrada_borrador.json)")
    ap.add_argument("--salida", required=True,
                    help="Archivo para guardar la entrada resultante (data/diario_nuevo.json)")
    ap.add_argument("--fecha", required=True, help="Fecha de publicación (AAAA-MM-DD)")
    args = ap.parse_args()

    # Leer entrada borrador
    with open(args.entrada_borrador, encoding="utf-8") as f:
        datos = json.load(f)
    candidatos = datos.get("candidatos", [])
    if not candidatos:
        print("::error::No hay candidatos en el borrador")
        sys.exit(1)

    # Fecha de entrada
    fecha = dt.date.fromisoformat(args.fecha)
    ventana_desde = fecha - dt.timedelta(days=7)
    ventana_hasta = fecha + dt.timedelta(days=15)

    # Generar entrada
    entrada = {
        "id": fecha.isoformat(),
        "numero": 1,  # se recalcula al fusionar con el diario
        "fecha": fecha.isoformat(),
        "titulo": generar_titulo(candidatos),
        "intro": generar_intro(candidatos, ventana_desde.isoformat(), ventana_hasta.isoformat()),
        "ventana": {
            "desde": ventana_desde.isoformat(),
            "hasta": ventana_hasta.isoformat(),
        },
        "artistas": [],
    }

    for cand in candidatos:
        artista = {
            "nombre": cand.get("nombre", ""),
            "origen": cand.get("origen", ""),
            "estilo": cand.get("estilos", []),
            "porQue": generar_porque(cand),
            "cancion": cand.get("cancion", {"titulo": "", "url": ""}),
            "conciertos": cand.get("conciertos", []),
            "redes": cand.get("redes", {}),
            "youtubeChannelId": cand.get("youtubeChannelId", ""),
            "spotifyId": cand.get("spotify", {}).get("id", ""),
            "foto": cand.get("foto", ""),
            "videos": cand.get("youtube", {}).get("videos", []) or [],
        }
        entrada["artistas"].append(artista)

    # Guardar entrada como nuevo diario (temporal)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump({"entradas": [entrada]}, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"**Entrada generada** para {fecha} con {len(candidatos)} artistas")


if __name__ == "__main__":
    main()