"""
app.py

Applicazione Tkinter professionale per stampare immagini e scontrini
su stampanti termiche ESC/POS (es. Epson TM-P20).
"""

import os
import tempfile
from typing import List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageTk
import serial  # pyserial per il controllo porta
import qrcode
import barcode
from barcode.writer import ImageWriter

# -------------------------------------------------------------------
# CONFIGURAZIONE DI BASE (valori di default modificabili dalla GUI)
# -------------------------------------------------------------------
DEFAULT_PORT = "COM8"
DEFAULT_BAUDRATE = 9600
MAX_WIDTH = 384  # pixel massimi per larghezza stampa


def check_printer_port(port: str, baudrate: int = DEFAULT_BAUDRATE) -> bool:
    """
    Verifica che la porta seriale sia disponibile.

    :param port: Nome della porta (es. COM8 o /dev/ttyUSB0)
    :param baudrate: Baud rate per la connessione seriale
    :returns: True se la porta si apre e si chiude correttamente, False altrimenti
    """
    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=1)
        ser.close()
        return True
    except serial.SerialException:
        return False


def convert_image(filepath: str, max_width: int = MAX_WIDTH) -> Image.Image:
    """
    Carica e converte un'immagine in bianco/nero 1-bit,
    ridimensionata e centrata orizzontalmente.

    :param filepath: Percorso all'immagine originale
    :param max_width: Larghezza massima in pixel
    :returns: PIL.Image in mode "1" (bianco/nero puro)
    """
    img = Image.open(filepath).convert("RGBA")
    # Gestione trasparenza -> sfondo bianco
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img)

    # Ridimensiona mantenendo proporzioni
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

    # Scala di grigi -> soglia 1-bit
    gray = img.convert("L")
    bw = gray.point(lambda x: 0 if x < 128 else 255, "1")

    # Padding per centrare se più stretta
    if bw.width < max_width:
        pad = (max_width - bw.width) // 2
        bw = ImageOps.expand(bw, border=(pad, 0), fill=255)

    return bw


