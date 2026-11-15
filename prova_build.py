#!/usr/bin/env python3
"""prova_build.py — prove di build.py con risposte finte di YouTube (CASATO_YT_FINTO). Lavora su una copia in una cartella temporanea: non tocca il sito.
  python3 prova_build.py"""
import glob, json, os, re, shutil, subprocess, sys, tempfile

QUI = os.path.dirname(os.path.abspath(__file__)); ok = ko = 0


def vedi(nome, cond, extra=''):
    global ok, ko
    if cond: ok += 1; print('ok  ', nome)
    else: ko += 1; print('KO  ', nome, extra)


def copia():
    d = tempfile.mkdtemp(prefix='casato_prova_')
    for n in ('build.py', 'index.html', 'assets', 'dati', 'video', '404.html', 'sitemap.xml'):
        s = os.path.join(QUI, n)
        (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, os.path.join(d, n))
    return d


def gira(d, finto, **env):
    p = os.path.join(d, '_finto.json'); json.dump(finto, open(p, 'w'))
    r = subprocess.run([sys.executable, os.path.join(d, 'build.py')], capture_output=True, text=True, env=dict(os.environ, CASATO_YT_FINTO=p, **env))
    os.remove(p); return r.returncode, r.stdout + r.stderr


def home(d): return re.findall(r'class=ep href="video/([^/"]+)/"', open(os.path.join(d, 'index.html'), encoding='utf-8').read())
def dato(d, slug): return json.load(open(os.path.join(d, 'dati/video', slug + '.json'), encoding='utf-8'))


V = {os.path.basename(f)[:-5]: json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(QUI, 'dati/video/*.json'))}
GIA_RITIRATI = {s for s, v in V.items() if v.get('ritirato_dal')}      # episodi che YouTube non ha più già prima della prova: restano negati
V = {s: v for s, v in V.items() if s not in GIA_RITIRATI}
ID = {s: v['youtube_id'] for s, v in V.items()}; tutti = {i: {'title': V[s]['titolo']} for s, i in ID.items()}
d = copia(); n0 = len(home(d))

