# casatoitaliano-sito

Sito delle fonti e dei crediti dei video di Casato Italiano, pubblicato con GitHub Pages.

## Pubblicare un episodio
1. Copia in `dati/video/<slug>.json` il `05_master/pagina_video.json` dell'episodio, con in più `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG) e `pubblica` (true quando il video è pubblico).
2. Copia la thumbnail in `dati/video/<slug>.jpg`.
3. `python3 build.py`, poi commit e push.

Le pagine generate (`index.html`, `video/`, `404.html`, `sitemap.xml`, `assets/stile.css`) non vanno modificate a mano.
