"""Comprueba que data/diario.json está bien y que la web no tiene nada roto.

- Estructura: campos obligatorios, fechas válidas, números de entrada
  seguidos, artistas repetidos, IDs de Spotify y YouTube con formato correcto.
- Enlaces: que cargan las fotos y las miniaturas de los vídeos.

Sale con código 1 si hay errores (GitHub avisa por correo de la ejecución
fallida). Los avisos no hacen fallar.

Uso: python3 scripts/revisar.py [--sin-red]
"""
import argparse
import datetime as dt
import re
import sys
import time
import urllib.error
import urllib.request

import comun as c

CAMPOS_ENTRADA = ("id", "numero", "fecha", "titulo", "intro", "artistas")
CAMPOS_ARTISTA = ("nombre", "estilo", "porQue")
REDES = {"spotify", "youtube", "instagram", "tiktok", "facebook", "bandcamp", "web"}
PROHIBIDO = re.compile(r"no he encontrado|no encontr[eé]|sin verificar|no verificad|"
                       r"tus gustos|que escuchas|tu spotify|el dueño", re.I)


def fecha_ok(s):
    try:
        dt.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def carga(url):
    for intento in range(3):
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": c.UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code != 429:
                return e.code
        except Exception:
            pass
        time.sleep(5 * (intento + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-red", action="store_true", help="no comprueba fotos ni miniaturas")
    args = ap.parse_args()

    errores, avisos = [], []
    try:
        diario = c.leer_diario()
    except ValueError as e:
        print(f"ERROR: data/diario.json no es un JSON válido: {e}")
        sys.exit(1)

    entradas = diario.get("entradas", [])
    numeros = sorted(e.get("numero", 0) for e in entradas)
    if numeros != list(range(1, len(entradas) + 1)):
        errores.append(f"Los números de entrada no van seguidos: {numeros}")
    vistos = {}
    urls = []
    for e in entradas:
        n = e.get("numero")
        for k in CAMPOS_ENTRADA:
            if not e.get(k):
                errores.append(f"Nº {n}: falta «{k}»")
        if not fecha_ok(e.get("fecha")):
            errores.append(f"Nº {n}: fecha no válida «{e.get('fecha')}»")
        v = e.get("ventana")
        if v and not (fecha_ok(v.get("desde")) and fecha_ok(v.get("hasta"))):
            errores.append(f"Nº {n}: ventana no válida")
        for campo in ("titulo", "intro"):
            if PROHIBIDO.search(e.get(campo, "")):
                avisos.append(f"Nº {n}: el {campo} parece hablar del proceso o de los gustos del dueño")
        for a in e.get("artistas", []):
            nom = a.get("nombre", "?")
            clave = c.normalizar(nom)
            if clave in vistos:
                errores.append(f"«{nom}» aparece en el Nº {vistos[clave]} y en el Nº {n}")
            vistos[clave] = n
            for k in CAMPOS_ARTISTA:
                if not a.get(k):
                    errores.append(f"Nº {n} · {nom}: falta «{k}»")
            if not a.get("origen"):
                avisos.append(f"Nº {n} · {nom}: sin origen")
            if PROHIBIDO.search(a.get("porQue", "")):
                avisos.append(f"Nº {n} · {nom}: el texto parece hablar del proceso o de los gustos del dueño")
            if a.get("spotifyId") and not re.fullmatch(r"[A-Za-z0-9]{22}", a["spotifyId"]):
                errores.append(f"Nº {n} · {nom}: spotifyId con formato raro")
            for r in (a.get("redes") or {}):
                if r not in REDES:
                    avisos.append(f"Nº {n} · {nom}: red desconocida «{r}» (la web no la pinta)")
            for x in a.get("conciertos") or []:
                if not fecha_ok(x.get("fecha")):
                    errores.append(f"Nº {n} · {nom}: concierto con fecha no válida «{x.get('fecha')}»")
                if not x.get("lugar"):
                    errores.append(f"Nº {n} · {nom}: concierto sin lugar")
            if v and a.get("conciertos") and not any(v["desde"] <= x.get("fecha", "") <= v["hasta"] for x in a["conciertos"]):
                avisos.append(f"Nº {n} · {nom}: ningún concierto dentro de la ventana")
            vids = a.get("videos") or []
            for x in vids:
                if not re.fullmatch(r"[\w-]{11}", x.get("id", "")):
                    errores.append(f"Nº {n} · {nom}: id de vídeo no válido «{x.get('id')}»")
                else:
                    urls.append((f"Nº {n} · {nom}: miniatura del vídeo {x['id']}", f"https://i.ytimg.com/vi/{x['id']}/hqdefault.jpg"))
            if len({x.get('id') for x in vids}) < len(vids):
                errores.append(f"Nº {n} · {nom}: vídeo repetido")
            if not vids and not a.get("youtubeChannelId"):
                avisos.append(f"Nº {n} · {nom}: sin vídeos")
            if a.get("foto"):
                urls.append((f"Nº {n} · {nom}: foto", a["foto"]))
            else:
                avisos.append(f"Nº {n} · {nom}: sin foto (salen las iniciales)")

    if not args.sin_red:
        for desc, u in urls:
            st = carga(u)
            if st != 200:
                errores.append(f"{desc} no carga (HTTP {st}): {u}")

    lineas = [f"**Revisión del diario:** {len(entradas)} entradas, {len(vistos)} artistas, "
              f"{len(errores)} error(es), {len(avisos)} aviso(s)."]
    lineas += [f"- ❌ {x}" for x in errores] + [f"- ⚠️ {x}" for x in avisos]
    texto = "\n".join(lineas)
    print(texto)
    c.resumen_github(texto)
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
