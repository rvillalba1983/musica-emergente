#!/usr/bin/env python3
"""Sincroniza datos del diario con Supabase (si está configurado).

Puede:
1. Subir data/diario.json a Supabase (tabla entradas)
2. Subir data/rechazados.json a Supabase (tabla rechazados)

Requiere variables de entorno: SUPABASE_URL y SUPABASE_SERVICE_KEY

Uso:
  export SUPABASE_URL="https://tu-proyecto.supabase.co"
  export SUPABASE_SERVICE_KEY="tu_clave_servicio"

  python3 scripts/sync_supabase.py --subir-diario data/diario.json
  python3 scripts/sync_supabase.py --subir-rechazados data/rechazados.json
"""
import argparse
import json
import os
import sys
import unicodedata
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("⚠️ Define SUPABASE_URL y SUPABASE_SERVICE_KEY antes de usar este script")

import urllib.request
import urllib.error


def normalizar_nombre(nombre):
    s = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def supabase_post(path, datos):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    payload = json.dumps(datos).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def subir_diario(ruta_diario):
    """Subir entradas del diario a Supabase."""
    with open(ruta_diario, encoding="utf-8") as f:
        diario = json.load(f)

    entradas = diario.get("entradas", [])
    errores = 0
    for e in entradas:
        status, body = supabase_post(
            "entradas",
            {
                "fecha": e.get("fecha"),
                "numero": e.get("numero"),
                "titulo": e.get("titulo"),
                "intro": e.get("intro"),
                "ventana_desde": e.get("ventana", {}).get("desde"),
                "ventana_hasta": e.get("ventana", {}).get("hasta"),
                "artistas": e.get("artistas", []),
            },
        )
        if status not in (200, 201):
            print(f"❌ Entrada {e.get('id')} ({e.get('numero')}): HTTP {status} - {body[:200]}")
            errores += 1
        else:
            print(f"✅ Entrada Nº {e.get('numero')} ({e.get('fecha')}) subida")

    print(f"\n{len(entradas) - errores} entradas subidas, {errores} errores")


def subir_rechazados(ruta_rechazados):
    """Subir artistas rechazados a Supabase."""
    with open(ruta_rechazados, encoding="utf-8") as f:
        datos = json.load(f)

    rechazados = datos.get("nombres", [])
    errores = 0
    for r in rechazados:
        status, body = supabase_post(
            "rechazados",
            {
                "nombre": r.get("nombre"),
                "motivo": r.get("motivo"),
                "origen": r.get("origen"),
            },
        )
        if status not in (200, 201):
            print(f"❌ Rechazado {r.get('nombre')}: HTTP {status} - {body[:200]}")
            errores += 1
        else:
            print(f"✅ Rechazado {r.get('nombre')} ({r.get('motivo')}) subido")

    print(f"\n{len(rechazados) - errores} rechazados subidos, {errores} errores")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subir-diario", metavar="RUTA", help="Subir diario.json a Supabase")
    ap.add_argument("--subir-rechazados", metavar="RUTA", help="Subir rechazados.json a Supabase")
    args = ap.parse_args()

    if not args.subir_diario and not args.subir_rechazados:
        print("Debes indicar --subir-diario o --subir-rechazados")
        sys.exit(2)

    if args.subir_diario:
        subir_diario(args.subir_diario)
    if args.subir_rechazados:
        subir_rechazados(args.subir_rechazados)


if __name__ == "__main__":
    main()