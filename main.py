import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import io
import os
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

class OrganizatorKryminalny:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizator Kryminalny v2.6.5")
        self.root.geometry("1150x750")
        self.root.configure(bg="#1e272e")
        
        self.db_name = "baza_danych.db"
        self.init_db()
        self.icon_cache = []
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=60, background="#2f3542", foreground="white", fieldbackground="#2f3542")
        self.style.map("Treeview", background=[('selected', '#3742fa')])
        
        # Header
        header = tk.Frame(self.root, bg="#2f3640", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="🚔 SYSTEM KARTOTEKI OPERACYJNEJ", bg="#2f3640", fg="#dcdde1", font=("Arial", 14, "bold")).pack(pady=15)

        # Search
        search_frame = tk.Frame(self.root, bg="#1e272e")
        search_frame.pack(fill=tk.X, side=tk.TOP, padx=20, pady=10)
        self.search_entry = tk.Entry(search_frame, bg="#353b48", fg="white", font=("Arial", 12))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.odswiez_liste())

        # Footer
        footer = tk.Frame(self.root, bg="#2f3640", pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        btn_c = {"font": ("Arial", 9, "bold"), "fg": "white", "padx": 10}
        tk.Button(footer, text="➕ DODAJ", bg="#44bd32", command=self.okno_dodawania, **btn_c).pack(side=tk.LEFT, padx=10)
        tk.Button(footer, text="🗑️ USUŃ", bg="#c23616", command=self.usun_osobe, **btn_c).pack(side=tk.LEFT)
        tk.Button(footer, text="📂 IMPORT", bg="#718093", command=self.importuj_baze, **btn_c).pack(side=tk.RIGHT, padx=10)
        tk.Button(footer, text="📤 EKSPORT", bg="#273c75", command=self.eksportuj_baze, **btn_c).pack(side=tk.RIGHT)

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=("ID", "Osoba", "Sprawa", "Klub"), show='tree headings')
        self.tree.heading("#0", text="Foto")
        self.tree.heading("ID", text="ID"); self.tree.heading("Osoba", text="Osoba")
        self.tree.heading("Sprawa", text="Numer Sprawy"); self.tree.heading("Klub", text="Klub")
        self.tree.column("#0", width=80, anchor="center"); self.tree.column("ID", width=50, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.pokaz_detale())

        self.odswiez_liste()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute('''CREATE TABLE IF NOT EXISTS osoby
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, imie TEXT, nazwisko TEXT, 
                      klub TEXT, pojazdy TEXT, adresy TEXT, nr_sprawy TEXT, 
                      telefon TEXT, notatka TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS zdjecia
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, osoba_id INTEGER, 
                      foto BLOB, czy_profilowe INTEGER DEFAULT 0,
                      FOREIGN KEY(osoba_id) REFERENCES osoby(id) ON DELETE CASCADE)''')
        conn.commit(); conn.close()

    def center_window(self, window, width, height):
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def odswiez_liste(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.icon_cache = [] 
        f = f"%{self.search_entry.get()}%"
        conn = sqlite3.connect(self.db_name)
        query = """
            SELECT o.id, o.imie, o.nazwisko, o.nr_sprawy, o.klub, z.foto 
            FROM osoby o 
            LEFT JOIN zdjecia z ON o.id = z.osoba_id AND z.czy_profilowe = 1
            WHERE o.imie LIKE ? OR o.nazwisko LIKE ? OR o.nr_sprawy LIKE ? OR o.pojazdy LIKE ? OR o.adresy LIKE ? OR o.telefon LIKE ?
            GROUP BY o.id
        """
        cursor = conn.execute(query, (f,f,f,f,f,f))
        for r in cursor:
            img_tk = None
            if r[5]:
                try:
                    img = Image.open(io.BytesIO(r[5])); img.thumbnail((55, 55))
                    img_tk = ImageTk.PhotoImage(img); self.icon_cache.append(img_tk)
                except: pass
            self.tree.insert("", tk.END, image=img_tk if img_tk else "", values=(r[0], f"{r[1]} {r[2]}", r[3], r[4]))
        conn.close()

    def okno_dodawania(self, edycja_id=None, dane_startowe=None):
        okno = tk.Toplevel(self.root)
        okno.title("DODAJ / EDYTUJ OSOBĘ")
        okno.configure(bg="#2f3542")
        self.center_window(okno, 550, 800)
        
        # Konfiguracja kolumn okna
        okno.columnconfigure(1, weight=1)

        self.temp_photos = []
        if edycja_id:
            conn = sqlite3.connect(self.db_name)
            p_data = conn.execute("SELECT foto, czy_profilowe FROM zdjecia WHERE osoba_id=?", (edycja_id,)).fetchall()
            conn.close()
            self.temp_photos = [list(row) for row in p_data]

        rows_vehicles = []; rows_phones = []

        # --- FUNKCJE POMOCNICZE ---
        def wybierz_f():
            if len(self.temp_photos) >= 5:
                messagebox.showwarning("Limit", "Maksymalnie 5 zdjęć."); return
            sciezki = filedialog.askopenfilenames(filetypes=[("Obrazy", "*.jpg *.png *.jpeg")])
            for p in sciezki:
                if len(self.temp_photos) < 5:
                    with open(p, "rb") as f:
                        is_prof = 1 if not self.temp_photos else 0
                        self.temp_photos.append([f.read(), is_prof])
            set_mini_gallery()

        def set_mini_gallery():
            for widget in gallery_inner.winfo_children(): widget.destroy()
            for i, (blob, is_prof) in enumerate(self.temp_photos):
                frame = tk.Frame(gallery_inner, bg="#2f3542")
                frame.pack(side=tk.LEFT, padx=5)
                try:
                    img = Image.open(io.BytesIO(blob)); img.thumbnail((70, 70))
                    ph = ImageTk.PhotoImage(img)
                    btn = tk.Button(frame, image=ph, bg="#2f3542", relief="solid" if is_prof else "flat", 
                                   bd=3 if is_prof else 0, command=lambda idx=i: ustaw_profilowe(idx))
                    btn.image = ph; btn.pack()
                    tk.Button(frame, text="USUŃ", bg="#c23616", fg="white", font=("Arial", 7), 
                             command=lambda idx=i: usun_foto(idx)).pack(fill=tk.X)
                except: pass

        def usun_foto(idx):
            was_prof = self.temp_photos[idx][1]
            self.temp_photos.pop(idx)
            if was_prof and self.temp_photos: self.temp_photos[0][1] = 1
            set_mini_gallery()

        def ustaw_profilowe(idx):
            for i in range(len(self.temp_photos)): self.temp_photos[i][1] = 1 if i == idx else 0
            set_mini_gallery()

        def add_v_row(brand="", plate=""):
            row = tk.Frame(vehicle_container, bg="#353b48")
            row.pack(fill=tk.X, pady=2)
            e1 = tk.Entry(row, width=20); e1.insert(0, brand); e1.pack(side=tk.LEFT, padx=2)
            tk.Label(row, text="rej:", bg="#353b48", fg="white").pack(side=tk.LEFT)
            e2 = tk.Entry(row, width=15); e2.insert(0, plate); e2.pack(side=tk.LEFT, padx=2)
            tk.Button(row, text="X", bg="#c23616", fg="white", command=lambda: [row.destroy(), rows_vehicles.remove((e1, e2))]).pack(side=tk.LEFT)
            rows_vehicles.append((e1, e2))

        def add_p_row(val=""):
            row = tk.Frame(phone_container, bg="#353b48")
            row.pack(fill=tk.X, pady=2)
            e = tk.Entry(row, width=40); e.insert(0, val); e.pack(side=tk.LEFT, padx=2)
            tk.Button(row, text="X", bg="#c23616", fg="white", command=lambda: [row.destroy(), rows_phones.remove(e)]).pack(side=tk.LEFT)
            rows_phones.append(e)

        # --- BUDOWA GUI (GRID) ---
        r = 0
        fields = [("Imię", "imie"), ("Nazwisko", "nazwisko"), ("Klub", "klub")]
        entries = {}
        for label, key in fields:
            tk.Label(okno, text=label, bg="#2f3542", fg="white").grid(row=r, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(okno); e.grid(row=r, column=1, padx=10, pady=5, sticky="ew")
            if dane_startowe: 
                val = dane_startowe[fields.index((label, key))+1]
                e.insert(0, val if val else "")
            entries[key] = e; r += 1

        # Pojazdy
        tk.Label(okno, text="POJAZDY", bg="#2f3542", fg="#f1c40f", font=("Arial", 9, "bold")).grid(row=r, column=0, padx=10, sticky="nw")
        v_btn_frame = tk.Frame(okno, bg="#2f3542")
        v_btn_frame.grid(row=r, column=1, sticky="ew", padx=10)
        tk.Button(v_btn_frame, text="+ DODAJ POJAZD", bg="#2980b9", fg="white", command=add_v_row).pack(anchor="w")
        vehicle_container = tk.Frame(v_btn_frame, bg="#2f3542"); vehicle_container.pack(fill=tk.X, pady=5)
        r += 1

        # Adresy i Nr Sprawy
        for label, key in [("Adresy", "adresy"), ("Nr sprawy", "sprawa")]:
            tk.Label(okno, text=label, bg="#2f3542", fg="white").grid(row=r, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(okno); e.grid(row=r, column=1, padx=10, pady=5, sticky="ew")
            if dane_startowe:
                val = dane_startowe[5] if key == "adresy" else dane_startowe[6]
                e.insert(0, val if val else "")
            entries[key] = e; r += 1

        # Telefony
        tk.Label(okno, text="TELEFONY", bg="#2f3542", fg="#f1c40f", font=("Arial", 9, "bold")).grid(row=r, column=0, padx=10, sticky="nw")
        p_btn_frame = tk.Frame(okno, bg="#2f3542")
        p_btn_frame.grid(row=r, column=1, sticky="ew", padx=10)
        tk.Button(p_btn_frame, text="+ DODAJ TEL", bg="#2980b9", fg="white", command=add_p_row).pack(anchor="w")
        phone_container = tk.Frame(p_btn_frame, bg="#2f3542"); phone_container.pack(fill=tk.X, pady=5)
        r += 1

        # Notatka
        tk.Label(okno, text="Notatka", bg="#2f3542", fg="white").grid(row=r, column=0, padx=10, sticky="nw")
        notatka = tk.Text(okno, height=4, bg="white"); notatka.grid(row=r, column=1, padx=10, pady=5, sticky="ew")
        if dane_startowe: notatka.insert("1.0", dane_startowe[8] if dane_startowe[8] else "")
        r += 1

        # Galeria
        tk.Label(okno, text="GALERIA (max 5)", bg="#2f3542", fg="#3498db", font=("Arial", 9, "bold")).grid(row=r, column=0, padx=10, sticky="nw")
        gal_main_frame = tk.Frame(okno, bg="#2f3542")
        gal_main_frame.grid(row=r, column=1, sticky="ew", padx=10)
        tk.Button(gal_main_frame, text="📸 DODAJ ZDJĘCIA", command=wybierz_f).pack(anchor="w")
        gallery_inner = tk.Frame(gal_main_frame, bg="#2f3542"); gallery_inner.pack(fill=tk.X, pady=5)
        r += 1

        # Zapisz
        def zapisz():
            v_str = " | ".join([f"{b.get()} [{p.get()}]" for b, p in rows_vehicles if b.get() or p.get()])
            p_str = ", ".join([e.get() for e in rows_phones if e.get()])
            data = [entries["imie"].get(), entries["nazwisko"].get(), entries["klub"].get(), 
                    v_str, entries["adresy"].get(), entries["sprawa"].get(), p_str, notatka.get("1.0", tk.END).strip()]
            
            conn = sqlite3.connect(self.db_name); cursor = conn.cursor()
            if edycja_id:
                cursor.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, pojazdy=?, adresy=?, nr_sprawy=?, telefon=?, notatka=? WHERE id=?", (*data, edycja_id))
                cursor.execute("DELETE FROM zdjecia WHERE osoba_id=?", (edycja_id,))
                oid = edycja_id
            else:
                cursor.execute("INSERT INTO osoby (imie, nazwisko, klub, pojazdy, adresy, nr_sprawy, telefon, notatka) VALUES (?,?,?,?,?,?,?,?)", data)
                oid = cursor.lastrowid
            
            for blob, is_p in self.temp_photos:
                cursor.execute("INSERT INTO zdjecia (osoba_id, foto, czy_profilowe) VALUES (?,?,?)", (oid, blob, is_p))
            conn.commit(); conn.close(); okno.destroy(); self.odswiez_liste()

        tk.Button(okno, text="ZAPISZ DANE", command=zapisz, bg="#44bd32", fg="white", font=("Arial", 12, "bold"), height=2).grid(row=r, column=0, columnspan=2, pady=20, sticky="ew", padx=50)

        # Wczytanie danych dynamicznych
        if dane_startowe:
            if dane_startowe[4]:
                for v in dane_startowe[4].split(" | "):
                    if " [" in v: p = v.replace("]","").split(" ["); add_v_row(p[0], p[1])
            if dane_startowe[7]:
                for t in str(dane_startowe[7]).split(", "): add_p_row(t)
        else: add_v_row(); add_p_row()
        set_mini_gallery()

    def pokaz_detale(self):
        sel = self.tree.selection()
        if not sel: return
        id_os = self.tree.item(sel[0])['values'][0]
        conn = sqlite3.connect(self.db_name)
        res = conn.execute("SELECT * FROM osoby WHERE id=?", (id_os,)).fetchone()
        photos = conn.execute("SELECT foto FROM zdjecia WHERE osoba_id=?", (id_os,)).fetchall()
        conn.close()
        
        if res:
            d = tk.Toplevel(self.root); d.title(f"Detale: {res[1]} {res[2]}"); d.configure(bg="#1e272e")
            self.center_window(d, 550, 800)
            c = tk.Canvas(d, bg="#1e272e", highlightthickness=0); s = ttk.Scrollbar(d, orient="vertical", command=c.yview)
            f = tk.Frame(c, bg="#1e272e"); f.bind("<Configure>", lambda e: c.configure(scrollregion=c.bbox("all")))
            c.create_window((0,0), window=f, anchor="nw"); c.configure(yscrollcommand=s.set)
            s.pack(side="right", fill="y"); c.pack(side="left", fill="both", expand=True)

            self.cur_idx = 0
            gal = tk.Frame(f, bg="#1e272e"); gal.pack(pady=10, fill=tk.X)
            l_img = tk.Label(gal, bg="#1e272e"); l_img.pack()
            def up_g():
                if not photos: return
                img = Image.open(io.BytesIO(photos[self.cur_idx][0])); img.thumbnail((400, 400))
                ph = ImageTk.PhotoImage(img); l_img.config(image=ph); l_img.image = ph
                l_c.config(text=f"{self.cur_idx+1} / {len(photos)}")
            
            if photos:
                nav = tk.Frame(gal, bg="#1e272e"); nav.pack()
                tk.Button(nav, text="◀", command=lambda: [setattr(self, 'cur_idx', (self.cur_idx-1)%len(photos)), up_g()]).pack(side=tk.LEFT, padx=10)
                l_c = tk.Label(nav, fg="white", bg="#1e272e"); l_c.pack(side=tk.LEFT)
                tk.Button(nav, text="▶", command=lambda: [setattr(self, 'cur_idx', (self.cur_idx+1)%len(photos)), up_g()]).pack(side=tk.LEFT, padx=10)
                up_g()

            h_f = ("Arial", 12, "bold"); d_f = ("Arial", 10)
            def sec(t, c, col="#f1c40f"):
                if c:
                    tk.Label(f, text=t, bg="#1e272e", fg=col, font=h_f).pack(anchor="w", padx=30, pady=(10, 2))
                    tk.Label(f, text=c, bg="#1e272e", fg="white", font=d_f, justify=tk.LEFT).pack(anchor="w", padx=45)

            sec("👤 OSOBA:", f"{res[1]} {res[2]}"); sec("🏘️ KLUB:", res[3], "#e74c3c")
            sec("📁 NUMER SPRAWY:", res[6]); sec("📍 ADRESY:", res[5])
            if res[4]:
                tk.Label(f, text="🚗 POJAZDY:", bg="#1e272e", fg="#3498db", font=h_f).pack(anchor="w", padx=30, pady=(10, 2))
                for v in res[4].split(" | "): tk.Label(f, text=f"• {v}", bg="#1e272e", fg="white", font=d_f).pack(anchor="w", padx=45)
            if res[7]:
                tk.Label(f, text="📞 TELEFONY:", bg="#1e272e", fg="#2ecc71", font=h_f).pack(anchor="w", padx=30, pady=(10, 2))
                for t in res[7].split(", "): tk.Label(f, text=f"• {t}", bg="#1e272e", fg="white", font=d_f).pack(anchor="w", padx=45)
            sec("📝 NOTATKA:", res[8])
            
            b_f = tk.Frame(f, bg="#1e272e"); b_f.pack(pady=30)
            tk.Button(b_f, text="✏️ EDYTUJ", bg="#f39c12", fg="white", command=lambda: [d.destroy(), self.okno_dodawania(id_os, res)]).pack(side=tk.LEFT, padx=10)
            tk.Button(b_f, text="📄 PDF", bg="#2980b9", fg="white", command=lambda: self.generuj_pdf(res)).pack(side=tk.LEFT, padx=10)

    def generuj_pdf(self, dane):
        fname = f"Kartoteka_{dane[1]}_{dane[2]}".replace(" ", "_")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{fname}.pdf")
        if not path: return
        try:
            pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
            f_reg, f_bold = "Arial", "Arial-Bold"
        except: f_reg, f_bold = "Helvetica", "Helvetica-Bold"
        c = canvas.Canvas(path, pagesize=A4); w, h = A4
        c.setFont(f_bold, 18); c.drawString(50, h - 50, "KARTA OPERACYJNA OSOBY")
        
        conn = sqlite3.connect(self.db_name)
        img_data = conn.execute("SELECT foto FROM zdjecia WHERE osoba_id=? AND czy_profilowe=1", (dane[0],)).fetchone()
        conn.close()
        if img_data:
            try:
                img = Image.open(io.BytesIO(img_data[0])); tmp = "temp_p.jpg"; img.convert("RGB").save(tmp, "JPEG")
                c.drawImage(tmp, w - 200, h - 250, width=150, height=180); os.remove(tmp)
            except: pass
        c.save(); messagebox.showinfo("PDF", "Raport zapisany.")

    def usun_osobe(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("!", "Usunąć osobę?"):
            conn = sqlite3.connect(self.db_name); conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM osoby WHERE id=?", (self.tree.item(sel[0])['values'][0],))
            conn.commit(); conn.close(); self.odswiez_liste()

    def eksportuj_baze(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: import shutil; shutil.copy2(self.db_name, p)

    def importuj_baze(self):
        p = filedialog.askopenfilename(filetypes=[("Baza", "*.db")])
        if p and messagebox.askyesno("Import", "Zastąpić bazę?"):
            import shutil; shutil.copy2(p, self.db_name); self.odswiez_liste()

if __name__ == "__main__":
    root = tk.Tk(); app = OrganizatorKryminalny(root); root.mainloop()
