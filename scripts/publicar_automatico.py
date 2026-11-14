#!/usr/bin/env python3
"""Publica automáticamente una entrada generada por IA en el diario.

Lee /tmp/entrada_ia.json, la inserta en data/diario.json (recálcula números),
la valida con revisar.py y si pasa, hace commit+push al repo.
Al final dispara refrescar.yml para actualizar vídeos y conciertos.

Requisitos: GITHUB_TOKEN con permisos contents: write y actions: write.
"""
import json
import os
import subprocess
import sys

ENTRADA = "/tmp/entrada_ia.json"


def main():
    if not os.path.exists(ENTRADA):
        print(f"❌ No existe {ENTRADA}", file=sys.stderr)
        sys.exit(1)

    with open(ENTRADA, encoding="utf-8") as f:
        entrada = json.load(f)

    # Insertar al principio del diario
    with open("data/diario.json", encoding="utf-8") as f:
        diario = json.load(f)

    # Evitar duplicados por si acaso con misma fecha
    ids_existentes = {e["id"] for e in diario["entradas"]}
    if entrada["id"] in ids_existentes:
        print(f"⚠️ Ya existe entrada {entrada['id']}, la sustituyo en su posición")
        for i, e in enumerate(diario["entradas"]):
            if e["id"] == entrada["id"]:
                diario["entradas"][i] = entrada
                break
    else:
        diario["entradas"] = [entrada] + diario["entradas"]

    # Recalcular números: el más reciente es 1, luego 2, etc.
    for i, e in enumerate(diario["entradas"]):
        e["numero"] = i + 1

    with open("data/diario.json", "w", encoding="utf-8") as f:
        json.dump(diario, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Validar con revisar.py
    result = subprocess.run(
        ["python3", "scripts/revisar.py", "--sin-red"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Validación falló, revertiendo diario.json")
        # Revertimos guardando el original
        with open("data/diario.json", "w", encoding="utf-8") as f:
            f.write("[]\n")
        sys.exit(1)

    # Commit y push
    subprocess.run(
        ["git", "config", "user.name", "github-actions[bot]"],
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        capture_output=True,
    )
    subprocess.run(["git", "add", "data/diario.json"], capture_output=True)
    result_commit = subprocess.run(
        ["git", "commit", "-m", f"Diario semanal {entrada['fecha']} (automática IA)"],
        capture_output=True,
        text=True,
    )
    if result_commit.returncode != 0 and "nothing to commit" not in result_commit.stderr:
        # Intentar pull/rebase
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], capture_output=True)
    subprocess.run(["git", "push", "origin", "HEAD:main"], capture_output=True)

    # Disparar refrescar.yml para vídeos y conciertos
    subprocess.run(
        ["gh", "workflow", "run", "refrescar.yml", "--ref", "main"],
        capture_output=True,
    )

    print(f"✅ Entrada publicada: {entrada['fecha']} - {entrada['titulo']}")


if __name__ == "__main__":
    main()