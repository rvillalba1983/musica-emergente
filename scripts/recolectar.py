"""Prepara data/candidatos.json para la entrada del viernes.

1. Lee las agendas (conciertosengranada.es, conciertos.club por provincias y
   escenaensevilla.es) y se queda con los conciertos de estilos afines dentro de
   la ventana: fecha de publicación − 7 días … + 15 días.
2. Quita a quien ya salió en el diario o está en data/excluir.json.
3. Para cada candidato baja la ficha del concierto (biografía), y busca su canal
   de YouTube (últimos vídeos y redes enlazadas) y su Spotify si lo enlaza.

No elige ni escribe nada: eso lo hace la IA leyendo el archivo resultante.

Uso: python3 scripts/recolectar.py [--fecha AAAA-MM-DD] [--max-youtube N]
"""
import argparse
import datetime as dt
import json
import os
import re

import comun as c

ESTILOS = {"Cantautores", "Mestizaje/Fusión", "Flamenco/Copla", "Folk", "Música Latina",
           "Pop Latino", "Rumba", "Canción de autor", "Música de Autor"}
DESCARTAR = re.compile(r"candlelight|tributo|espect[aá]culo flamenco|tablao|jam session|"
                       r"karaoke|open mic|micro abierto|homenaje", re.I)
PROVINCIAS = ["almeria", "cadiz", "cordoba", "huelva", "jaen", "malaga", "madrid",
              "barcelona", "valencia", "murcia", "alicante", "zaragoza", "asturias",
              "bilbao-bizkaia", "a-coruna", "pontevedra-vigo", "valladolid"]
ANDALUCIA = {"almeria", "cadiz", "cordoba", "huelva", "jaen", "malaga", "sevilla", "granada"}
EXCLUIR = os.path.join(c.RAIZ, "data", "excluir.json")
SALIDA = os.path.join(c.RAIZ, "data", "candidatos.json")


def proximo_viernes(hoy):
    return hoy + dt.timedelta(days=(4 - hoy.weekday()) % 7)


def agenda_granada(desde, hasta):
    url = ("https://www.conciertosengranada.es/search.php?fecha1=%d/%d/%d&fecha2=%d/%d/%d"
           % (desde.day, desde.month, desde.year, hasta.day, hasta.month, hasta.year))
    p = c.descargar(url)
    return [dict(x, zona="Granada") for x in c.parsear_agenda(p or "", "https://www.conciertosengranada.es/")]


def agenda_provincia(prov):
    if prov == "sevilla":
        url, base = "https://www.escenaensevilla.es/", "https://www.escenaensevilla.es/"
    else:
        url, base = f"https://conciertos.club/{prov}", "https://conciertos.club/"
    p = c.descargar(url)
    zona = "Andalucía" if prov in ANDALUCIA else "España"
    return [dict(x, zona=zona) for x in c.parsear_agenda(p or "", base)]


