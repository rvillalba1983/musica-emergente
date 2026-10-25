# Radar de salas: cómo se actualiza

Web estática publicada en GitHub Pages: https://rvillalba1983.github.io/musica-emergente/
Todo el contenido está en `data/diario.json`. `index.html` + `assets/app.js` lo pintan (no hay build).

## Entrada semanal (cada viernes)

1. Añade una entrada NUEVA al principio de `entradas` en `data/diario.json`, sin tocar las anteriores.
   - `id` y `fecha`: fecha de publicación (AAAA-MM-DD). `numero`: el siguiente al último.
   - `ventana.desde` = fecha − 7 días, `ventana.hasta` = fecha + 15 días.
   - `titulo`: frase corta que resuma la tanda. `intro`: 2-4 frases (qué hay en Granada/Andalucía, huecos).
2. Criterio de artistas (5 por semana):
   - Emergentes de verdad: primeras giras, EP o primeros discos, circuitos tipo Girando Por Salas o Radar Joven. Nada de veteranos ni artistas que llenan teatros.
   - Con al menos un concierto DENTRO de la ventana. Busca en salas y bares, festivales, ciclos de cantautores, conciertos en pueblos y asociaciones culturales, en España y Latinoamérica.
   - Que encajen con el perfil: canción de autor, rumba, flamenco y flamenquito, mestizaje; letras en castellano preferiblemente.
   - Que no hayan salido en ninguna entrada anterior.
3. Campos por artista (mira las entradas existentes como ejemplo):
   - `nombre`, `origen`, `estilo` (2-3 etiquetas), `porQue` (2-4 frases: quién es y por qué encaja).
   - `foto`: `https://open.spotify.com/oembed?url=https://open.spotify.com/artist/<ID>` devuelve `thumbnail_url`; usa `https://i.scdn.co/image/<hash>` cambiando el prefijo `ab67616100005174` por `ab6761610000e5eb` (640 px).
   - `spotifyId` (se incrusta el reproductor del artista), `cancion` {titulo, url}.
   - `conciertos`: [{fecha, hora, lugar, ciudad, precio, url}]. Incluye también las fechas fuera de la ventana si las hay.
   - `redes`: spotify, youtube, instagram, tiktok, facebook, bandcamp, web (solo las que existan y estén verificadas).
   - `videos`: los 2 últimos vídeos del canal oficial [{id, titulo}]. Si no puedes leer YouTube, pon `youtubeChannelId` (UC…) y la web incrusta sola los dos últimos vídeos subidos. Si no tienes ninguno de los dos, omite el campo.
4. Nunca inventes enlaces, IDs ni fechas: todo debe venir de una herramienta o de una fuente consultada.
5. Valida el JSON (`python3 -c "import json;json.load(open('data/diario.json'))"`), haz commit en `main` y push. Pages se actualiza solo en 1-2 minutos.
