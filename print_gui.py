import os
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional

import qrcode
import serial  # per controllo porta
from escpos.printer import Serial as EscposSerial
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from PIL import Image, ImageOps, ImageTk


class ThermalPrinterApp(tk.Tk):
    """
    Applicazione Tkinter per stampare immagini e scontrini
    su stampanti termiche ESC/POS.
    """

    DEFAULT_PORT = "COM8"
    DEFAULT_BAUDRATE = 9600
    MAX_WIDTH = 384  # pixel massimi per larghezza stampa

    def __init__(self):
        super().__init__()
        self.title("GarageZero Thermal Printer")
        self.geometry("650x700")

        # Configurazione stampante
        self.port_var = tk.StringVar(value=self.DEFAULT_PORT)
        self.baud_var = tk.IntVar(value=self.DEFAULT_BAUDRATE)

        # Stato
        self.selected_image: Optional[str] = None
        self.logo_path: Optional[str] = None
        self.product_rows: List[dict] = []
        self.qr_payload = tk.StringVar()
        self.barcode_payload = tk.StringVar()
        self.qr_enabled = tk.BooleanVar()
        self.barcode_enabled = tk.BooleanVar()

        self._build_ui()

    def _build_ui(self) -> None:
        # Frame configurazione
        frame = ttk.LabelFrame(self, text="Configurazione Stampante")
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame, text="Porta COM:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.port_var, width=10).grid(row=0, column=1)
        ttk.Label(frame, text="Baudrate:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        ttk.Entry(frame, textvariable=self.baud_var, width=10).grid(row=0, column=3)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        img_tab = ttk.Frame(notebook)
        rec_tab = ttk.Frame(notebook)
        notebook.add(img_tab, text="Stampa Immagine")
        notebook.add(rec_tab, text="Scontrino di Test")

        self._build_image_tab(img_tab)
        self._build_receipt_tab(rec_tab)

    def _build_image_tab(self, parent: ttk.Frame) -> None:
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, pady=10)
        ttk.Button(container, text="Carica Immagine", command=self.load_image).pack(
            pady=5
        )
        self.preview_image_lbl = ttk.Label(container)
        self.preview_image_lbl.pack(pady=5)
        ttk.Button(container, text="Stampa Immagine", command=self.print_image).pack(
            pady=5
        )

    def _build_receipt_tab(self, parent: ttk.Frame) -> None:
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        container = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        ttk.Button(container, text="Carica Logo", command=self.load_logo).pack(pady=5)
        self.preview_logo_lbl = ttk.Label(container)
        self.preview_logo_lbl.pack(pady=5)

        prod_frame = ttk.LabelFrame(container, text="Prodotti")
        prod_frame.pack(fill="x", pady=5)
        ttk.Button(
            container,
            text="Aggiungi Prodotto",
            command=lambda: self.add_product_row(prod_frame),
        ).pack(pady=2)

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

    @staticmethod
    def check_printer_port(port: str, baudrate: int) -> bool:
        try:
            with serial.Serial(port=port, baudrate=baudrate, timeout=1):
                return True
        except serial.SerialException:
            return False

    @staticmethod
    def convert_image(filepath: str, max_width: int = MAX_WIDTH) -> Image.Image:
        img = Image.open(filepath).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
        gray = img.convert("L")
        bw = gray.point(lambda x: 0 if x < 128 else 255, "1")
        if bw.width < max_width:
            pad = (max_width - bw.width) // 2
            bw = ImageOps.expand(bw, border=(pad, 0), fill=255)
        return bw

    def load_image(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Immagini", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if not path:
            return
        self.selected_image = path
        preview = self.convert_image(path).copy()
        preview.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(preview)
        self.preview_image_lbl.config(image=photo)
        self.preview_image_lbl.image = photo

    def print_image(self) -> None:
        if not self.selected_image:
            messagebox.showwarning("Attenzione", "Nessuna immagine selezionata.")
            return
        port, baud = self.port_var.get(), self.baud_var.get()
        if not self.check_printer_port(port, baud):
            messagebox.showerror("Errore", f"Porta {port} non disponibile.")
            return

        printer = None
        try:
            printer = EscposSerial(devfile=port, baudrate=baud)
            printer.set(align="center")
            bw = self.convert_image(self.selected_image)
            printer.image(bw)
            printer.cut()
            messagebox.showinfo("Successo", "Immagine inviata alla stampante.")
        except Exception as e:
            messagebox.showerror("Errore", str(e))
        finally:
            if printer:
                try:
                    printer.close()
                except Exception:
                    pass

    def load_logo(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Immagini", "*.png;*.jpg;*.bmp")])
        if not path:
            return
        self.logo_path = path
        preview = self.convert_image(path).copy()
        preview.thumbnail((200, 200))
        photo = ImageTk.PhotoImage(preview)
        self.preview_logo_lbl.config(image=photo)
        self.preview_logo_lbl.image = photo

    def add_product_row(self, container: ttk.Frame) -> None:
        frame = ttk.Frame(container)
        frame.pack(fill="x", pady=2, padx=5)
        name = ttk.Entry(frame, width=20)
        name.pack(side="left", padx=5)
        qty = ttk.Entry(frame, width=5)
        qty.pack(side="left", padx=5)
        price = ttk.Entry(frame, width=7)
        price.pack(side="left", padx=5)
        self.product_rows.append({"name": name, "qty": qty, "price": price})

    def print_receipt(self) -> None:
        port, baud = self.port_var.get(), self.baud_var.get()
        if not self.check_printer_port(port, baud):
            messagebox.showerror("Errore", f"Porta {port} non disponibile.")
            return

        items = []
        for e in self.product_rows:
            try:
                items.append(
                    {
                        "name": e["name"].get().strip(),
                        "qty": int(e["qty"].get()),
                        "price": float(e["price"].get()),
                    }
                )
            except ValueError:
                continue

        printer = None
        try:
            printer = EscposSerial(devfile=port, baudrate=baud)
            printer.set(align="center")
            # Logo
            if self.logo_path:
                printer.image(self.convert_image(self.logo_path))
            # Header
            printer.text("GARAGEZERO\n")
            printer.text("----------------------------\n")
            # Prodotti
            for it in items:
                line = f"{it['name'][:15]:15}{it['qty']:>3} x {it['price']:>6.2f}\n"
                printer.text(line)
            printer.text("----------------------------\n")
            total = sum(it["qty"] * it["price"] for it in items)
            printer.text(f"TOTALE: {total:.2f}\n")
            # QR/barcode
            if self.qr_enabled.get():
                printer.qr(self.qr_payload.get(), size=6)
            if self.barcode_enabled.get():
                printer.barcode(self.barcode_payload.get(), "CODE128")
            printer.cut()
            messagebox.showinfo("Successo", "Scontrino inviato alla stampante.")
        except Exception as e:
            messagebox.showerror("Errore", str(e))
        finally:
            if printer:
                try:
                    printer.close()
                except Exception:
                    pass


if __name__ == "__main__":
    app = ThermalPrinterApp()
    app.mainloop()
