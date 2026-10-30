# casatoitaliano-sito

Sito delle fonti e dei crediti dei video di Casato Italiano («Le famiglie che possiedono l'Italia»), pubblicato con GitHub Pages. Stile «notte e oro» dal 24/10/2026 (`TEMA=carta` per lo stile precedente).

## Pubblicare un episodio
1. Copia in `dati/video/<slug>.json` il `05_master/pagina_video.json` dell'episodio, con in più `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG), `youtube_id` anche se il video è ancora privato, `uscita` (data e ora di pubblicazione su YouTube, ISO con fuso, es. `2026-10-28T12:00:00Z`: il `publishAt` di YouTube) e `serie` («famiglie», default, o «cognomi» per la prima serie). Il titolo è quello di YouTube.
2. Copia la thumbnail in `dati/video/<slug>.jpg`.
3. `python3 build.py`, poi commit e push.

Le pagine generate (`index.html`, `video/`, `404.html`, `sitemap.xml`, `assets/stile.css`) non vanno modificate a mano.

## Uscite programmate (27/10/2026)
Un episodio entra in home e nella sitemap solo quando il video è pubblico su YouTube. Dal 30/10/2026 lo decide YouTube: `build.py` chiede a YouTube (oEmbed, senza chiavi) se ogni video è pubblico, così un'uscita spostata in YouTube Studio non porta in home un video ancora privato. Se YouTube non risponde (per esempio fuori dalla GitHub Action) vale `uscita`: senza data l'episodio aspetta. Prima dell'uscita la pagina singola esiste ma dice «Il video esce su YouTube il … alle …» (o «a breve» se la data è passata e il video è ancora privato). La GitHub Action `Uscite programmate` rigenera il sito una volta al giorno alle 12:17 UTC (13:17 italiane, 14:17 con l'ora legale), dopo le uscite delle 12:00 UTC, e pubblica da sola i cambiamenti. Per anticipare si lancia l'Action a mano. `pubblica: false` resta per tenere fuori un episodio a mano.
