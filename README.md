# casatoitaliano-sito

**Sito offline dal 26/11/2026** (richiesta di Alessandro). Ogni indirizzo di casatoitaliano.it risponde 404 con la pagina `404.html`; l'aggiornamento automatico da YouTube è spento perché il flusso `.github/workflows/uscite.yml` è stato tolto insieme al resto.

Tutto il sito com'era (pagine, dati, `build.py`, flusso automatico) è nel ramo `sito-online-2026-11-26`.

## Rimettere online
`git revert` del commit «Sito offline», poi push su `main`: tornano pagine, dati e aggiornamento automatico.
