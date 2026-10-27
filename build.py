#!/usr/bin/env python3
"""Genera il sito di Casato Italiano dai dati degli episodi.

  python3 build.py            → index.html + video/<slug>/index.html (+ sitemap.xml)

Dati: dati/video/<slug>.json, cioè il `05_master/pagina_video.json` dell'episodio (skill ytfs-5, pagina_crediti.py),
con in più i campi della pubblicazione: `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG) e la thumbnail in
dati/video/<slug>.jpg. Ogni episodio con la sua pagina entra anche nella home (decisione di Alessandro del 15/10/2026: a ogni
episodio si aggiornano la pagina singola e la home). Solo `pubblica: false` esplicito lo tiene fuori dalla home.
27/10/2026: un episodio entra in home e nella sitemap solo quando il video è uscito: serve `youtube_id` e, se c'è, `uscita`
(data e ora di pubblicazione di YouTube, ISO con fuso, es. 2026-10-28T11:00:00Z) già passata. Prima la pagina singola dice quando esce.
Una GitHub Action rigenera il sito ogni ora, così l'episodio compare da solo dopo l'uscita.
24/10/2026: il canale racconta le famiglie. In home il motto, prima le famiglie e poi la serie dei cognomi (campo `serie`: «famiglie», default, o «cognomi»). Stile: TEMA=notte (default) o carta.
"""
import html, json, os, glob, shutil, datetime, re

QUI = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://casatoitaliano.it'
e = html.escape

CSS_CARTA = """@font-face{font-family:'Cormorant';src:url(fonts/CormorantGaramond[wght].ttf);font-weight:300 700;font-display:swap}
@font-face{font-family:'Cormorant';src:url(fonts/CormorantGaramond-Italic[wght].ttf);font-style:italic;font-weight:300 700;font-display:swap}
@font-face{font-family:'Inter';src:url(fonts/Inter[opsz,wght].ttf);font-weight:100 900;font-display:swap}
:root{--carta:#ECE2CC;--terra:#D9CAA8;--ink:#2A2018;--grigio:#6B5C49;--rosso:#8C1C13}
*{box-sizing:border-box}
body{margin:0;background:var(--carta);color:var(--ink);font:20px/1.6 'Cormorant',Georgia,serif}
header{border-bottom:1px solid var(--terra);padding:12px 20px;display:flex;align-items:center;gap:12px}
header img{width:44px;height:44px}header a{color:var(--ink);text-decoration:none;font-size:24px;font-weight:600;letter-spacing:.06em}
main{max-width:760px;margin:0 auto;padding:28px 20px 60px}
.reg{font:600 13px 'Inter',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--rosso)}
h1{font-size:40px;line-height:1.15;margin:.2em 0 .5em;font-weight:600}
.thumb{width:100%;border:1px solid var(--terra);display:block}
.yt{display:inline-block;margin:14px 0 6px;color:var(--rosso);font:600 16px 'Inter',sans-serif}
h2{font-size:27px;font-weight:600;border-bottom:1px solid var(--ink);padding-bottom:4px;margin-top:2em}
ol,ul{padding-left:1.2em;overflow-wrap:anywhere}li{margin:.5em 0}a{color:var(--rosso)}
.cr{display:block;overflow-wrap:anywhere;padding:10px 0;border-bottom:1px dashed var(--terra);font-size:19px}
.cr .m{font:500 14px 'Inter',sans-serif;color:var(--grigio);padding-top:4px}.cr .l{font:14px 'Inter',sans-serif;color:var(--grigio)}
.nota{background:#f4ecda;border-left:3px solid var(--rosso);padding:12px 16px;font-style:italic}
.ep{display:grid;grid-template-columns:240px 1fr;gap:18px;padding:18px 0;border-bottom:1px solid var(--terra);text-decoration:none;color:var(--ink)}
.ep img{width:100%;border:1px solid var(--terra)}.ep h3{margin:.1em 0;font-size:25px;line-height:1.2;font-weight:600}
.intro{font-size:22px;font-style:italic}
footer{text-align:center;color:var(--grigio);font:14px 'Inter',sans-serif;padding:30px}
@media (max-width:600px){body{font-size:21px}h1{font-size:33px}.ep{grid-template-columns:1fr}.cr{font-size:20px}.cr .l,.cr .m{font-size:15px}}
.motto{font-size:30px;font-weight:600;line-height:1.2;margin:.2em 0 .3em}.serie{font:600 14px 'Inter',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--grigio);margin:2.4em 0 .2em;border-bottom:1px solid var(--terra);padding-bottom:6px}"""

