# casatoitaliano-sito

Sito delle fonti e dei crediti dei video di Casato Italiano («Le famiglie che possiedono l'Italia»), pubblicato con GitHub Pages. Stile «notte e oro» dal 24/10/2026 (`TEMA=carta` per lo stile precedente).

## Pubblicare un episodio
1. Copia in `dati/video/<slug>.json` il `05_master/pagina_video.json` dell'episodio, con in più `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG), `pubblica` (true quando il video è pubblico) e `serie` («famiglie», default, o «cognomi» per la prima serie). Il titolo è quello di YouTube.
2. Copia la thumbnail in `dati/video/<slug>.jpg`.
3. `python3 build.py`, poi commit e push.

Le pagine generate (`index.html`, `video/`, `404.html`, `sitemap.xml`, `assets/stile.css`) non vanno modificate a mano.
