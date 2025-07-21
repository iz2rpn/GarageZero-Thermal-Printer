

# GarageZero Thermal Printer

**Quick and easy thermal printing from your desktop!**

A lightweight Python/Tkinter tool to send **images**, **logos**, and **receipts** to ESC/POS thermal printers (e.g. Epson TM‑P20). Supports QR codes, barcodes, and a clean, customizable layout.

---

## Key Features

* **Image Printing**

  * Load PNG/JPEG/BMP/GIF files
  * Automatic black & white conversion, centered to 384px width

* **Test Receipt**

  * Customizable header and footer (multi-line)
  * Custom logo
  * Products with name, quantity, and price, including automatic line/total calculation
  * QR code and barcode (custom content)

* **Configuration**

  * Serial port selection (e.g. COM8 or /dev/ttyUSB0)
  * Baudrate (default: 9600)

* **Live previews** for image and logo

* Automatic serial port management (open/close)

---

## Requirements

* Python 3.9+

* Libraries:

  ```bash
  pip install python-escpos pillow qrcode python-barcode pyserial
  ```

* ESC/POS thermal printer (Epson TM‑P20 recommended)

---

## Getting Started

1. Clone or download the project.
2. Install dependencies.
3. Run:

   ```bash
   python app.py
   ```
4. Configure the serial port and baudrate, then choose **Image Printing** or **Test Receipt**.

---

## Known Issues

* If printing doesn't start, try **restarting the serial interface** (unplug/replug the printer or restart the app).

---

## License

Apache License Version 2.0, January 2004
Copyright (c) \[2025] \[Pietro Marchetta]

---