CSS_NOTTE = """@font-face{font-family:'Anton';src:url(fonts/Anton-Regular.ttf);font-display:swap}
@font-face{font-family:'Inter';src:url(fonts/Inter[opsz,wght].ttf);font-weight:100 900;font-display:swap}
:root{--fondo:#0B1222;--fondo2:#141d33;--linea:#28324d;--testo:#F1ECE0;--grigio:#9AA3BC;--oro:#F7BE16}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at top,#16203a 0,var(--fondo) 55%) fixed,var(--fondo);color:var(--testo);font:18px/1.65 'Inter',system-ui,sans-serif}
header{border-bottom:1px solid var(--linea);padding:12px 20px;display:flex;align-items:center;gap:12px}
header img{width:44px;height:44px;border-radius:50%}header a{color:#fff;text-decoration:none;font:26px 'Anton',Impact,sans-serif;letter-spacing:.04em}
main{max-width:820px;margin:0 auto;padding:28px 20px 60px}
.reg{font:700 12px 'Inter',sans-serif;letter-spacing:.18em;text-transform:uppercase;color:var(--oro)}
h1{font:40px/1.12 'Anton',Impact,sans-serif;color:#fff;margin:.2em 0 .5em;letter-spacing:.01em}
.thumb{width:100%;border-radius:8px;display:block}
.yt{display:inline-block;margin:14px 0 6px;color:var(--oro);font:700 16px 'Inter',sans-serif}
h2{font:26px 'Anton',Impact,sans-serif;color:#fff;border-bottom:1px solid var(--linea);padding-bottom:6px;margin-top:2em;letter-spacing:.02em}
ol,ul{padding-left:1.2em;overflow-wrap:anywhere}li{margin:.5em 0}a{color:var(--oro)}
.cr{display:block;overflow-wrap:anywhere;padding:10px 0;border-bottom:1px dashed var(--linea);font-size:17px}
.cr .m,.cr .l{font:14px 'Inter',sans-serif;color:var(--grigio)}
.nota{background:var(--fondo2);border-left:3px solid var(--oro);padding:12px 16px}
.ep{display:grid;grid-template-columns:260px 1fr;gap:18px;padding:18px 0;border-bottom:1px solid var(--linea);text-decoration:none;color:var(--testo)}
.ep img{width:100%;border-radius:6px}.ep h3{margin:.15em 0;font:24px/1.15 'Anton',Impact,sans-serif;color:#fff;letter-spacing:.01em}
.motto{font:46px/1.05 'Anton',Impact,sans-serif;color:#fff;margin:.1em 0 .25em;text-transform:uppercase}
.intro{font-size:19px;color:var(--testo)}
.serie{font:700 13px 'Inter',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:var(--oro);margin:2.4em 0 .2em;border-bottom:1px solid var(--linea);padding-bottom:6px}
footer{text-align:center;color:var(--grigio);font:14px 'Inter',sans-serif;padding:30px}
@media (max-width:600px){body{font-size:18px}h1{font-size:32px}.motto{font-size:36px}.ep{grid-template-columns:1fr}}"""
TEMA = os.environ.get('TEMA', 'notte')   # 24/10/2026: stile del sito (notte = come banner e grafiche; carta = stile dei cognomi)
CSS = CSS_NOTTE if TEMA == 'notte' else CSS_CARTA
MOTTO = "Le famiglie che possiedono l'Italia"


import hashlib
VERSIONE_CSS = hashlib.md5(CSS.encode()).hexdigest()[:8]   # il link al CSS cambia quando cambia lo stile: niente copie vecchie in cache


