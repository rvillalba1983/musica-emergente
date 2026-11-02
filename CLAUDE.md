# Radar de salas: cómo se actualiza

Web estática publicada en GitHub Pages: https://rvillalba1983.github.io/musica-emergente/
Todo el contenido está en `data/diario.json`. `index.html` + `assets/app.js` lo pintan (no hay build).

Todas las entradas, nuevas y antiguas, se pintan con el mismo formato completo (foto, conciertos, redes, reproductor de Spotify y 2 vídeos). Cualquier artista que se añada o retoque debe llevar todos los campos de abajo.

## Scripts automáticos (GitHub Actions, sin IA)

En `scripts/` (Python sin dependencias) y `.github/workflows/`:

- `recolectar.py` (jueves por la tarde): lee las agendas (conciertosengranada.es, conciertos.club por provincias, escenaensevilla.es), filtra estilos afines dentro de la ventana del próximo viernes, quita a quien ya salió o está en `data/excluir.json`, y deja en `data/candidatos.json` cada candidato con sus conciertos, la biografía de la ficha y, si lo encuentra, su canal de YouTube (últimos vídeos y redes enlazadas) y su Spotify. **Es una lista sin revisar**: el canal y el Spotify se emparejan por nombre y pueden ser de un homónimo.
- `refrescar.py` (miércoles): actualiza los 2 últimos vídeos de cada artista publicado, añade fechas nuevas de conciertos.club (nunca borra) y repone fotos caídas.
- `revisar.py` (tras cada cambio del diario y tras el refresco): comprueba campos, fechas, repetidos, formatos de ID y que cargan fotos y miniaturas. Si falla, GitHub avisa por correo.

Todos van despacio a propósito (pausas de 6-10 s con YouTube y 3-5 s con las agendas), reintentan con espera creciente ante un 429 y, si YouTube bloquea 3 veces seguidas, dejan de llamarle en esa ejecución sin tocar los datos que ya había. Se pueden lanzar a mano en la pestaña Actions del repo ("Run workflow") o en local: `python3 scripts/revisar.py`.

## Entrada semanal (cada viernes)

0. Antes de buscar nada, haz `git pull` y lee `data/candidatos.json`: si es de esta semana (`fecha_entrada`), parte de esa lista y comprueba cada candidato antes de usarlo (que el YouTube y el Spotify son de ese artista, que encaja y que es emergente). Completa por tu cuenta lo que falte o si `youtube_bloqueado` es true. Si eliges a alguien que el dueño ya sigue o que no debe salir nunca, añádelo a `data/excluir.json`.

1. Añade una entrada NUEVA al principio de `entradas` en `data/diario.json`, sin tocar las anteriores.
   - `id` y `fecha`: fecha de publicación (AAAA-MM-DD). `numero`: el siguiente al último.
   - `ventana.desde` = fecha − 7 días, `ventana.hasta` = fecha + 15 días.
   - `titulo`: frase corta que resuma la tanda. `intro`: 1-3 frases (qué hay en Granada/Andalucía).
   - Tono de diario musical para cualquier lector: NADA de comentarios sobre cómo se ha hecho la selección, criterios, búsquedas, huecos ("no he encontrado…"), dudas de verificación, ni referencias a los gustos o al Spotify del dueño. Si un dato no está verificado, no lo pongas. Los huecos y dudas se cuentan solo en el mensaje privado al usuario, no en la web.
2. Criterio de artistas (5 por semana):
   - Emergentes de verdad: primeras giras, EP o primeros discos, circuitos tipo Girando Por Salas o Radar Joven. Nada de veteranos ni artistas que llenan teatros.
   - Con al menos un concierto DENTRO de la ventana. Busca en salas y bares, festivales, ciclos de cantautores, conciertos en pueblos y asociaciones culturales, en España y Latinoamérica.
   - Que encajen con el perfil: canción de autor, rumba, flamenco y flamenquito, mestizaje; letras en castellano preferiblemente.
   - Que no hayan salido en ninguna entrada anterior.
3. Campos por artista (mira las entradas existentes como ejemplo):
   - `nombre`, `origen`, `estilo` (2-3 etiquetas), `porQue` (2-4 frases: quién es, qué hace y dónde toca; sin comparar con los artistas que escucha el dueño).
   - `foto`: `https://open.spotify.com/oembed?url=https://open.spotify.com/artist/<ID>` devuelve `thumbnail_url`; usa `https://i.scdn.co/image/<hash>` cambiando el prefijo `ab67616100005174` por `ab6761610000e5eb` (640 px).
   - `spotifyId` (se incrusta el reproductor del artista), `cancion` {titulo, url}.
   - `conciertos`: [{fecha, hora, lugar, ciudad, precio, url}]. Incluye también las fechas fuera de la ventana si las hay.
   - `redes`: spotify, youtube, instagram, tiktok, facebook, bandcamp, web (solo las que existan y estén verificadas).
   - `videos`: los 2 últimos vídeos del canal oficial [{id, titulo}]. Si no puedes leer YouTube, pon `youtubeChannelId` (UC…) y la web incrusta sola los dos últimos vídeos subidos. Si no tienes ninguno de los dos, omite el campo.
4. Nunca inventes enlaces, IDs ni fechas: todo debe venir de una herramienta o de una fuente consultada.
5. Valida con `python3 scripts/revisar.py` (debe salir sin errores), haz `git pull --rebase`, commit en `main` y push. Pages se actualiza solo en 1-2 minutos.