c, o = gira(d, tutti)
vedi('1 · tutti pubblici: codice 0, home uguale, ogni episodio ricorda pubblico_dal', c == 0 and len(home(d)) == n0 and all(dato(d, s).get('pubblico_dal') for s in V), o[-300:])
ordine1 = home(d)
c, o = gira(d, {})                      # YouTube non risponde a nessuno
vedi('2 · YouTube muto: codice 0, home identica e nello stesso ordine', c == 0 and home(d) == ordine1, o[-300:])
c, o = gira(d, {i: False for i in ID.values()})      # YouTube nega tutti: blocco
vedi('3 · YouTube nega tutti: codice 2 (non pubblicare), nessuna pagina cancellata, nessun ritirato_dal', c == 2 and 'BLOCCO' in o and all(os.path.exists(os.path.join(d, 'video', s, 'index.html')) for s in V) and not any(dato(d, s).get('ritirato_dal') for s in V), o[-300:])
x = ordine1[2]; f = dict(tutti); f[ID[x]] = False
c, o = gira(d, f)
vedi('4 · un video passato in privato: codice 0, fuori dalla home, pagina cancellata, fuori dalla sitemap, dati conservati', c == 0 and x not in home(d) and len(home(d)) == n0 - 1 and not os.path.exists(os.path.join(d, 'video', x)) and x not in open(os.path.join(d, 'sitemap.xml')).read() and dato(d, x).get('ritirato_dal') and dato(d, x).get('pubblico_dal'), o[-300:])
c, o = gira(d, {})
vedi('5 · poi YouTube muto: il ritirato resta ritirato, gli altri restano', c == 0 and x not in home(d) and len(home(d)) == n0 - 1 and not os.path.exists(os.path.join(d, 'video', x)), o[-300:])
c, o = gira(d, tutti)
vedi('6 · il video torna pubblico: di nuovo in home allo stesso posto, pagina rifatta', c == 0 and home(d) == ordine1 and os.path.exists(os.path.join(d, 'video', x, 'index.html')) and not dato(d, x).get('ritirato_dal'), o[-300:])
f = dict(tutti); f[ID[ordine1[0]]] = {'title': 'Titolo nuovo messo in Studio'}
c, o = gira(d, f)
vedi('7 · titolo cambiato su YouTube: il sito lo segue (dati, home, pagina)', c == 0 and dato(d, ordine1[0])['titolo'] == 'Titolo nuovo messo in Studio' and 'Titolo nuovo messo in Studio' in open(os.path.join(d, 'index.html'), encoding='utf-8').read() and 'Titolo nuovo messo in Studio' in open(os.path.join(d, 'video', ordine1[0], 'index.html'), encoding='utf-8').read(), o[-300:])
# episodio nuovo, ancora privato, poi pubblico
nuovo = dict(dato(d, ordine1[1])); nuovo.update(slug='99-episodio-di-prova', youtube_id='PROVA_NUOVO', titolo='Episodio di prova'); [nuovo.pop(k, None) for k in ('pubblico_dal', 'ritirato_dal', 'uscita', 'data')]
json.dump(nuovo, open(os.path.join(d, 'dati/video/99-episodio-di-prova.json'), 'w', encoding='utf-8'), ensure_ascii=False)
f = dict(tutti); f['PROVA_NUOVO'] = False
c, o = gira(d, f)
vedi('8 · episodio nuovo ancora privato: fuori dalla home, la pagina esiste e dice che esce', c == 0 and '99-episodio-di-prova' not in home(d) and 'Il video esce su YouTube' in open(os.path.join(d, 'video/99-episodio-di-prova/index.html'), encoding='utf-8').read(), o[-300:])
f['PROVA_NUOVO'] = {'title': 'Episodio di prova'}
c, o = gira(d, f)
vedi('9 · diventa pubblico: primo in home, senza date scritte a mano', c == 0 and home(d)[0] == '99-episodio-di-prova' and dato(d, '99-episodio-di-prova').get('pubblico_dal'), o[-300:])
# una fonte non pubblicabile in un episodio
y = ordine1[3]; v = dato(d, y); (v.get('capitoli') or [{'fonti': v.setdefault('fonti_ricerca', [])}])[0]['fonti'].append({'titolo': 'TODO da verificare', 'url': 'https://example.com'})
json.dump(v, open(os.path.join(d, 'dati/video', y + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
f = dict(tutti); f['PROVA_NUOVO'] = {'title': 'Episodio di prova'}; f[ID[ordine1[5]]] = {'title': 'Altro titolo nuovo'}
c, o = gira(d, f)
vedi('10 · un episodio con una fonte sbagliata: codice 1, resta in home come prima, gli altri si aggiornano lo stesso', c == 1 and 'FONTE NON PUBBLICABILE' in o and y in home(d) and 'Altro titolo nuovo' in open(os.path.join(d, 'index.html'), encoding='utf-8').read(), o[-400:])
# quattro ritirati insieme: blocco; con la conferma passano
f = dict(tutti); f['PROVA_NUOVO'] = {'title': 'Episodio di prova'}
for s in ordine1[6:10]: f[ID[s]] = False
c, o = gira(d, f)
vedi('11 · quattro video negati insieme: codice 2, niente toccato', c == 2 and all(os.path.exists(os.path.join(d, 'video', s, 'index.html')) for s in ordine1[6:10]), o[-300:])
c, o = gira(d, f, CASATO_CONFERMA_RITIRATI='1')
vedi('12 · gli stessi quattro con la conferma: ritirati', all(not os.path.exists(os.path.join(d, 'video', s)) for s in ordine1[6:10]) and not set(ordine1[6:10]) & set(home(d)), o[-300:])
shutil.rmtree(d)
print(f'{ok} controlli ok, {ko} falliti'); sys.exit(1 if ko else 0)
