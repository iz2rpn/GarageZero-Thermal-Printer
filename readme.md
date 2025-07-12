# GarageZero Thermal Printer

**Stampa termica semplice e veloce dal tuo desktop!**

Un piccolo tool in Python/Tkinter per inviare **immagini**, **loghi** e **scontrini** alle stampanti ESC/POS (p.es. Epson TM‑P20). Supporta QR code, barcode e layout personalizzabile senza fronzoli.

---

## Funzioni principali

* **Stampa Immagine**

  * Carica PNG/JPEG/BMP/GIF
  * Conversione automatica in bianco/nero, centrata a 384px
* **Scontrino di Test**

  * Header e footer modificabili (multilinea)
  * Logo personalizzato
  * Prodotti: nome, quantità, prezzo con calcolo automatico
  * QR code e barcode (contenuto a scelta)
* **Configura**

  * Porta seriale (es. COM8 o /dev/ttyUSB0)
  * Baudrate (default 9600)
* **Anteprime** live per immagine e logo
* Gestione automatica della porta (apertura/chiusura)

---

## Requisiti

* Python 3.9+
* Librerie:

  ```bash
  pip install python-escpos pillow qrcode python-barcode pyserial
  ```
* Stampante termica ESC/POS (consigliata Epson TM‑P20)

---

## Avvio

1. Clona o scarica il progetto.
2. Installa le dipendenze.
3. ```bash
   python app.py
   ```
4. Configura porta e baudrate, poi scegli tra **Stampa Immagine** e **Scontrino di Test**.

---

## Problemi noti

* Se la stampa non parte, prova a **riavviare l’interfaccia seriale** (scollega/ricollega la stampante o chiudi e riapri l’app).

---

© 2025 iz2rpn • MIT License
