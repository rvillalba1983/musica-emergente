"""Utilidades compartidas por los scripts del Radar de salas.

Solo usa la biblioteca estándar de Python. Todas las peticiones pasan por
`descargar()`, que espacia las llamadas a cada web, reintenta con espera
creciente cuando hay bloqueos (429, 503, captchas) y, para YouTube, deja de
intentarlo tras varios fallos seguidos para no empeorar el bloqueo.
"""
import html
import json
import os
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIARIO = os.path.join(RAIZ, "data", "diario.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Pausa mínima (segundos) entre dos peticiones al mismo dominio.
PAUSAS = {
    "www.youtube.com": (6, 10),
    "open.spotify.com": (1.5, 3),
    "conciertos.club": (3, 5),
    "www.conciertosengranada.es": (3, 5),
    "www.escenaensevilla.es": (3, 5),
}
PAUSA_DEFECTO = (2, 4)
REINTENTOS = 4
ESPERA_BASE = 30  # 30 s, 60 s, 120 s…

_ultima = {}
_fallos_seguidos = {}
_cortado = set()
MAX_FALLOS_SEGUIDOS = 3


def log(*a):
    print(*a, file=sys.stderr, flush=True)


class Bloqueado(Exception):
    """La web nos está frenando (429, captcha…)."""


def _esperar_turno(host):
    lo, hi = PAUSAS.get(host, PAUSA_DEFECTO)
    espera = random.uniform(lo, hi) - (time.time() - _ultima.get(host, 0))
    if espera > 0:
        time.sleep(espera)
    _ultima[host] = time.time()


def descargar(url, cabeceras=None):
    """Devuelve el texto de `url` o None si no se pudo (sin lanzar excepción).

    Si un dominio acumula MAX_FALLOS_SEGUIDOS bloqueos, se deja de llamar a él
    durante el resto de la ejecución (devuelve None al instante).
    """
    host = urllib.parse.urlparse(url).netloc
    if host in _cortado:
        return None
    h = {"User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9"}
    if "youtube.com" in host:
        # Evita la pantalla de consentimiento de cookies en IPs de servidores.
        h["Cookie"] = "SOCS=CAI; CONSENT=YES+1"
    h.update(cabeceras or {})
    for intento in range(REINTENTOS):
        _esperar_turno(host)
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=40) as r:
                final = r.geturl()
                texto = r.read().decode("utf-8", "ignore")
            if "youtube.com" in host and ("consent.youtube.com" in final or "/sorry/" in final
                                          or "unusual traffic" in texto[:20000]):
                raise Bloqueado("pantalla de consentimiento o captcha")
            _fallos_seguidos[host] = 0
            return texto
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in (429, 500, 502, 503, 504):
                log(f"  ! {url} → HTTP {e.code}")
                return None
            espera = e.headers.get("Retry-After")
            espera = int(espera) if espera and espera.isdigit() else ESPERA_BASE * 2 ** intento
            motivo = f"HTTP {e.code}"
        except Bloqueado as e:
            espera, motivo = ESPERA_BASE * 2 ** intento, str(e)
        except Exception as e:  # timeouts, conexión cortada…
            espera, motivo = 10 * (intento + 1), type(e).__name__
        if intento < REINTENTOS - 1:
            log(f"  … {host}: {motivo}; espero {espera} s y reintento")
            time.sleep(espera + random.uniform(0, 5))
    _fallos_seguidos[host] = _fallos_seguidos.get(host, 0) + 1
    log(f"  ! no se pudo descargar {url}")
    if _fallos_seguidos[host] >= MAX_FALLOS_SEGUIDOS:
        log(f"  !! {host} bloquea demasiado: dejo de pedirle nada en esta ejecución")
        _cortado.add(host)
    return None


def dominio_cortado(host):
    return host in _cortado


# ---------------------------------------------------------------- texto ---

def normalizar(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slug(s):
    return normalizar(s).replace(" ", "-")


def texto_plano(fragmento):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragmento, flags=re.S)
    t = re.sub(r"<br\s*/?>|</p>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*", "\n", t)).strip()


# ---------------------------------------------------------------- diario ---

