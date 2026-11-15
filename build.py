#!/usr/bin/env python3
"""Genera il sito di Casato Italiano dai dati degli episodi.

  python3 build.py            → index.html + video/<slug>/index.html (+ sitemap.xml)

Dati: dati/video/<slug>.json, cioè il `05_master/pagina_video.json` dell'episodio (skill ytfs-5, pagina_crediti.py),
con in più i campi della pubblicazione: `numero`, `regione`, `youtube_id`, `data` (AAAA-MM-GG) e la thumbnail in
dati/video/<slug>.jpg. Ogni episodio con la sua pagina entra anche nella home (decisione di Alessandro del 15/10/2026: a ogni
episodio si aggiornano la pagina singola e la home). Solo `pubblica: false` esplicito lo tiene fuori dalla home.
27/10/2026: un episodio entra in home e nella sitemap solo quando il video è uscito: serve `youtube_id` e `uscita`
(data e ora di pubblicazione di YouTube, ISO con fuso, es. 2026-10-28T11:00:00Z) già passata. Prima la pagina singola dice quando esce.
Una GitHub Action rigenera il sito ogni giorno dopo l'uscita delle 13 (12:17 UTC), così l'episodio compare da solo.
30/10/2026: se YouTube risponde, decide YouTube (video pubblico o no, via oEmbed); la data `uscita` vale solo quando YouTube
non è raggiungibile e per scrivere sulla pagina quando esce. CASATO_YT=0 per non chiedere a YouTube.
15/11/2026 (Alessandro: «rendere più solido lo strumento che aggiorna la home»): il sito RICORDA ciò che YouTube ha risposto.
  - La prima volta che YouTube dice «pubblico» si scrive nei dati `pubblico_dal` (data e ora). Da lì l'episodio è in home anche quando YouTube non risponde
    (fuori dalla GitHub Action, o se YouTube blocca la macchina): il risultato è lo stesso da ovunque si lanci, e le date a mano non servono più. Ordine in home: `pubblico_dal`.
  - A ogni giro si legge da YouTube anche il titolo e la copertina: se cambiano in Studio, il sito li segue.
  - Un video che ERA pubblico e ora YouTube dice chiaramente non pubblico (privato o tolto), mentre gli altri rispondono: è ritirato. Esce dalla home e dalla sitemap
    e la sua pagina viene cancellata (404). I dati restano: se torna pubblico, torna tutto. Si scrive `ritirato_dal`.
  - Più di RITIRATI_MAX (3) ritirati nello stesso giro = YouTube sta bloccando la macchina: non si tocca niente e il giro finisce in errore (codice 2: non pubblicare).
    Se sono voluti: CASATO_CONFERMA_RITIRATI=1.
  - Un episodio con una fonte non pubblicabile non ferma più il sito: resta com'era (o fuori, se non c'era) e il giro finisce in errore (codice 1) dopo aver aggiornato gli altri.
  - Rete di sicurezza: se la home nuova ha meno episodi di prima senza che siano ritirati o spenti a mano, codice 2.
24/10/2026: il canale racconta le famiglie. In home il motto, prima le famiglie e poi la serie dei cognomi (campo `serie`: «famiglie», default, o «cognomi»). Stile: TEMA=notte (default) o carta.
"""
import html, json, os, glob, shutil, datetime, re, sys

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
ol,ul{padding-left:1.2em;overflow-wrap:anywhere}li{margin:.5em 0}a{color:var(--rosso)}h3.fg{font-size:20px;font-weight:600;margin:1.6em 0 .2em}
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
ol,ul{padding-left:1.2em;overflow-wrap:anywhere}li{margin:.5em 0}a{color:var(--oro)}h3.fg{font:21px/1.2 'Anton',Impact,sans-serif;color:#fff;letter-spacing:.02em;margin:1.6em 0 .2em}
.cr{display:block;overflow-wrap:anywhere;padding:10px 0;border-bottom:1px dashed var(--linea);font-size:17px}
.cr .m,.cr .l{font:14px 'Inter',sans-serif;color:var(--grigio)}
.nota{background:var(--fondo2);border-left:3px solid var(--oro);padding:12px 16px}
.racconta{font-size:20px;color:var(--testo);margin:1.2em 0 0}
.indice{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0;padding:0;list-style:none}.indice li{margin:0}
.indice a{display:block;font:600 14px 'Inter',sans-serif;color:var(--testo);text-decoration:none;border:1px solid var(--linea);border-radius:999px;padding:6px 12px}
.indice a:hover{border-color:var(--oro);color:var(--oro)}
.cap{margin:2.2em 0 0;padding-top:.2em}.cap h3{font:24px/1.15 'Anton',Impact,sans-serif;color:#fff;letter-spacing:.02em;margin:0 0 .5em;display:flex;gap:12px;align-items:baseline}
.cap h3 .min{font:600 14px 'Inter',sans-serif;color:var(--oro);letter-spacing:.06em;white-space:nowrap}
.fonte{padding:10px 0;border-bottom:1px dashed var(--linea);overflow-wrap:anywhere}
.fonte .t{font:700 12px 'Inter',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--grigio)}
.fonte .a{display:block;font-size:18px;line-height:1.3;margin:.15em 0 0}
.ep{display:grid;grid-template-columns:260px 1fr;gap:18px;padding:18px 0;border-bottom:1px solid var(--linea);text-decoration:none;color:var(--testo)}
.ep img{width:100%;border-radius:6px}.ep h3{margin:.15em 0;font:24px/1.15 'Anton',Impact,sans-serif;color:#fff;letter-spacing:.01em}
.motto{font:46px/1.05 'Anton',Impact,sans-serif;color:#fff;margin:.1em 0 .25em;text-transform:uppercase}
.intro{font-size:19px;color:var(--testo)}
.serie{font:700 13px 'Inter',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:var(--oro);margin:2.4em 0 .2em;border-bottom:1px solid var(--linea);padding-bottom:6px}
footer{text-align:center;color:var(--grigio);font:14px 'Inter',sans-serif;padding:30px}
@media (max-width:600px){body{font-size:18px}h1{font-size:32px}.motto{font-size:36px}.ep{grid-template-columns:1fr}}"""
TEMA = os.environ.get('TEMA', 'notte')   # 24/10/2026: stile del sito (notte = come banner e grafiche; carta = stile dei cognomi)
CSS = CSS_NOTTE if TEMA == 'notte' else CSS_CARTA
MOTTO = "Orgoglio italiano, luogo per luogo"


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


def pubblico_su_youtube(yid):
    """Chiede a YouTube (oEmbed, nessuna chiave): True pubblico, False chiaramente non pubblico (privato, programmato, tolto), None se YouTube non risponde
    o risponde altro (rete, blocco, errore del server). 15/11/2026: da solo NON decide più niente: lo legge `stato()` insieme a ciò che il sito ricorda."""
    if yid in _STATO_YT: return _STATO_YT[yid]
    finto = os.environ.get('CASATO_YT_FINTO')          # solo per le prove: {"<id>": true | false | null | {"title": "…"}}
    if finto:
        x = json.load(open(finto, encoding='utf-8')).get(yid, None)
        r = True if isinstance(x, dict) else x
        if isinstance(x, dict): _TITOLO_YT[yid] = x.get('title')
        _STATO_YT[yid] = r; return r
    import urllib.request, urllib.error
    u = f'https://www.youtube.com/oembed?format=json&url=https://www.youtube.com/watch?v={yid}'
    try:
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'casatoitaliano-build'}), timeout=15).read()); r = True
        _TITOLO_YT[yid] = (j.get('title') or '').strip() or None
    except urllib.error.HTTPError as x:
        r = False if x.code in (400, 401, 403, 404) else None
    except Exception:
        r = None
    _STATO_YT[yid] = r
    return r


_STATO_YT = {}
_TITOLO_YT = {}
RITIRATI_MAX = 3      # più di così nello stesso giro = YouTube sta bloccando, non è una scelta di Alessandro
_BLOCCO = [False]


def chiedi(v):
    if not v.get('youtube_id') or os.environ.get('CASATO_YT', '1') == '0': return None
    return pubblico_su_youtube(v['youtube_id'])


def ritirato(v):
    """era pubblico (il sito lo ricorda) e YouTube ora dice chiaramente di no, senza che sia un blocco."""
    if not v.get('pubblico_dal'): return False
    s = chiedi(v)
    if s is True: return False
    if v.get('ritirato_dal'): return True      # già ritirato: resta ritirato finché YouTube non lo ridà pubblico (anche se tace o blocca)
    return s is False and not _BLOCCO[0]


def uscito(v):
    if not v.get('youtube_id'): return False
    s = chiedi(v)
    if s is True: return True
    if v.get('pubblico_dal'): return not ritirato(v)      # il sito ricorda: resta in home se YouTube tace o se è un blocco
    if s is False: return False                              # mai stato pubblico e YouTube dice di no: aspetta
    u = uscita(v)                                            # YouTube non risponde e il sito non ricorda niente: vale la data scritta nei dati
    return u is not None and u <= ADESSO


def quando(v):
    u = uscita(v)
    if not u or u <= ADESSO: return 'a breve'   # data passata ma video ancora privato: uscita spostata
    try:
        from zoneinfo import ZoneInfo
        u = u.astimezone(ZoneInfo('Europe/Rome'))
    except Exception:
        pass
    return f"il {u.day} {MESI[u.month - 1]} alle {u.hour}:{u.minute:02d}"


def salva(f, v):
    """Riscrive i dati di un episodio nella stessa forma in cui erano (rientro di 1 o 2 spazi, a capo finale): così nella storia del sito si vede solo ciò che cambia."""
    vecchio = open(f, encoding='utf-8').read() if os.path.exists(f) else ''
    m = re.search(r'^\{\n( +)"', vecchio)
    open(f, 'w', encoding='utf-8').write(json.dumps(v, ensure_ascii=False, indent=len(m.group(1)) if m else 1) + ('\n' if vecchio.endswith('\n') else ''))


def copertina(yid, dest):
    """Scarica la copertina del video da YouTube e la mette al posto di quella nei dati, se è cambiata. True se l'ha cambiata. Se YouTube non la dà resta quella che c'è."""
    if os.environ.get('CASATO_YT_FINTO') or os.environ.get('CASATO_COPERTINE', '1') == '0': return False
    import urllib.request
    for nome in ('maxresdefault', 'sddefault'):
        try:
            b = urllib.request.urlopen(urllib.request.Request(f'https://i.ytimg.com/vi/{yid}/{nome}.jpg', headers={'User-Agent': 'casatoitaliano-build'}), timeout=20).read()
        except Exception:
            continue
        if len(b) < 5000: continue
        if os.path.exists(dest) and open(dest, 'rb').read() == b: return False
        open(dest, 'wb').write(b); return True
    return False


def nome_file(t):
    return e(t.replace('File:', '').replace('_', ' ').rsplit('.', 1)[0]) if t.startswith('File:') else e(t)


def pagina(v):
    m = v.get('materiali') or {}; g = m.get('generati') or {}
    yt = f'https://www.youtube.com/watch?v={e(v["youtube_id"])}' if v.get('youtube_id') else 'https://www.youtube.com/channel/UCxcCEZ9jiKbM7oYoAsfrAKg'
    # 05/11/2026 (EP31): fonti raggruppate per voce del video (campo `gruppo`); una fonte senza url (Registro delle Imprese:
    # i suoi link portano a pagine d'errore) si scrive come testo, senza link.
    li = lambda f: (f"<li><a href=\"{e(f['url'].replace(' ', '%20'))}\">{e(f['titolo'])}</a></li>" if f.get('url') else f"<li>{e(f['titolo'])}</li>")
    ric, gp = '', None
    for f in v.get('fonti_ricerca', []):
        if f.get('gruppo') and f['gruppo'] != gp:
            ric += ('</ul>' if gp else '') + f"<h3 class=fg>{e(f['gruppo'])}</h3><ul>"; gp = f['gruppo']
        ric += li(f)
    if gp: ric += '</ul>'
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
    if v.get('standard') == 2:   # 06/11/2026: standard unico della pagina (bibbia del canale §12): testata, fonti per capitolo con cosa sostengono, fonti generali, materiali
        ric = ''
        def fonte(f):
            testo = f.get('titolo') or 'Apri l\'articolo'   # fonti senza titolo degli episodi vecchi (bibbia §12, v1.4): testata e link
            tit = f"<a class=a href=\"{e(f['url'].replace(' ', '%20'))}\">{e(testo)}</a>" if f.get('url') else f"<span class=a>{e(f['titolo'])}</span>"
            return f"<div class=fonte><div class=t>{e(' · '.join(x for x in (f.get('testata'), f.get('data')) if x))}</div>{tit}</div>"
        caps = v.get('capitoli') or []
        if v.get('racconta'): corpo += f"<p class=racconta>{e(v['racconta'])}</p>"
        corpo += ("<h2>Le fonti, capitolo per capitolo</h2><p class=nota>Solo le fonti che sostengono qualcosa detto nel video, capitolo per capitolo, nell'ordine in cui il video le usa.</p>" if caps
                  else "<h2>Le fonti</h2><p class=nota>Le fonti su cui si basa il video.</p>")
        for i, c in enumerate(caps):
            corpo += f"<section class=cap id=c{i}><h3>{e(c['titolo'])}</h3>" + ''.join(fonte(f) for f in c['fonti']) + "</section>"
        if v.get('elenco'):   # seconda forma (bibbia §12, v1.3): elenco unico pulito, quando l'episodio non lega le frasi ai capitoli
            corpo += ''.join(fonte(f) for f in v['elenco'])
        if v.get('fonti_generali'): corpo += "<h2>Fonti generali</h2>" + ''.join(fonte(f) for f in v['fonti_generali'])
        if cr or g.get('immagini') or g.get('clip') or m.get('dati_mappe'): corpo += "<h2>Materiali</h2>"
        if cr: corpo += f"<h3 class=fg>Attribuzioni di immagini e video</h3>{cr}"
        if g.get('immagini') or g.get('clip'):
            q = ' e '.join(x for x in (f"{g['immagini']} immagini" if g.get('immagini') else '', f"{g['clip']} clip" if g.get('clip') else '') if x)
            corpo += f"<h3 class=fg>Scene ricostruite</h3><p class=nota>Alcune scene sono ricostruite con l'intelligenza artificiale. Non sono documenti né fotografie d'epoca.</p>"
        dm = [d for d in (m.get('dati_mappe') or []) if re.search(r'\bCC[ -]BY\b', d.get('licenza') or '', re.I)]
        if dm: corpo += "<h3 class=fg>Mappe</h3><ul>" + ''.join(f"<li>{e(d['titolo'])} · {e(d['licenza'])} · <a href=\"{e(d['link'])}\">fonte</a></li>" for d in dm) + "</ul>"
        return scheletro(f"{v['titolo']} · Casato Italiano", corpo, f"Fonti e crediti del video «{v['titolo']}»", f"{BASE}/video/{v['slug']}/", '../../')
    if ric: corpo += f"<h2>Fonti della ricerca</h2><p class=nota>Divise per voce del video, nell'ordine in cui compaiono. Le fonti del Registro delle Imprese sono indicate senza link: le sue pagine non si aprono senza accesso.</p>{ric}" if gp else f"<h2>Fonti della ricerca</h2><ol>{ric}</ol>"
    if cr: corpo += f"<h2>Attribuzioni di immagini e video</h2>{cr}"
    if g.get('immagini') or g.get('clip'):
        q = ' e '.join(x for x in (f"{g['immagini']} immagini" if g.get('immagini') else '', f"{g['clip']} clip" if g.get('clip') else '') if x)
        corpo += f"<h2>Scene ricostruite</h2><p class=nota>Alcune scene sono ricostruite con l'intelligenza artificiale. Non sono documenti né fotografie d'epoca.</p>"
    if m.get('dati_mappe'):
        dm = [d for d in m['dati_mappe'] if re.search(r'\bCC[ -]BY\b', d.get('licenza') or '', re.I)]
        if dm: corpo += "<h2>Mappe</h2><ul>" + ''.join(f"<li>{e(d['titolo'])} · {e(d['licenza'])} · <a href=\"{e(d['link'])}\">fonte</a></li>" for d in dm) + "</ul>"
    return scheletro(f"{v['titolo']} · Casato Italiano", corpo, f"Fonti e crediti del video «{v['titolo']}»", f"{BASE}/video/{v['slug']}/", '../../')


# 29/10/2026: appunti di lavoro finiti come titoli delle fonti (EP Toscana, EP Friuli). Il sito non si genera se capita di nuovo.
SPIA = re.compile(r'verifica da zero|verificat|\.json|\.py\b|bibbia|soglia_|interno:|\bTODO\b|da verificare|01_script|02_|fase \d', re.I)
SPAZZ = re.compile(r'too many requests|attention required|cloudflare|just a moment|security checkpoint|access denied|bot check|wartungsmodus|pagina non trovata|page not found', re.I)
def controlla_fonti(v):
    err = []
    for f in v.get('fonti_ricerca', []) + [r for c in v.get('capitoli') or [] for r in c['fonti']] + (v.get('fonti_generali') or []) + (v.get('elenco') or []):
        t, u = f.get('titolo', ''), f.get('url', '')
        if v.get('standard') == 2 and not t.strip() and u.startswith('http'): continue   # bibbia §12 v1.4: fonte senza titolo degli episodi vecchi, pubblicata con testata e link
        if (SPIA.search(t) or t.startswith('http') or re.fullmatch(r'[a-z0-9]+(_[a-z0-9]+)+', t) or not t.strip()
                or (u and not u.startswith('http')) or ' ; ' in u or 'registroimprese' in u
                or re.match(r'^(.{3,}?),\s*\1$', t.strip(), re.I) or SPAZZ.search(t)):
            err.append(f"{v['slug']}: «{t}» → {u}")
    return err

def main():
    os.makedirs(os.path.join(QUI, 'assets'), exist_ok=True)
    open(os.path.join(QUI, 'assets/stile.css'), 'w').write(CSS)
    vids = []; errori = []; avvisi = []
    prima = set(re.findall(r'class=ep href="video/([^/"]+)/"', open(os.path.join(QUI, 'index.html'), encoding='utf-8').read())) if os.path.exists(os.path.join(QUI, 'index.html')) else set()
    dati = [(f, json.load(open(f, encoding='utf-8'))) for f in sorted(glob.glob(os.path.join(QUI, 'dati/video/*.json')))]
    # 1 · blocco? più di RITIRATI_MAX video che il sito ricorda pubblici e che YouTube ora nega, nello stesso giro
    negati = [v for _, v in dati if v.get('pubblico_dal') and not v.get('ritirato_dal') and chiedi(v) is False]
    if len(negati) > RITIRATI_MAX and os.environ.get('CASATO_CONFERMA_RITIRATI') != '1':
        _BLOCCO[0] = True
        errori.append(f"BLOCCO: YouTube dice non pubblici {len(negati)} video che erano pubblici ({', '.join(v['slug'][:28] for v in negati[:6])}…): più di {RITIRATI_MAX} insieme, non si tocca niente. Se è voluto: rilanciare con CASATO_CONFERMA_RITIRATI=1")
    ritirati_ora = []; fuori_voluti = set()
    for f, v in dati:
        cambiato = False; d = os.path.join(QUI, 'video', v['slug']); t = f[:-5] + '.jpg'
        s = chiedi(v)
        if s is True:
            if not v.get('pubblico_dal'):      # prima volta: per gli episodi già fuori vale l'uscita scritta nei dati, se è passata
                u = uscita(v); v['pubblico_dal'] = (u if (u and u <= ADESSO) else ADESSO).strftime('%Y-%m-%dT%H:%M:%SZ'); cambiato = True
            if v.pop('ritirato_dal', None): cambiato = True
            tit = _TITOLO_YT.get(v['youtube_id'])
            if tit and tit != v.get('titolo'): avvisi.append(f"titolo aggiornato da YouTube: {v['slug'][:40]}"); v['titolo'] = tit; cambiato = True
            if copertina(v['youtube_id'], t): avvisi.append(f"copertina aggiornata da YouTube: {v['slug'][:40]}")
        elif ritirato(v):
            if not v.get('ritirato_dal'): v['ritirato_dal'] = ADESSO.strftime('%Y-%m-%dT%H:%M:%SZ'); cambiato = True; ritirati_ora.append(v['slug'])
            if os.path.isdir(d): shutil.rmtree(d)      # la pagina di un video ritirato non deve essere raggiungibile
            fuori_voluti.add(v['slug'])
            if v['slug'] in ritirati_ora: avvisi.append(f"ritirato (non più pubblico su YouTube): {v['slug'][:40]}")
            if cambiato: salva(f, v)
            continue
        if cambiato: salva(f, v)
        if v.get('pubblica', True) is False: fuori_voluti.add(v['slug'])
        ef = controlla_fonti(v)
        if ef:      # un episodio sbagliato non ferma gli altri: resta la pagina che c'era
            errori += ['FONTE NON PUBBLICABILE: ' + x for x in ef]
            if os.path.exists(os.path.join(d, 'index.html')): vids.append(v)
            continue
        os.makedirs(d, exist_ok=True)
        if os.path.exists(t): shutil.copy(t, os.path.join(d, 'thumb.jpg'))
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(pagina(v)); vids.append(v)
    ordine = lambda v: v.get('pubblico_dal') or v.get('uscita') or v.get('data', '')
    pub = sorted([v for v in vids if v.get('pubblica', True) is not False and uscito(v)], key=ordine, reverse=True)
    voce = lambda v: f"<a class=ep href=\"video/{e(v['slug'])}/\"><img src=\"video/{e(v['slug'])}/thumb.jpg\" alt=\"\"><div><div class=reg>{e(v.get('regione', ''))}</div><h3>{e(v['titolo'])}</h3></div></a>"
    fam = [v for v in pub if v.get('serie', 'famiglie') != 'cognomi']; cog = [v for v in pub if v.get('serie') == 'cognomi']
    # 24/10/2026: il canale racconta le famiglie; i video sui cognomi restano in una sezione a parte, sotto
    corpo = (f"<div class=motto>{e(MOTTO)}</div>"
             "<p class=intro>Le famiglie, gli imprenditori e le aziende che sono partiti da un posto preciso d'Italia e sono arrivati lontano: "
             "regione per regione, città per città, settore per settore. Per ogni video del canale, qui trovi le fonti della ricerca e i crediti di immagini, video e mappe.</p>"
             + (f"<div class=serie>Le famiglie</div>{''.join(voce(v) for v in fam)}" if fam else "<p>Il primo episodio arriva presto.</p>")
             + (f"<div class=serie>La prima serie: i cognomi</div>{''.join(voce(v) for v in cog)}" if cog else ''))
    open(os.path.join(QUI, 'index.html'), 'w', encoding='utf-8').write(scheletro(f'Casato Italiano · {MOTTO}', corpo, "Casato Italiano, il canale YouTube sull'orgoglio italiano, luogo per luogo: fonti e crediti di ogni video", BASE + '/'))
    open(os.path.join(QUI, '404.html'), 'w', encoding='utf-8').write(scheletro('Pagina non trovata · Casato Italiano',
        "<h1>Pagina non trovata</h1><p>Questa pagina non esiste. <a href=\"/\">Torna all'elenco dei video</a>.</p>", r='/'))
    oggi = datetime.date.today().isoformat()
    sm = ''.join(f"<url><loc>{BASE}/video/{v['slug']}/</loc><lastmod>{(v.get('pubblico_dal') or v.get('data') or oggi)[:10]}</lastmod></url>" for v in pub)
    open(os.path.join(QUI, 'sitemap.xml'), 'w').write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{BASE}/</loc></url>{sm}</urlset>')
    attesa = [f"{v['slug'][:40]} ({quando(v)})" for v in vids if not uscito(v)]
    if os.environ.get('GITHUB_ACTIONS'):   # visibile nelle annotazioni della run
        risp = sum(1 for x in _STATO_YT.values() if x is not None)
        print(f"::notice title=YouTube::{risp} video su {len(_STATO_YT)} verificati su YouTube; in home {len(pub)}")
    print(f'sito: {len(vids)} pagine video, {len(pub)} in home' + (f"; in attesa dell'uscita: {', '.join(attesa)}" if attesa else ''))
    for w in avvisi: print('·', w)
    # rete di sicurezza: nessun episodio esce dalla home se non perché ritirato da YouTube o spento a mano (`pubblica: false`)
    persi = sorted(prima - {v['slug'] for v in pub} - fuori_voluti)
    if persi and os.environ.get('CASATO_CONFERMA_RITIRATI') != '1':
        errori.insert(0, f"RETE DI SICUREZZA: uscirebbero dalla home senza motivo {len(persi)} episodi ({', '.join(x[:32] for x in persi[:6])}). Non pubblicare.")
        print('\n'.join(errori)); sys.exit(2)
    if errori:
        print('\n'.join(errori)); sys.exit(2 if _BLOCCO[0] else 1)


if __name__ == '__main__':
    main()
