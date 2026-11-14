#!/usr/bin/env python3
"""Crea un GitHub Issue con la entrada generada por IA para su revisión.

Lee /tmp/entrada_ia.json y crea un issue en rvillalba1983/musica-emergente
con el JSON completo e instrucciones para publicarlo.

Requiere: GITHUB_TOKEN en entorno (lo da GitHub Actions automáticamente).
"""
import json
import os
import subprocess
import sys

ENTRADA = "/tmp/entrada_ia.json"


def main():
    if not os.path.exists(ENTRADA):
        print(f"No existe {ENTRADA}", file=sys.stderr)
        sys.exit(1)

    with open(ENTRADA, encoding="utf-8") as f:
        e = json.load(f)

    fecha = e.get("fecha", "?")
    titulo = e.get("titulo", "Sin título")
    cuerpo = (
        "Entrada generada automaticamente por IA. Revisar y, si esta bien, publicar con:\n"
        "\n"
        "gh workflow run publicar.yml --field fecha=\"{fecha}\" --field entrada='{entrada}'\n"
        "\n"
        "JSON completo:\n"
        "\n"
        "{json}\n"
    ).format(
        fecha=fecha,
        entrada=json.dumps(e, ensure_ascii=False),
        json=json.dumps(e, ensure_ascii=False, indent=2),
    )

    cmd = [
        "gh", "issue", "create",
        "--title", "Entrada semanal " + fecha + ": " + titulo,
        "--body", cuerpo,
        "--label", "diario-semanal",
        "--label", "ia-generado",
        "--repo", "rvillalba1983/musica-emergente",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()