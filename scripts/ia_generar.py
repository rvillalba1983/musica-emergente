#!/usr/bin/env python3
"""Genera la entrada semanal para el diario Radar de salas.

Lee data/candidatos_filtrados.json (o data/candidatos.json) y genera un JSON
con la entrada para la fecha indicada. Si se llama con --model, intenta una
llamada a API de IA; si no, usa una plantilla local con los candidatos.

Uso:
  python3 scripts/ia_generar.py [--entrada data/candidatos_filtrados.json] [--salida /tmp/entrada_ia.json] [--fecha 2026-11-13]
"""
import argparse
import datetime as dt
import json
import os
import sys

import comun as c


def fecha_proxima():
    hoy = dt.date.today()
    return (hoy + dt.timedelta(days=(4 - hoy.weekday()) % 7)).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=os.path.join(c.RAIZ, "data", "candidatos.json"))
    ap.add_argument("--salida", default="/tmp/entrada_ia.json")
    ap.add_argument("--fecha", default=None)
    args = ap.parse_args()

    fecha = args.fecha or fecha_proxima()
    import datetime as dt2
    fd = (dt2.date.fromisoformat(fecha) - dt2.timedelta(days=7)).isoformat()
    fh = (dt2.date.fromisoformat(fecha) + dt2.timedelta(days=15)).isoformat()

    with open(args.entrada, encoding="utf-8") as f:
        datos = json.load(f)
    candidatos = datos.get("candidatos", [])[:5]

    entrada = {
        "id": fecha,
        "numero": 5,
        "fecha": fecha,
        "titulo": "Semana de artistas emergentes",
        "intro": f"{len(candidatos)} artistas con conciertos entre {fd} y {fh}.",
        "ventana": {"desde": fd, "hasta": fh},
        "artistas": [],
    }

    for a in candidatos:
        yt = a.get("youtube") or {}
        sp = a.get("spotify") or {}
        entrada["artistas"].append({
            "nombre": a.get("nombre", ""),
            "origen": a.get("origen", ""),
            "estilo": a.get("estilos", [])[:3],
            "porQue": (a.get("bio", "")[:250] if a.get("bio") else "Artista emergente con concierto en la ventana."),
            "cancion": {"titulo": "", "url": ""},
            "conciertos": a.get("conciertos", [])[:3],
            "redes": a.get("redes_enlazadas", {}),
            "youtubeChannelId": yt.get("channelId", ""),
            "spotifyId": sp.get("id", "")[:22] if sp.get("id") else "",
            "foto": "",
            "videos": yt.get("videos", [])[:2],
        })

    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(entrada, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"✅ Entrada generada para {fecha} con {len(candidatos)} artistas")


if __name__ == "__main__":
    main()