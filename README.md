# casatoitaliano-sito

Sito delle fonti e dei crediti dei video di Casato Italiano («Le famiglie che possiedono l'Italia»), pubblicato con GitHub Pages. Stile «notte e oro» dal 24/10/2026 (`TEMA=carta` per lo stile precedente).

## Pubblicare un episodio
1. Copia in `dati/video/<slug>.json` il `05_master/pagina_video.json` dell'episodio, con in più `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG), `uscita` (data e ora di pubblicazione su YouTube, ISO con fuso, es. `2026-10-28T11:00:00Z`; si mette quando il video è programmato) e `serie` («famiglie», default, o «cognomi» per la prima serie). Il titolo è quello di YouTube.
2. Copia la thumbnail in `dati/video/<slug>.jpg`.
3. `python3 build.py`, poi commit e push.

Le pagine generate (`index.html`, `video/`, `404.html`, `sitemap.xml`, `assets/stile.css`) non vanno modificate a mano.

## Uscite programmate (27/10/2026)
Un episodio entra in home e nella sitemap solo quando il video è uscito: serve `youtube_id` e, se c'è `uscita`, che l'ora sia passata. Prima, la pagina singola esiste ma dice «Il video esce su YouTube il … alle …» invece di portare a un video privato. La GitHub Action `Uscite programmate` rigenera il sito ogni ora (al minuto 7) e pubblica da sola i cambiamenti, quindi l'episodio compare entro un'ora dall'uscita senza toccare niente. `pubblica: false` resta per tenere fuori un episodio a mano.
