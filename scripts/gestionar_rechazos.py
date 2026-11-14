#!/usr/bin/env python3
"""Gestiona la lista de artistas rechazados para no volver a proponerlos.

Permite a Claude añadir rechazados con motivo, consultar la lista
y quitarlos cuando se decida.

Archivo: data/rechazados.json
Formato:
{
  "nota": "...",
  "nombres": [
    {
      "nombre": "Nombre del artista",
      "motivo": "muy_famoso | estilo_no_afin | concierto_fuera_ventana | homonimo | falta_facebook_verificado | ...",
      "fecha_rechazo": "2026-11-08",
      "origen": "Granada" | "Andalucía" | "España" | null
    }
  ]
}

Uso:
  python3 scripts/gestionar_rechazos.py --list        # mostrar todos los rechazados
  python3 scripts/gestionar_rechazos.py --add "Artista" "motivo"  # añadir uno
  python3 scripts/gestionar_rechazos.py --remove "Artista"  # quitar uno
  python3 scripts/gestionar_rechazos.py --clear           # borrar todos (admin)
"""
import argparse
import datetime as dt
import json
import os
import sys
import unicodedata
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECHAZADOS_PATH = os.path.join(RAIZ, "data", "rechazados.json")


def normalizar_nombre(nombre):
    """Normalizar nombre para comparacion (como hace comun.py)."""
    s = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def cargar_rechazados():
    """Cargar la lista de rechazados desde el archivo JSON."""
    if os.path.exists(RECHAZADOS_PATH):
        with open(RECHAZADOS_PATH, encoding="utf-8") as f:
            datos = json.load(f)
        return datos.get("nombres", [])
    return [] if not os.path.exists(RECHAZADOS_PATH) else []


def guardar_rechazados(nombres):
    """Guardar la lista de rechazados en el archivo JSON."""
    datos = {
        "nota": "Artistas rechazados por motivos editoriales (no vuelven a aparecer en candidatos hasta que se quite de aqui).",
        "nombres": nombres
    }
    with open(RECHAZADOS_PATH, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def listar_rechazados():
    """Mostrar todos los rechazados."""
    nombres = cargar_rechazados()
    if not nombres:
        print("No hay artistas rechazados en la lista.")
        return
    print(f"Total rechazados: {len(nombres)}\n")
    for i, r in enumerate(nombres, 1):
        print(f"{i}. {r['nombre']}")
        print(f"   Motivo: {r['motivo']}")
        if r.get("fecha_rechazo"):
            print(f"   Fecha: {r['fecha_rechazo']}")
        if r.get("origen"):
            print(f"   Origen: {r['origen']}")
        print()


def anadir_rechazado(nombre, motivo, origen=None):
    """Anadir un nuevo rechazado a la lista."""
    nombres = cargar_rechazados()
    # Verificar si ya existe
    norm_nuevo = normalizar_nombre(nombre)
    for r in nombres:
        if normalizar_nombre(r["nombre"]) == norm_nuevo:
            print(f"AVISO: '{nombre}' ya esta en la lista de rechazados (motivo: {r['motivo']})")
            return False

    # Anadir nuevo
    fecha_rechazo = dt.date.today().isoformat()
    nuevo = {
        "nombre": nombre,
        "motivo": motivo,
        "fecha_rechazo": fecha_rechazo,
        "origen": origen
    }
    nombres.append(nuevo)
    guardar_rechazados(nombres)
    print(f"OK '{nombre}' anadido a rechazados (motivo: {motivo})")
    return True


def quitar_rechazado(nombre):
    """Quitar un rechazado de la lista."""
    nombres = cargar_rechazados()
    norm_nuevo = normalizar_nombre(nombre)
    longitud_antes = len(nombres)
    nombres = [r for r in nombres if normalizar_nombre(r["nombre"]) != norm_nuevo]
    if len(nombres) < longitud_antes:
        guardar_rechazados(nombres)
        print(f"OK '{nombre}' quitado de la lista de rechazados")
        return True
    else:
        print(f"AVISO: '{nombre}' no encontrado en la lista de rechazados")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="Mostrar todos los rechazados")
    ap.add_argument("--add", nargs=2, metavar=("NOMBRE", "MOTIVO"),
                    help="Anadir un nuevo rechazado (nombre y motivo)")
    ap.add_argument("--remove", metavar="NOMBRE",
                    help="Quitar un rechazado de la lista")
    ap.add_argument("--clear", action="store_true", help="Borrar todos los rechazados (ADMIN)")
    args = ap.parse_args()

    if args.list:
        listar_rechazados()
    elif args.add:
        nombre, motivo = args.add
        anadir_rechazado(nombre, motivo)
    elif args.remove:
        quitar_rechazado(args.remove)
    elif args.clear:
        print("ATENCION: Esto borrara TODOS los rechazados de la lista.")
        confirm = input("Estas seguro? (s/N): ")
        if confirm.lower() == 's':
            guardar_rechazados([])
            print("OK Lista de rechazados borrada")
        else:
            print("Operacion cancelada")
    else:
        print("Opcion no valida. Usa --list para ver, --add para anadir, --remove para quitar, --clear para borrar todo")


if __name__ == "__main__":
    main()