def leer_diario():
    with open(DIARIO, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def nombres_publicados(diario):
    return {normalizar(a["nombre"]) for e in diario["entradas"] for a in e["artistas"]}


# --------------------------------------------------------------- agendas ---
# conciertos.club, conciertosengranada.es y escenaensevilla.es usan la misma
# plantilla: cada concierto es un <li> con un bloque de microdatos schema.org.

def _meta(bloque, prop):
    m = re.search(r'itemprop="%s" content="([^"]*)"' % prop, bloque)
    return html.unescape(m.group(1)).strip() if m else ""


def parsear_agenda(pagina, base):
    """Lista de conciertos de una página de agenda (o de ficha de artista)."""
    out = []
    for li in re.findall(r"<li[ >].*?</li>", pagina, flags=re.S):
        if 'itemprop="startDate"' not in li:
            continue
        estilo = re.search(r'class="estilo">\s*/\s*([^<]+)<', li)
        nombre = re.search(r'class="nombre"[^>]*>(.*?)</a>', li, flags=re.S)
        performers = re.findall(
            r'itemprop="performer".*?itemprop="name" content="([^"]*)"', li, flags=re.S)
        loc = re.search(r'itemprop="location".*?itemprop="name" content="([^"]*)"', li, flags=re.S)
        precio = re.search(r'class="precio"[^>]*>([^<]+)<', li) or re.search(
            r'class="precio_wrap">\s*([^<]+?)\s*</span>', li)
        url = _meta(li, "url")
        inicio = _meta(li, "startDate")
        out.append({
            "titulo": texto_plano(nombre.group(1)) if nombre else _meta(li, "name"),
            "artistas": [html.unescape(p).strip() for p in performers] or [_meta(li, "name")],
            "estilo": estilo.group(1).strip() if estilo else "",
            "fecha": inicio[:10],
            "hora": inicio[11:16] if len(inicio) > 10 else "",
            "lugar": html.unescape(loc.group(1)).strip() if loc else "",
            "ciudad": _meta(li, "addressLocality").split(",")[0].strip(),
            "precio": re.sub(r"\s*€", " €", html.unescape(precio.group(1)).strip()) if precio else "",
            "url": urllib.parse.urljoin(base, url) if url else "",
        })
    return out


# --------------------------------------------------------------- YouTube ---

def yt_datos(pagina):
    if not pagina:
        return None
    i = pagina.find("var ytInitialData = ")
    if i < 0:
        return None
    s = pagina.find("{", i)
    e = pagina.find(";</script>", s)
    try:
        return json.loads(pagina[s:e])
    except ValueError:
        return None


def recorrer(o, clave, acc=None):
    acc = [] if acc is None else acc
    if isinstance(o, dict):
        if clave in o:
            acc.append(o[clave])
        for v in o.values():
            recorrer(v, clave, acc)
    elif isinstance(o, list):
        for v in o:
            recorrer(v, clave, acc)
    return acc


def yt_buscar_canal(nombre):
    """Busca el canal oficial cuyo título coincide con el nombre del artista."""
    d = yt_datos(descargar("https://www.youtube.com/results?search_query=" + urllib.parse.quote(nombre)))
    if not d:
        return None
    objetivo = normalizar(nombre)
    candidatos = []
    for c in recorrer(d, "channelRenderer"):
        titulo = (c.get("title") or {}).get("simpleText", "")
        if re.search(r"\b(tema|topic)\b", titulo, re.I):
            continue
        if normalizar(titulo) == objetivo:
            candidatos.append(c.get("channelId"))
    # Si no hay canal con el nombre exacto, el dueño de los vídeos con ese nombre.
    if not candidatos:
        cuenta = {}
        for v in recorrer(d, "videoRenderer")[:10]:
            run = ((v.get("ownerText") or {}).get("runs") or [{}])[0]
            if normalizar(run.get("text", "")) == objetivo:
                cid = run.get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId")
                cuenta[cid] = cuenta.get(cid, 0) + 1
        candidatos = sorted(cuenta, key=cuenta.get, reverse=True)
    return candidatos[0] if candidatos else None


def yt_canal_de_handle(url_canal):
    """De https://www.youtube.com/@handle saca el id UC… del canal."""
    p = descargar(url_canal)
    if not p:
        return None
    m = re.search(r'"externalId":"(UC[\w-]{22})"', p) or re.search(r'"channelId":"(UC[\w-]{22})"', p)
    return m.group(1) if m else None


NO_MUSICA = re.compile(r"\b(vlog|entrevista|intervista|interview|podcast|teaser|trailer|tr[aá]iler)\b", re.I)


def yt_ultimos_videos(channel_id, n=2):
    """Los n vídeos más recientes del canal (saltando vlogs y entrevistas)."""
    d = yt_datos(descargar(f"https://www.youtube.com/channel/{channel_id}/videos"))
    if not d:
        return None
    vids = []
    for r in recorrer(d, "richItemRenderer"):
        c = r.get("content") or {}
        if "lockupViewModel" in c:
            l = c["lockupViewModel"]
            md = l.get("metadata", {}).get("lockupMetadataViewModel", {})
            vid, tit = l.get("contentId"), md.get("title", {}).get("content", "")
        elif "videoRenderer" in c:
            v = c["videoRenderer"]
            vid, tit = v.get("videoId"), "".join(x.get("text", "") for x in v.get("title", {}).get("runs", []))
        else:
            continue
        if vid and len(vid) == 11:
            vids.append({"id": vid, "titulo": tit})
    musicales = [v for v in vids if not NO_MUSICA.search(v["titulo"])] or vids
    # Si varios vídeos son de la misma canción (videoclip, lyric, poema visual…),
    # se queda con el más reciente y pasa a la siguiente canción.
    elegidos, canciones = [], set()
    for v in musicales:
        base = cancion_base(v["titulo"])
        if base in canciones:
            continue
        canciones.add(base)
        elegidos.append(v)
        if len(elegidos) == n:
            break
    return elegidos


def cancion_base(titulo):
    t = re.sub(r"[\(\[].*?[\)\]]", " ", titulo)
    partes = [p for p in re.split(r"\s[-–—|]\s", t) if p.strip()]
    return normalizar(max(partes, key=len) if partes else t)


def yt_redes(channel_id):
    """Enlaces externos que el propio canal muestra en su página «Acerca de»."""
    p = descargar(f"https://www.youtube.com/channel/{channel_id}/about")
    if not p:
        return None
    enlaces = sorted({urllib.parse.unquote(m) for m in re.findall(r'q=(https?%3A%2F%2F[^"&\\]+)', p)})
    handle = re.search(r'"vanityChannelUrl":"https?://www\.youtube\.com/(@[^"]+)"', p)
    return {
        "youtube": f"https://www.youtube.com/{handle.group(1)}" if handle else f"https://www.youtube.com/channel/{channel_id}",
        "enlaces": enlaces,
    }


def clasificar_redes(enlaces):
    redes = {}
    for u in enlaces:
        low = u.lower()
        for clave, patron in (("instagram", "instagram.com/"), ("tiktok", "tiktok.com/@"),
                              ("facebook", "facebook.com/"), ("bandcamp", ".bandcamp.com"),
                              ("spotify", "open.spotify.com/artist/")):
            if patron in low and clave not in redes:
                redes[clave] = u.split("?")[0]
    return redes


# --------------------------------------------------------------- Spotify ---

def spotify_foto(artist_id):
    """Foto de 640 px del artista vía oembed (sin autenticación)."""
    t = descargar("https://open.spotify.com/oembed?url=https://open.spotify.com/artist/" + artist_id)
    try:
        d = json.loads(t or "")
    except ValueError:
        return None
    m = re.search(r"ab67616100005174([0-9a-f]{24})", d.get("thumbnail_url", ""))
    return {"nombre": d.get("title"), "foto": "https://i.scdn.co/image/ab6761610000e5eb" + m.group(1) if m else None}


def resumen_github(texto):
    """Añade texto al resumen visible de la ejecución en GitHub Actions."""
    ruta = os.environ.get("GITHUB_STEP_SUMMARY")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(texto + "\n")