def ficha(url):
    """Texto descriptivo de la ficha del concierto (biografía del artista)."""
    p = c.descargar(url) if url else None
    if not p:
        return ""
    m = re.search(r"<!--\s*content\s*-->(.*?)(Buscar Alojamiento|Conciertos destacados)", p, flags=re.S)
    trozo = m.group(1) if m else ""
    if not trozo:
        m = re.search(r'class="(?:texto|descripcion|txt)[^"]*"[^>]*>(.*?)</div>', p, flags=re.S)
        trozo = m.group(1) if m else ""
    t = c.texto_plano(trozo)
    return t[:1500]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fecha", help="fecha de publicación (por defecto, el próximo viernes)")
    ap.add_argument("--max-youtube", type=int, default=30,
                    help="como mucho, a cuántos candidatos se les busca YouTube")
    args = ap.parse_args()

    fecha = dt.date.fromisoformat(args.fecha) if args.fecha else proximo_viernes(dt.date.today())
    desde, hasta = fecha - dt.timedelta(days=7), fecha + dt.timedelta(days=15)
    c.log(f"Ventana {desde} → {hasta} (entrada del {fecha})")

    diario = c.leer_diario()
    vetados = c.nombres_publicados(diario)
    excluir = []
    if os.path.exists(EXCLUIR):
        with open(EXCLUIR, encoding="utf-8") as f:
            excluir = json.load(f).get("nombres", [])
    vetados |= {c.normalizar(n) for n in excluir}

    conciertos = agenda_granada(desde, hasta)
    c.log(f"Granada: {len(conciertos)} conciertos")
    for prov in ["sevilla"] + PROVINCIAS:
        lista = agenda_provincia(prov)
        c.log(f"{prov}: {len(lista)} conciertos")
        conciertos += lista

    # Agrupa por artista los conciertos de estilos afines dentro de la ventana.
    por_artista = {}
    for x in conciertos:
        if not x["fecha"] or not (desde.isoformat() <= x["fecha"] <= hasta.isoformat()):
            continue
        if x["estilo"] not in ESTILOS or DESCARTAR.search(x["titulo"]):
            continue
        for nombre in x["artistas"]:
            if not nombre or DESCARTAR.search(nombre):
                continue
            clave = c.normalizar(nombre)
            if clave in vetados:
                continue
            a = por_artista.setdefault(clave, {"nombre": nombre, "estilos": set(), "zona": x["zona"], "conciertos": []})
            a["estilos"].add(x["estilo"])
            if x["zona"] == "Granada" or (x["zona"] == "Andalucía" and a["zona"] == "España"):
                a["zona"] = x["zona"]
            con = {k: x[k] for k in ("fecha", "hora", "lugar", "ciudad", "precio", "url") if x[k]}
            if con not in a["conciertos"]:
                a["conciertos"].append(con)

    orden = {"Granada": 0, "Andalucía": 1, "España": 2}
    candidatos = sorted(por_artista.values(), key=lambda a: (orden[a["zona"]], a["conciertos"][0]["fecha"]))
    c.log(f"{len(candidatos)} candidatos tras filtrar")

    for i, a in enumerate(candidatos):
        a["estilos"] = sorted(a["estilos"])
        a["conciertos"].sort(key=lambda x: x["fecha"])
        a["bio"] = ficha(a["conciertos"][0].get("url"))
        if i >= args.max_youtube or c.dominio_cortado("www.youtube.com"):
            a["youtube"] = None
            continue
        c.log(f"[{i + 1}/{len(candidatos)}] {a['nombre']}")
        cid = c.yt_buscar_canal(a["nombre"])
        if not cid:
            a["youtube"] = None
            continue
        info = c.yt_redes(cid) or {}
        redes = c.clasificar_redes(info.get("enlaces", []))
        a["youtube"] = {"channelId": cid, "url": info.get("youtube"), "videos": c.yt_ultimos_videos(cid) or [],
                        "enlaces": info.get("enlaces", [])}
        a["redes_enlazadas"] = redes
        sp = redes.get("spotify")
        m = re.search(r"artist/([A-Za-z0-9]{22})", sp or "")
        if m:
            a["spotify"] = dict(id=m.group(1), **(c.spotify_foto(m.group(1)) or {}))

    salida = {
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "fecha_entrada": fecha.isoformat(),
        "ventana": {"desde": desde.isoformat(), "hasta": hasta.isoformat()},
        "aviso": ("Lista automática SIN revisar: el canal de YouTube y el Spotify se han emparejado por "
                  "nombre y pueden ser de otro artista homónimo. Compruébalo antes de publicar."),
        "youtube_bloqueado": c.dominio_cortado("www.youtube.com"),
        "candidatos": candidatos,
    }
    c.guardar_json(SALIDA, salida)
    con_yt = sum(1 for a in candidatos if a.get("youtube"))
    msg = (f"**Candidatos para la entrada del {fecha}:** {len(candidatos)} "
           f"({sum(a['zona'] == 'Granada' for a in candidatos)} en Granada, "
           f"{sum(a['zona'] == 'Andalucía' for a in candidatos)} en el resto de Andalucía); "
           f"{con_yt} con canal de YouTube.")
    if salida["youtube_bloqueado"]:
        msg += " ⚠️ YouTube bloqueó las peticiones a mitad: faltan vídeos."
    c.log(msg)
    c.resumen_github(msg)


if __name__ == "__main__":
    main()
