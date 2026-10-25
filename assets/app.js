(function () {
  "use strict";

  var MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  var DIAS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

  var ICONOS = {
    spotify: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 1.5a10.5 10.5 0 1 0 0 21 10.5 10.5 0 0 0 0-21Zm4.8 15.1a.65.65 0 0 1-.9.22c-2.46-1.5-5.56-1.85-9.2-1.01a.65.65 0 1 1-.3-1.27c3.99-.91 7.42-.52 10.18 1.17.31.19.4.59.22.9Zm1.28-2.85a.82.82 0 0 1-1.12.27c-2.82-1.73-7.12-2.23-10.45-1.22a.82.82 0 1 1-.47-1.57c3.8-1.15 8.54-.6 11.77 1.39.38.24.5.74.27 1.13Zm.11-2.97C14.8 8.77 9.2 8.58 5.96 9.57a.98.98 0 1 1-.57-1.88c3.72-1.13 9.9-.91 13.81 1.41a.98.98 0 0 1-1.01 1.69Z"/></svg>',
    youtube: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12c0 1.6.2 3.2.5 4.8a3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1c.3-1.6.5-3.2.5-4.8s-.2-3.2-.5-4.8ZM9.75 15.02V8.98L15.5 12l-5.75 3.02Z"/></svg>',
    instagram: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.2c3.2 0 3.6 0 4.8.07 3.25.15 4.77 1.69 4.92 4.92.06 1.27.07 1.65.07 4.85s0 3.58-.07 4.85c-.15 3.23-1.66 4.77-4.92 4.92-1.27.06-1.64.07-4.8.07-3.2 0-3.58 0-4.85-.07-3.26-.15-4.77-1.7-4.92-4.92C2.17 15.58 2.16 15.2 2.16 12s0-3.58.07-4.85C2.38 3.92 3.9 2.38 7.15 2.23 8.42 2.17 8.8 2.16 12 2.16Zm0 4.65a5.15 5.15 0 1 0 0 10.3 5.15 5.15 0 0 0 0-10.3Zm0 8.5a3.35 3.35 0 1 1 0-6.7 3.35 3.35 0 0 1 0 6.7Zm5.35-9.9a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4Z"/></svg>',
    tiktok: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16.6 2h-3.4v13.4a2.9 2.9 0 1 1-2.9-2.9c.3 0 .6 0 .9.1V9.1a6.3 6.3 0 1 0 5.4 6.3V8.6a7.9 7.9 0 0 0 4.6 1.5V6.7a4.6 4.6 0 0 1-4.6-4.7Z"/></svg>',
    bandcamp: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M0 18.75 7.44 5.25H24l-7.44 13.5H0Z"/></svg>',
    web: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.9 6h-2.95a15.6 15.6 0 0 0-1.38-3.56A8.03 8.03 0 0 1 18.9 8ZM12 4.04A14.1 14.1 0 0 1 13.91 8h-3.82A14.1 14.1 0 0 1 12 4.04ZM4.26 14a8.2 8.2 0 0 1 0-4h3.38a16.5 16.5 0 0 0 0 4H4.26Zm.84 2h2.95c.32 1.25.78 2.45 1.38 3.56A8 8 0 0 1 5.1 16Zm2.95-8H5.1a8 8 0 0 1 4.33-3.56A15.6 15.6 0 0 0 8.05 8ZM12 19.96A14.1 14.1 0 0 1 10.09 16h3.82A14.1 14.1 0 0 1 12 19.96ZM14.34 14H9.66a14.7 14.7 0 0 1 0-4h4.68a14.7 14.7 0 0 1 0 4Zm.23 5.56c.6-1.11 1.06-2.31 1.38-3.56h2.95a8.03 8.03 0 0 1-4.33 3.56ZM16.36 14a16.5 16.5 0 0 0 0-4h3.38a8.2 8.2 0 0 1 0 4h-3.38Z"/></svg>',
    facebook: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M24 12a12 12 0 1 0-13.9 11.86v-8.4H7.08V12h3.04V9.36c0-3 1.8-4.67 4.54-4.67 1.31 0 2.68.24 2.68.24v2.95h-1.5c-1.5 0-1.96.93-1.96 1.88V12h3.33l-.53 3.47h-2.8v8.39A12 12 0 0 0 24 12Z"/></svg>'
  };
  var NOMBRES_RED = { spotify: "Spotify", youtube: "YouTube", instagram: "Instagram", tiktok: "TikTok", bandcamp: "Bandcamp", web: "Web", facebook: "Facebook" };
  var ORDEN_REDES = ["spotify", "youtube", "instagram", "tiktok", "facebook", "bandcamp", "web"];

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function parseFecha(iso) { var p = iso.split("-").map(Number); return new Date(p[0], p[1] - 1, p[2]); }
  function fechaLarga(iso) { var d = parseFecha(iso); return d.getDate() + " de " + MESES[d.getMonth()] + " de " + d.getFullYear(); }
  function fechaCorta(iso) { var d = parseFecha(iso); return d.getDate() + " " + MESES[d.getMonth()].slice(0, 3); }
  function hoy() { var d = new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }

  function estadoConcierto(iso) {
    var dias = Math.round((parseFecha(iso) - hoy()) / 86400000);
    if (dias < 0) return { cls: "pasado", txt: "Ya tocó" };
    if (dias === 0) return { cls: "proximo", txt: "Hoy" };
    if (dias <= 15) return { cls: "proximo", txt: dias === 1 ? "Mañana" : "En " + dias + " días" };
    return { cls: "lejos", txt: "Más adelante" };
  }

  function renderConciertos(lista) {
    if (!lista || !lista.length) return "";
    var items = lista.slice().sort(function (a, b) { return a.fecha < b.fecha ? -1 : 1; }).map(function (c) {
      var d = parseFecha(c.fecha);
      var est = estadoConcierto(c.fecha);
      var lugar = esc(c.lugar) + (c.ciudad ? " <span>· " + esc(c.ciudad) + "</span>" : "");
      var extra = [c.hora, c.precio].filter(Boolean).map(esc).join(" · ");
      if (extra) lugar += " <span>· " + extra + "</span>";
      if (c.url) lugar = '<a href="' + esc(c.url) + '" target="_blank" rel="noopener">' + lugar + "</a>";
      return '<li><span class="dia">' + DIAS[d.getDay()] + " " + fechaCorta(c.fecha) + '</span><span class="lugar">' + lugar +
        '</span><span class="estado ' + est.cls + '">' + est.txt + "</span></li>";
    });
    return '<ul class="conciertos">' + items.join("") + "</ul>";
  }

  function renderRedes(redes) {
    if (!redes) return "";
    var html = ORDEN_REDES.filter(function (k) { return redes[k]; }).map(function (k) {
      return '<a class="red" href="' + esc(redes[k]) + '" target="_blank" rel="noopener">' + (ICONOS[k] || "") + NOMBRES_RED[k] + "</a>";
    }).join("");
    return html ? '<div class="redes">' + html + "</div>" : "";
  }

  function renderVideos(a) {
    var vids = (a.videos || []).slice(0, 2);
    var html = vids.map(function (v) {
      return '<div class="video"><button type="button" data-yt="' + esc(v.id) + '" aria-label="Reproducir ' + esc(v.titulo || "vídeo") + '">' +
        '<img loading="lazy" src="https://i.ytimg.com/vi/' + esc(v.id) + '/hqdefault.jpg" alt="">' +
        '<span class="play"></span><span class="vt">' + esc(v.titulo || "") + "</span></button></div>";
    }).join("");
    if (!vids.length && a.youtubeChannelId) {
      // Sin IDs concretos: se incrustan los dos últimos vídeos subidos al canal.
      var uploads = "UU" + a.youtubeChannelId.slice(2);
      html = [1, 2].map(function (i) {
        return '<div class="video"><iframe loading="lazy" title="Último vídeo ' + i + ' de ' + esc(a.nombre) + '" src="https://www.youtube-nocookie.com/embed/videoseries?list=' +
          esc(uploads) + "&index=" + i + '" allow="encrypted-media; picture-in-picture" allowfullscreen></iframe></div>';
      }).join("");
    }
    return html ? '<div class="videos">' + html + "</div>" : "";
  }

  function renderArtista(a, completa) {
    var tags = (a.estilo || []).map(function (t) { return '<span class="tag">' + esc(t) + "</span>"; }).join("");
    var cancion = a.cancion ? '<p class="cancion">Para empezar: <strong><a href="' + esc(a.cancion.url) + '" target="_blank" rel="noopener">' + esc(a.cancion.titulo) + "</a></strong></p>" : "";
    var foto = a.foto ? '<img class="foto" loading="lazy" src="' + esc(a.foto) + '" alt="' + esc(a.nombre) + '">' : '<div class="foto" aria-hidden="true"></div>';
    var media = "";
    if (completa) {
      var sp = a.spotifyId ? '<iframe class="spotify-embed" loading="lazy" title="' + esc(a.nombre) + ' en Spotify" src="https://open.spotify.com/embed/artist/' + esc(a.spotifyId) + '?utm_source=generator" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>' : "";
      media = sp || a.videos || a.youtubeChannelId ? '<div class="media">' + sp + renderVideos(a) + "</div>" : "";
    }
    return '<article class="artista">' + foto + "<div>" +
      "<h3>" + esc(a.nombre) + "</h3>" +
      (a.origen ? '<p class="origen">' + esc(a.origen) + "</p>" : "") +
      (tags ? '<div class="tags">' + tags + "</div>" : "") +
      '<p class="porque">' + esc(a.porQue) + "</p>" + cancion +
      renderConciertos(a.conciertos) + renderRedes(a.redes) +
      "</div>" + media + "</article>";
  }

  function renderEntrada(e, idx) {
    var ultima = idx === 0;
    var ventana = e.ventana ? '<span class="ventana">Conciertos entre el ' + fechaLarga(e.ventana.desde) + " y el " + fechaLarga(e.ventana.hasta) + "</span>" : "";
    return '<section class="entrada' + (ultima ? "" : " antigua") + '" id="n' + esc(e.numero) + '">' +
      '<header class="entrada-head"><div class="entrada-meta"><span class="num">Nº ' + esc(e.numero) + "</span><span>" + fechaLarga(e.fecha) + "</span>" +
      (ultima ? '<span class="badge-ultima">Esta semana</span>' : "") + "</div>" +
      "<h2>" + esc(e.titulo) + "</h2>" + (e.intro ? '<p class="intro">' + esc(e.intro) + "</p>" : "") + ventana + "</header>" +
      e.artistas.map(function (a) { return renderArtista(a, ultima || e.completa); }).join("") + "</section>";
  }

  function render(data) {
    if (data.titulo) { document.getElementById("site-title").textContent = data.titulo; document.title = data.titulo; }
    if (data.subtitulo) document.getElementById("site-sub").textContent = data.subtitulo;
    var entradas = (data.entradas || []).slice().sort(function (a, b) { return a.fecha < b.fecha ? 1 : -1; });
    document.getElementById("diario").innerHTML = entradas.map(renderEntrada).join("");
    document.getElementById("toc").innerHTML = entradas.map(function (e, i) {
      return '<a href="#n' + esc(e.numero) + '">Nº ' + esc(e.numero) + " · " + fechaCorta(e.fecha) + (i === 0 ? " (última)" : "") + "</a>";
    }).join("");
    if (location.hash) { var t = document.querySelector(location.hash); if (t) t.scrollIntoView(); }
  }

  document.addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-yt]");
    if (!b) return;
    var id = b.getAttribute("data-yt");
    var f = document.createElement("iframe");
    f.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1";
    f.title = b.getAttribute("aria-label");
    f.allow = "autoplay; encrypted-media; picture-in-picture";
    f.allowFullscreen = true;
    b.parentNode.replaceChild(f, b);
  });

  fetch("data/diario.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(render)
    .catch(function () {
      document.getElementById("diario").innerHTML = '<p class="error">No se ha podido cargar el diario. Recarga la página en un momento.</p>';
    });
})();
