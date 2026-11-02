"""Pone al día a los artistas ya publicados en data/diario.json.

- Vídeos: sustituye los 2 vídeos por los 2 últimos del canal oficial cuando
  el artista ha subido algo nuevo (solo si YouTube responde bien; si bloquea,
  no toca nada).
- Conciertos: añade las fechas futuras nuevas que aparezcan en la ficha del
  artista en conciertos.club. Nunca borra fechas.
- Fotos: si una foto de Spotify ha dejado de existir, pide la actual.

Uso: python3 scripts/refrescar.py [--sin-youtube] [--sin-conciertos]
"""
import argparse
import datetime as dt
import re
import urllib.request

import comun as c


def limpiar_titulo(titulo, artista):
    """Quita el nombre del artista y coletillas del título de YouTube."""
    t = titulo
    nombre = re.escape(artista)
    t = re.sub(r"^\s*%s\s*[-–—|:]\s*" % nombre, "", t, flags=re.I)
    t = re.sub(r"\s*[-–—|]\s*%s\s*$" % nombre, "", t, flags=re.I)
    t = t.strip(" -–—|")
    if t.isupper() and len(t) > 4:
        t = t.capitalize()
    return t or titulo


def canal(a):
    if a.get("youtubeChannelId"):
        return a["youtubeChannelId"]
    yt = (a.get("redes") or {}).get("youtube", "")
    m = re.search(r"/channel/(UC[\w-]{22})", yt)
    if m:
        return m.group(1)
    if "youtube.com/@" in yt:
        cid = c.yt_canal_de_handle(yt)
        if cid:
            a["youtubeChannelId"] = cid  # se guarda para no volver a buscarlo
        return cid
    return None


def refrescar_videos(a, cambios):
    cid = canal(a)
    if not cid:
        return
    nuevos = c.yt_ultimos_videos(cid)
    if not nuevos or len(nuevos) < min(2, len(a.get("videos") or [])):
        return
    actuales = {v["id"]: v for v in a.get("videos") or []}
    if [v["id"] for v in nuevos] == list(actuales):
        return
    a["videos"] = [actuales.get(v["id"]) or {"id": v["id"], "titulo": limpiar_titulo(v["titulo"], a["nombre"])}
                   for v in nuevos]
    cambios.append(f"{a['nombre']}: vídeos nuevos → " + ", ".join(v["titulo"] for v in a["videos"]))


def refrescar_conciertos(a, hoy, cambios):
    url = "https://conciertos.club/artistas/" + c.slug(a["nombre"])
    p = c.descargar(url)
    if not p:
        return
    titulo = re.search(r"<title>(.*?)</title>", p, flags=re.S)
    if not titulo or c.normalizar(a["nombre"]) not in c.normalizar(titulo.group(1)):
        return
    existentes = {(x["fecha"], c.normalizar(x.get("ciudad", ""))) for x in a.get("conciertos") or []}
    fechas_existentes = {x["fecha"] for x in a.get("conciertos") or []}
    nuevos = []
    for x in c.parsear_agenda(p, "https://conciertos.club/"):
        if not x["fecha"] or x["fecha"] < hoy:
            continue
        if c.normalizar(a["nombre"]) not in {c.normalizar(n) for n in x["artistas"]}:
            continue
        clave = (x["fecha"], c.normalizar(x["ciudad"]))
        if clave in existentes or x["fecha"] in fechas_existentes:
            continue
        con = {k: x[k] for k in ("fecha", "hora", "lugar", "ciudad", "precio") if x[k]}
        con["url"] = url
        nuevos.append(con)
        existentes.add(clave)
    if nuevos:
        a.setdefault("conciertos", []).extend(nuevos)
        a["conciertos"].sort(key=lambda x: x["fecha"])
        cambios.append(f"{a['nombre']}: {len(nuevos)} concierto(s) nuevo(s) → "
                       + ", ".join(f"{x['fecha']} {x.get('ciudad', '')}" for x in nuevos))


def foto_viva(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": c.UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def refrescar_foto(a, cambios):
    if not a.get("foto") or not a.get("spotifyId") or foto_viva(a["foto"]):
        return
    nueva = (c.spotify_foto(a["spotifyId"]) or {}).get("foto")
    if nueva and nueva != a["foto"]:
        a["foto"] = nueva
        cambios.append(f"{a['nombre']}: foto actualizada")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-youtube", action="store_true")
    ap.add_argument("--sin-conciertos", action="store_true")
    args = ap.parse_args()

    hoy = dt.date.today().isoformat()
    diario = c.leer_diario()
    cambios = []
    artistas = [a for e in diario["entradas"] for a in e["artistas"]]
    for i, a in enumerate(artistas):
        c.log(f"[{i + 1}/{len(artistas)}] {a['nombre']}")
        refrescar_foto(a, cambios)
        if not args.sin_conciertos:
            refrescar_conciertos(a, hoy, cambios)
        if not args.sin_youtube and not c.dominio_cortado("www.youtube.com"):
            refrescar_videos(a, cambios)

    if cambios:
        c.guardar_json(c.DIARIO, diario)
    titulo = f"**Refresco del diario ({hoy}):** {len(cambios)} cambio(s)."
    if c.dominio_cortado("www.youtube.com"):
        titulo += " ⚠️ YouTube bloqueó las peticiones: algunos vídeos no se han revisado."
    texto = "\n".join([titulo] + [f"- {x}" for x in cambios])
    c.log(texto)
    c.resumen_github(texto)


if __name__ == "__main__":
    main()
