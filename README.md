# Radar de salas

Diario semanal de artistas emergentes con conciertos en bares, salas, festivales y pueblos de España y Latinoamérica. Cada viernes se publica una entrada nueva; la última se ve al entrar y las anteriores quedan debajo.

**Web:** https://rvillalba1983.github.io/musica-emergente/

- `data/diario.json`: todas las entradas y artistas.
- `index.html`, `assets/`: la web (HTML, CSS y JS estático, sin build).
- `CLAUDE.md`: el procedimiento para añadir la entrada semanal.
- `scripts/` y `.github/workflows/`: tareas automáticas de GitHub Actions. Los jueves recogen candidatos de las agendas (`data/candidatos.json`), los miércoles actualizan vídeos y conciertos de los artistas publicados, y tras cada cambio revisan que no haya nada roto.
- `data/excluir.json`: nombres que el recolector no debe proponer.
