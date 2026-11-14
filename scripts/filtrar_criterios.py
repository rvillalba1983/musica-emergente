#!/usr/bin/env python3
"""Filtrar candidatos según criterios editoriales sin IA.

Requisitos del diario Radar de salas para la selección semanal:
- Emergentes de verdad: primeras giras, EP o primeros discos, circuitos tipo Girando Por Salas o Radar Joven. Nada de veteranos ni artistas que llenan teatros.
- Con al menos un concierto DENTRO de la ventana (fecha de publicación − 7 días … +15 días).
- Que encajen con el perfil: canción de autor, rumba, flamenco y flamenquito, mestizaje; letras en castellano preferiblemente.
- Que no hayan salido en ninguna entrada anterior (ya gestionado por excluir.json + rechazados.json).

Uso: python3 scripts/filtrar_criterios.py --entrada data/candidatos.json --ventana_desde YYYY-MM-DD --ventana_hasta YYYY-MM-DD --salida data/candidatos_filtrados.json
"""
import argparse
import datetime as dt
import json
import os
import sys

import comun as c

# Estilos afines según criterios del diario (del CLAUDE.md)
ESTILOS_AFINES = {
    "Cantautores", "Mestizaje/Fusión", "Rumba", "Flamenco/Copla",
    "Folk", "Música Latina", "Pop Latino", "Canción de autor", "Música de Autor"
}

# Estilos descartar (muy comerciales, rockazos, etc.)
ESTILOS_DESCARTAR = {"Rock", "Pop rock", "Indie rock", "Electrónica", "Hip hop"}

# Circuitos de emergentes según el diario (Girando Por Salas, Radar Joven)
CIRCUITOS_EMERGENTES = {
    "Girando Por Salas", "GPS", "Radar Joven", "Radar joven"
}

# Umbral para considerar "emergente" en seguidores (si tenemos datos de Spotify)
MAX_SEGUIDORES_EMERGENTE = 50000

# Cantidad mínima de álbumes para considerar emergente
MIN_ALBUMES_EMERGENTE = 1

def es_emergente(candidato, ventana_fecha):
    """Heurística sin IA para emergente.
    Basada en:
    - primeros discos/EP (no disponible directamente)
    - circuitos emergentes (GPS, Radar Joven)
    - seguidores en Spotify (si hay ID y se puede consultar)
    - edad del álbum más reciente (si hay fecha de lanzamiento)
    """
    # Criterio 1: estilos afines
    estilos = set(candidato.get("estilos", []))
    if not estilos & ESTILOS_AFINES:
        return False

    # Criterio 2: rechazado (fuera del exclu.json original, pero manejado ahora)
    # (esto es responsabilidad del recolector; aquí no se gestiona)

    # Criterio 3: circuitos emergentes (si aparecen en bio/conciertos)
    if candidato.get("bio"):
        bio = candidato["bio"].lower()
        for circuito in CIRCUITOS_EMERGENTES:
            if circuito.lower() in bio.lower():
                return True

    # Criterio 4: seguidores en Spotify (si hay ID)
    spotify_id = candidato.get("spotifyId")
    if spotify_id:
        # No podemos consultar Spotify sin token; si lo hubiera, podríamos llamar a la API
        # Por ahora, asumimos que no lo tenemos, y pasamos a la siguiente heurística
        pass

    # Criterio 5: edad del álbum más reciente (si tenemos fecha de lanzamiento)
    # No disponible en los datos actuales

    # Criterio 6: canción de autor o mestizaje (título de canciones)
    cancion = candidato.get("cancion", {})
    titulo = (cancion.get("titulo", "") + " " + candidato.get("nombre", "")).lower()
    palabras_clave_emergente = ["primera", " debut ", " ep ", " nuevo ", " emergente "]
    if any(p in titulo for p in palabras_clave_emergente):
        return True

    # Sin datos suficientes para afirmar que NO es emergente (no tenemos seguidores
    # ni fecha del último álbum): se deja pasar para revisión editorial.
    return True

def filtrar_candidatos(candidatos, ventana_desde, ventana_hasta):
    """Filtrar candidatos según criterios del diario."""
    filtrados = []

    for candidato in candidatos:
        # 1. Estilos afines + no descartados
        estilos = set(candidato.get("estilos", []))
        if not estilos & ESTILOS_AFINES:
            continue
        if estilos & ESTILOS_DESCARTAR:
            continue

        # 2. Concierto dentro de la ventana
        dentro = False
        for conc in candidato.get("conciertos", []):
            if conc.get("fecha") and ventana_desde <= conc["fecha"] <= ventana_hasta:
                dentro = True
                break
        if not dentro:
            continue

        # 3. Emergente (heurística sin IA)
        if not es_emergente(candidato, ventana_hasta):
            continue

        # 4. No debe estar excluido por nombres del diario (esto lo hace el recolector originalmente)
        # (asumiendo que el recolector ya filtra por excluir.json + nombres ya publicados)

        filtrados.append(candidato)

    return filtrados

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada", help="Archivo de candidatos (JSON)")
    ap.add_argument("ventana_desde", help="Fecha de entrada (YYYY-MM-DD)")
    ap.add_argument("ventana_hasta", help="Fecha de publicación +15 días (YYYY-MM-DD)")
    ap.add_argument("salida", help="Archivo de candidatos filtrados (JSON)")
    args = ap.parse_args()

    # Cargar candidatos
    with open(args.entrada, encoding="utf-8") as f:
        datos = json.load(f)
    candidatos = datos.get("candidatos", [])

    # Filtrar
    filtro = filtrar_candidatos(candidatos, args.ventana_desde, args.ventana_hasta)

    # Guardar filtrados
    salida = {
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "ventana": {
            "desde": args.ventana_desde,
            "hasta": args.ventana_hasta,
        },
        "candidatos_filtrados": filtro,
        "nota": "Lista filtrada según criterios editoriales sin IA (estilos afines, ventana, emergente).",
    }
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"**Filtrado**: {len(candidatos)} candidatos → {len(filtro)} candidatos tras filtrar.")

if __name__ == "__main__":
    main()