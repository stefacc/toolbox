# overlay - trigger visivo su una zona dello schermo

Mette un overlay verde semitrasparente su una zona dello schermo, la osserva e,
quando la zona passa dallo **stato X** allo **stato Y**, esegue un'azione (click).

Solo Windows. Unica dipendenza: Pillow.

```
pip install -r requirements.txt
python overlay.py
```

## Uso

1. **Seleziona zona** - trascina un rettangolo sullo schermo (Esc annulla).
2. **Cattura stato X** - salva l'aspetto attuale della zona (stato di partenza).
3. **Cattura stato Y** - porta la zona nello stato che deve far scattare l'azione e cattura.
4. **Punto click (3s)** - entro 3 secondi porta il mouse dove cliccare.
   Se non impostato, clicca al centro della zona.
5. **Avvia** o **F8** - avvia il monitoraggio. F8 lo ferma da qualsiasi finestra.

## Come funziona

- L'overlay e' **click-through**: i click lo attraversano.
- L'overlay e' **escluso dalle catture dello schermo** (`SetWindowDisplayAffinity`),
  quindi il verde non falsa il confronto.
- Ogni lettura viene ridotta a 32x32 e confrontata con le immagini di riferimento:
  la "distanza" (0-255) e' mostrata in tempo reale. Sotto la **soglia** lo stato e'
  riconosciuto, altrimenti e' `?` e non succede nulla.
- Uno stato deve restare uguale per 2 letture di fila prima di contare; dopo un'azione
  c'e' un **cooldown** (default 1 s).
- Azioni: click sinistro, doppio click, click destro; opzione per riportare il mouse
  dov'era.

Zona, punto, impostazioni e immagini di riferimento vengono salvati accanto allo
script (`config.json`, `stato_X.png`, `stato_Y.png`) e ricaricati all'avvio.
