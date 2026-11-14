#!/usr/bin/env python3
"""Genera la entrada semanal para el diario Radar de salas.

Lee data/candidatos_filtrados.json (o data/candidatos.json) y genera un JSON
con la entrada para la fecha indicada.

Orden de resolución del modelo:
  1. OPENAI_API_KEY  -> OpenAI (o endpoint compatible en OPENAI_BASE_URL)
  2. GITHUB_TOKEN    -> GitHub Models (models.github.ai, OpenAI-compatible)
  3. Sin clave       -> plantilla local sin redacción IA

Uso:
  python3 scripts/ia_generar.py [--entrada data/candidatos_filtrados.json] [--salida /tmp/entrada_ia.json] [--fecha 2026-11-13]
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
import urllib.error

import comun as c


SYSTEM_PROMPT = """Eres el redactor del diario musical "Radar de salas".
Redacta una entrada semanal presentando a los artistas emergentes seleccionados.
Reglas estrictas:
- Nunca inventes enlaces, IDs, fechas ni datos. Usa solo los campos que te doy.
- Tono de diario musical, cercano y directo. No hables del proceso ni de ti.
- Si falta un dato, omite ese campo; no lo inventes.
- "porQue" debe ser una frase corta (máx. 200 caracteres) que enganche.
- "cancion": elige el primer vídeo del canal si existe; si no, deja título y url vacíos.
Devuelve SOLO el JSON, sin texto adicional ni comillas de bloque."""

GITHUB_MODELS_URL = "https://models.github.ai/inference/openai/v1"


def fecha_proxima():
    hoy = dt.date.today()
    return (hoy + dt.timedelta(days=(4 - hoy.weekday()) % 7)).isoformat()


def llamar_modelo(base_url, api_key, modelo, sistema, usuario):
    cuerpo = json.dumps({
        "model": modelo,
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ],
        "temperature": 0.7,
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "radar-salas-workflow",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        datos = json.loads(resp.read().decode("utf-8"))
    texto = datos["choices"][0]["message"]["content"].strip()
    if texto.startswith("```"):
        texto = texto.split("\n", 1)[1]
        if texto.endswith("```"):
            texto = texto[: -3]
    return json.loads(texto.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=os.path.join(c.RAIZ, "data", "candidatos.json"))
    ap.add_argument("--salida", default="/tmp/entrada_ia.json")
    ap.add_argument("--fecha", default=None)
    args = ap.parse_args()

    fecha = args.fecha or fecha_proxima()
    fd = (dt.date.fromisoformat(fecha) - dt.timedelta(days=7)).isoformat()
    fh = (dt.date.fromisoformat(fecha) + dt.timedelta(days=15)).isoformat()

    with open(args.entrada, encoding="utf-8") as f:
        datos = json.load(f)
    candidatos = datos.get("candidatos", [])[:8]

    # 1) OpenAI
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if os.environ.get("OPENAI_API_KEY"):
        entrada = llamar_modelo(
            base, os.environ["OPENAI_API_KEY"],
            os.environ.get("MODEL", "gpt-4o-mini"),
            SYSTEM_PROMPT, _usuario(fecha, fd, fh, candidatos),
        )
        entrada.setdefault("id", fecha)
        _guardar(args.salida, entrada, fecha)
        return

    # 2) GitHub Models (models.github.ai)
    gh_token = (
        os.environ.get("MODELS_TOKEN")
        or os.environ.get("GITHUB_MODELS_TOKEN")
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("INPUT_GITHUBTOKEN")
    )
    if gh_token:
        try:
            entrada = llamar_modelo(
                GITHUB_MODELS_URL, gh_token,
                os.environ.get("MODEL", "gpt-4o-mini"),
                SYSTEM_PROMPT, _usuario(fecha, fd, fh, candidatos),
            )
            entrada.setdefault("id", fecha)
            _guardar(args.salida, entrada, fecha)
            return
        except Exception as e:
            print(f"⚠️ GitHub Models falló ({e}); uso plantilla local", file=sys.stderr)

    # 3) Plantilla local
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
            "foto": a.get("foto", "") or "",
            "videos": yt.get("videos", [])[:2],
        })
    _guardar(args.salida, entrada, fecha)


def _usuario(fecha, fd, fh, candidatos):
    return (
        f"Redacta la entrada semanal del {fecha} (ventana {fd} a {fh}). "
        f"Candidatos con sus datos reales:\n{json.dumps(candidatos, ensure_ascii=False)}"
    )


def _guardar(salida, entrada, fecha):
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(entrada, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"✅ Entrada generada para {fecha} con {len(entrada.get('artistas', []))} artistas")


if __name__ == "__main__":
    main()