def scheletro(titolo, corpo, descr='', canon='', r=''):   # r = prefisso relativo verso la radice: funziona con e senza dominio
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titolo)}</title><meta name="description" content="{e(descr)}">{f'<link rel="canonical" href="{e(canon)}">' if canon else ''}
<link rel="icon" href="{r}assets/favicon.png"><link rel="stylesheet" href="{r}assets/stile.css?v={VERSIONE_CSS}"></head><body>
<header><img src="{r}assets/logo.png" alt=""><a href="{r or './'}">CASATO ITALIANO</a></header><main>{corpo}</main>
<footer>Casato Italiano · {MOTTO} · <a href="https://www.youtube.com/channel/UCxcCEZ9jiKbM7oYoAsfrAKg">YouTube</a></footer></body></html>"""


ADESSO = datetime.datetime.now(datetime.timezone.utc)
MESI = 'gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre'.split()


def uscita(v):
    """data e ora di uscita del video (datetime UTC) o None"""
    u = v.get('uscita')
    if not u: return None
    d = datetime.datetime.fromisoformat(u.replace('Z', '+00:00'))
    return d if d.tzinfo else d.replace(tzinfo=datetime.timezone.utc)


def uscito(v):
    u = uscita(v)
    return bool(v.get('youtube_id')) and (u is None or u <= ADESSO)


def quando(v):
    u = uscita(v)
    if not u: return 'presto'
    try:
        from zoneinfo import ZoneInfo
        u = u.astimezone(ZoneInfo('Europe/Rome'))
    except Exception:
        pass
    return f"il {u.day} {MESI[u.month - 1]} alle {u.hour}:{u.minute:02d}"


def nome_file(t):
    return e(t.replace('File:', '').replace('_', ' ').rsplit('.', 1)[0]) if t.startswith('File:') else e(t)


def pagina(v):
    m = v.get('materiali') or {}; g = m.get('generati') or {}
    yt = f'https://www.youtube.com/watch?v={e(v["youtube_id"])}' if v.get('youtube_id') else 'https://www.youtube.com/channel/UCxcCEZ9jiKbM7oYoAsfrAKg'
    ric = ''.join(f"<li><a href=\"{e(f['url'])}\">{e(f['titolo'])}</a></li>" for f in v.get('fonti_ricerca', []))
    # solo le attribuzioni obbligatorie (licenze CC BY / CC BY-SA), senza minutaggi (decisione di Alessandro, 15/10/2026)
    cr = ''.join(f"<div class=cr><span><a href=\"{e(r.get('link', ''))}\">{nome_file(r.get('titolo', ''))}</a><br>"
                 f"<span class=l>{' · '.join(e(x) for x in (r.get('autore'), r.get('licenza')) if x)}</span></span></div>"
                 for r in m.get('reali', []) if re.search(r'\bCC[ -]BY\b', r.get('licenza') or '', re.I))
    corpo = f"<div class=reg>{e(v.get('regione', ''))}</div><h1>{e(v['titolo'])}</h1>"
    fuori = uscito(v)
    if os.path.exists(os.path.join(QUI, 'video', v['slug'], 'thumb.jpg')):
        img = f"<img class=thumb src=\"thumb.jpg\" alt=\"{e(v['titolo'])}\">"
        corpo += f"<a href=\"{yt}\">{img}</a>" if fuori else img
    corpo += (f"<a class=yt href=\"{yt}\">Guarda il video su YouTube</a>" if fuori
              else f"<p class=yt>Il video esce su YouTube {e(quando(v))}.</p>")
    if ric: corpo += f"<h2>Fonti della ricerca</h2><ol>{ric}</ol>"
    if cr: corpo += f"<h2>Attribuzioni di immagini e video</h2>{cr}"
    if g.get('immagini') or g.get('clip'):
        q = ' e '.join(x for x in (f"{g['immagini']} immagini" if g.get('immagini') else '', f"{g['clip']} clip" if g.get('clip') else '') if x)
        corpo += f"<h2>Scene ricostruite</h2><p class=nota>Alcune scene sono ricostruite con l'intelligenza artificiale ({q}). Non sono documenti né fotografie d'epoca.</p>"
    if m.get('dati_mappe'):
        dm = [d for d in m['dati_mappe'] if re.search(r'\bCC[ -]BY\b', d.get('licenza') or '', re.I)]
        if dm: corpo += "<h2>Mappe</h2><ul>" + ''.join(f"<li>{e(d['titolo'])} · {e(d['licenza'])} · <a href=\"{e(d['link'])}\">fonte</a></li>" for d in dm) + "</ul>"
    return scheletro(f"{v['titolo']} · Casato Italiano", corpo, f"Fonti e crediti del video «{v['titolo']}»", f"{BASE}/video/{v['slug']}/", '../../')


def main():
    os.makedirs(os.path.join(QUI, 'assets'), exist_ok=True)
    open(os.path.join(QUI, 'assets/stile.css'), 'w').write(CSS)
    vids = []
    for f in sorted(glob.glob(os.path.join(QUI, 'dati/video/*.json'))):
        v = json.load(open(f, encoding='utf-8')); d = os.path.join(QUI, 'video', v['slug']); os.makedirs(d, exist_ok=True)
        t = f[:-5] + '.jpg'
        if os.path.exists(t): shutil.copy(t, os.path.join(d, 'thumb.jpg'))
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(pagina(v)); vids.append(v)
    pub = sorted([v for v in vids if v.get('pubblica', True) is not False and uscito(v)], key=lambda v: v.get('data', ''), reverse=True)
    voce = lambda v: f"<a class=ep href=\"video/{e(v['slug'])}/\"><img src=\"video/{e(v['slug'])}/thumb.jpg\" alt=\"\"><div><div class=reg>{e(v.get('regione', ''))}</div><h3>{e(v['titolo'])}</h3></div></a>"
    fam = [v for v in pub if v.get('serie', 'famiglie') != 'cognomi']; cog = [v for v in pub if v.get('serie') == 'cognomi']
    # 24/10/2026: il canale racconta le famiglie; i video sui cognomi restano in una sezione a parte, sotto
    corpo = (f"<div class=motto>{e(MOTTO)}</div>"
             "<p class=intro>Chi sono le famiglie più ricche d'Italia, regione per regione e tema per tema: da dove vengono, come hanno fatto i soldi "
             "e quali dei loro marchi usi già ogni giorno. Per ogni video del canale, qui trovi le fonti della ricerca e i crediti di immagini, video e mappe.</p>"
             + (f"<div class=serie>Le famiglie</div>{''.join(voce(v) for v in fam)}" if fam else "<p>Il primo episodio arriva presto.</p>")
             + (f"<div class=serie>La prima serie: i cognomi</div>{''.join(voce(v) for v in cog)}" if cog else ''))
    open(os.path.join(QUI, 'index.html'), 'w', encoding='utf-8').write(scheletro(f'Casato Italiano · {MOTTO}', corpo, f"Casato Italiano, il canale YouTube sulle famiglie più ricche d'Italia: fonti e crediti di ogni video", BASE + '/'))
    open(os.path.join(QUI, '404.html'), 'w', encoding='utf-8').write(scheletro('Pagina non trovata · Casato Italiano',
        "<h1>Pagina non trovata</h1><p>Questa pagina non esiste. <a href=\"/\">Torna all'elenco dei video</a>.</p>", r='/'))
    oggi = datetime.date.today().isoformat()
    sm = ''.join(f"<url><loc>{BASE}/video/{v['slug']}/</loc><lastmod>{v.get('data', oggi)}</lastmod></url>" for v in pub)
    open(os.path.join(QUI, 'sitemap.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{BASE}/</loc></url>{sm}</urlset>')
    attesa = [f"{v['slug'][:40]} ({quando(v)})" for v in vids if not uscito(v)]
    print(f'sito: {len(vids)} pagine video, {len(pub)} in home' + (f"; in attesa dell'uscita: {', '.join(attesa)}" if attesa else ''))


if __name__ == '__main__':
    main()