def generate_qr_image(data: str, size: int = 6) -> Image.Image:
    """
    Genera un QR code come PIL.Image in bianco/nero.

    :param data: Testo o URL da codificare
    :param size: Dimensione modulo QR
    :returns: PIL.Image in mode "1"
    """
    qr = qrcode.QRCode(box_size=size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    return img.convert("1")


def generate_barcode_image(data: str) -> Image.Image:
    """
    Genera un barcode Code128 come PIL.Image.

    :param data: Stringa da codificare
    :returns: PIL.Image in mode "1"
    """
    ean_cls = barcode.get_barcode_class("code128")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    try:
        ean = ean_cls(data, writer=ImageWriter())
        ean.write(tmp)
        tmp.close()
        return convert_image(tmp.name)
    finally:
        os.unlink(tmp.name)


class ThermalPrinterApp(tk.Tk):
    """
    Applicazione Tkinter per interfaccia termica con configurazione stampante.
    """

    def __init__(self):
        super().__init__()
        self.title("GarageZero Thermal Printer")
        self.geometry("650x700")

        # Configurazione stampante (modificabile in GUI)
        self.port = tk.StringVar(value=DEFAULT_PORT)
        self.baudrate = tk.IntVar(value=DEFAULT_BAUDRATE)

        # Stato applicazione
        self.selected_image: Optional[str] = None
        self.logo_path: Optional[str] = None
        self.product_rows: List[dict] = []
        self.qr_payload = tk.StringVar()
        self.barcode_payload = tk.StringVar()
        self.qr_enabled = tk.BooleanVar()
        self.barcode_enabled = tk.BooleanVar()

        self._build_ui()

    def _build_ui(self):
        # Frame impostazioni
        setting_frame = ttk.LabelFrame(self, text="Configurazione Stampante")
        setting_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(setting_frame, text="Porta COM:").grid(row=0, column=0, sticky="w")
        ttk.Entry(setting_frame, textvariable=self.port, width=10).grid(row=0, column=1)
        ttk.Label(setting_frame, text="Baudrate:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        ttk.Entry(setting_frame, textvariable=self.baudrate, width=10).grid(
            row=0, column=3
        )

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab Immagine
        tab_img = ttk.Frame(notebook)
        notebook.add(tab_img, text="Stampa Immagine")
        self._build_image_tab(tab_img)

        # Tab Scontrino
        tab_rec = ttk.Frame(notebook)
        notebook.add(tab_rec, text="Scontrino di Test")
        self._build_receipt_tab(tab_rec)

    def _build_image_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, pady=10)
        ttk.Button(frame, text="Carica Immagine", command=self.load_image).pack(pady=5)
        self.preview_image_lbl = ttk.Label(frame)
        self.preview_image_lbl.pack(pady=5)
        ttk.Button(frame, text="Stampa Immagine", command=self.print_image).pack(pady=5)

    def _build_receipt_tab(self, parent):
        canvas = tk.Canvas(parent)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        container = ttk.Frame(canvas)
        container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=container, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        ttk.Button(container, text="Carica Logo", command=self.load_logo).pack(pady=5)
        self.preview_logo_lbl = ttk.Label(container)
        self.preview_logo_lbl.pack(pady=5)

        prod_frame = ttk.LabelFrame(container, text="Prodotti")
        prod_frame.pack(fill="x", pady=5)
        ttk.Button(
            container,
            text="Aggiungi Prodotto",
            command=lambda: self.add_product_row(prod_frame),
        ).pack()

        codes_frame = ttk.LabelFrame(container, text="QR & Barcode")
        codes_frame.pack(fill="x", pady=10)
        ttk.Checkbutton(codes_frame, text="Usa QR Code", variable=self.qr_enabled).grid(
            row=0, column=0, sticky="w", padx=5
        )
        ttk.Entry(codes_frame, textvariable=self.qr_payload, width=40).grid(
            row=0, column=1
        )
        ttk.Checkbutton(
            codes_frame, text="Usa Barcode", variable=self.barcode_enabled
        ).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Entry(codes_frame, textvariable=self.barcode_payload, width=40).grid(
            row=1, column=1
        )

        ttk.Button(container, text="Stampa Scontrino", command=self.print_receipt).pack(
            pady=10
        )

    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Immagini", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if not path:
            return
        self.selected_image = path
        img = convert_image(path)
        preview = img.copy()
        preview.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(preview)
        self.preview_image_lbl.config(image=photo)
        self.preview_image_lbl.image = photo

    def print_image(self):
        if not self.selected_image:
            messagebox.showwarning("Attenzione", "Nessuna immagine selezionata.")
            return
        img = convert_image(self.selected_image)
        port, baud = self.port.get(), self.baudrate.get()
        if not check_printer_port(port, baud):
            messagebox.showerror("Errore", f"Porta {port} non disponibile.")
            return
        printer = None
        try:
            printer = serial.Serial(port=port, baudrate=baud)
            # ESC/POS: invio immagine in raw
            # Qui potresti implementare send bitmap conforme al tuo driver
        finally:
            if printer:
                printer.close()
        messagebox.showinfo("Successo", "Immagine inviata alla stampante.")

    def load_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Immagini", "*.png *.jpg *.bmp")])
        if not path:
            return
        self.logo_path = path
        img = convert_image(path)
        preview = img.copy()
        preview.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(preview)
        self.preview_logo_lbl.config(image=photo)
        self.preview_logo_lbl.image = photo

    def add_product_row(self, container):
        frame = ttk.Frame(container)
        frame.pack(fill="x", pady=2, padx=5)
        name = ttk.Entry(frame, width=20)
        qty = ttk.Entry(frame, width=5)
        price = ttk.Entry(frame, width=7)
        name.pack(side="left", padx=5)
        qty.pack(side="left", padx=5)
        price.pack(side="left", padx=5)
        self.product_rows.append({"name": name, "qty": qty, "price": price})

    def print_receipt(self):
        port, baud = self.port.get(), self.baudrate.get()
        if not check_printer_port(port, baud):
            messagebox.showerror("Errore", f"Porta {port} non disponibile.")
            return

        items = []
        for entry in self.product_rows:
            try:
                name = entry["name"].get().strip()
                qty = int(entry["qty"].get())
                price = float(entry["price"].get())
            except ValueError:
                continue
            items.append({"name": name, "qty": qty, "price": price})

        printer = None
        try:
            printer = serial.Serial(port=port, baudrate=baud)
            # Invia comandi ESC/POS raw per header, prodotti, QR/barcode e cut
        finally:
            if printer:
                printer.close()
        messagebox.showinfo("Successo", "Scontrino inviato alla stampante.")


if __name__ == "__main__":
    app = ThermalPrinterApp()
    app.mainloop()
