import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import io
import os
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

class OrganizatorKryminalny:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizator Kryminalny v2.5.1")
        self.root.geometry("1100x700")
        self.root.configure(bg="#1e272e")
        
        self.db_name = "baza_danych.db"
        self.init_db()
        
        self.icon_cache = []
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", rowheight=60, background="#2f3542", foreground="white", fieldbackground="#2f3542")
        self.style.map("Treeview", background=[('selected', '#3742fa')])
        
        # --- UI Header ---
        header = tk.Frame(self.root, bg="#2f3640", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        tk.Label(header, text="🚔 SYSTEM KARTOTEKI OPERACYJNEJ", bg="#2f3640", fg="#dcdde1", font=("Arial", 14, "bold")).pack(pady=15)

        # Panel wyszukiwania
        search_frame = tk.Frame(self.root, bg="#1e272e")
        search_frame.pack(fill=tk.X, side=tk.TOP, padx=20, pady=10)
        self.search_entry = tk.Entry(search_frame, bg="#353b48", fg="white", font=("Arial", 12))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.odswiez_liste())

        # --- STOPKA ---
        footer = tk.Frame(self.root, bg="#2f3640", pady=10)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        btn_c = {"font": ("Arial", 9, "bold"), "fg": "white", "padx": 10}
        tk.Button(footer, text="➕ DODAJ", bg="#44bd32", command=self.okno_dodawania, **btn_c).pack(side=tk.LEFT, padx=10)
        tk.Button(footer, text="🗑️ USUŃ", bg="#c23616", command=self.usun_osobe, **btn_c).pack(side=tk.LEFT)
        tk.Button(footer, text="📂 IMPORT", bg="#718093", command=self.importuj_baze, **btn_c).pack(side=tk.RIGHT, padx=10)
        tk.Button(footer, text="📤 EKSPORT", bg="#273c75", command=self.eksportuj_baze, **btn_c).pack(side=tk.RIGHT)

        # --- LISTA ---
        self.tree = ttk.Treeview(self.root, columns=("ID", "Osoba", "Sprawa", "Klub"), show='tree headings')
        self.tree.heading("#0", text="Foto")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Osoba", text="Osoba")
        self.tree.heading("Sprawa", text="Numer Sprawy")
        self.tree.heading("Klub", text="Klub")
        self.tree.column("#0", width=80, anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.pokaz_detale())

        self.odswiez_liste()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute('''CREATE TABLE IF NOT EXISTS osoby
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, imie TEXT, nazwisko TEXT, 
                      klub TEXT, pojazdy TEXT, adresy TEXT, nr_sprawy TEXT, 
                      telefon TEXT, notatka TEXT, foto BLOB)''')
        conn.commit()
        conn.close()

    def center_window(self, window, width, height):
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def odswiez_liste(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        self.icon_cache = [] 
        f = f"%{self.search_entry.get()}%"
        conn = sqlite3.connect(self.db_name)
        cursor = conn.execute("SELECT id, imie, nazwisko, nr_sprawy, klub, foto FROM osoby WHERE imie LIKE ? OR nazwisko LIKE ? OR nr_sprawy LIKE ? OR pojazdy LIKE ? OR adresy LIKE ? OR telefon LIKE ?", (f,f,f,f,f,f))
        for r in cursor:
            img_tk = None
            if r[5]:
                try:
                    img = Image.open(io.BytesIO(r[5]))
                    img.thumbnail((55, 55))
                    img_tk = ImageTk.PhotoImage(img)
                    self.icon_cache.append(img_tk)
                except: pass
            self.tree.insert("", tk.END, image=img_tk if img_tk else "", values=(r[0], f"{r[1]} {r[2]}", r[3], r[4]))
        conn.close()

    def okno_dodawania(self, edycja_id=None, dane_startowe=None):
        okno = tk.Toplevel(self.root)
        okno.configure(bg="#2f3542")
        okno.grab_set()
        
        width = 600
        okno.withdraw()

        rows_vehicles = []
        rows_phones = []

        def auto_resize():
            okno.update_idletasks()
            self.center_window(okno, width, okno.winfo_reqheight())

        def add_v_row(brand="", plate=""):
            row_f = tk.Frame(vehicle_frame, bg="#353b48")
            row_f.pack(fill=tk.X, pady=2)
            
            e_brand = tk.Entry(row_f, width=30)
            e_brand.insert(0, brand)
            e_brand.pack(side=tk.LEFT, padx=2)
            tk.Label(row_f, text="rej:", bg="#353b48", fg="white", font=("Arial", 8)).pack(side=tk.LEFT)
            e_plate = tk.Entry(row_f, width=15)
            e_plate.insert(0, plate)
            e_plate.pack(side=tk.LEFT, padx=2)
            
            tk.Button(row_f, text="X", bg="#c23616", fg="white", font=("Arial", 7, "bold"), 
                      command=lambda: [row_f.destroy(), rows_vehicles.remove((e_brand, e_plate)), auto_resize()]).pack(side=tk.LEFT, padx=2)
            
            rows_vehicles.append((e_brand, e_plate))
            auto_resize()

        def add_p_row(val=""):
            row_f = tk.Frame(phone_frame, bg="#353b48")
            row_f.pack(fill=tk.X, pady=2)
            
            e_p = tk.Entry(row_f, width=48)
            e_p.insert(0, val)
            e_p.pack(side=tk.LEFT, padx=2)
            
            tk.Button(row_f, text="X", bg="#c23616", fg="white", font=("Arial", 7, "bold"), 
                      command=lambda: [row_f.destroy(), rows_phones.remove(e_p), auto_resize()]).pack(side=tk.LEFT, padx=2)
            
            rows_phones.append(e_p)
            auto_resize()

        labels_top = ["Imię", "Nazwisko", "Klub"]
        labels_mid = ["Adresy", "Nr sprawy"]
        entries = {}
        current_row = 0

        # Sekcja górna
        for p in labels_top:
            tk.Label(okno, text=p, bg="#2f3542", fg="white").grid(row=current_row, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(okno, width=50)
            e.grid(row=current_row, column=1, columnspan=2)
            if dane_startowe:
                idx = ["Imię", "Nazwisko", "Klub"].index(p) + 1
                e.insert(0, str(dane_startowe[idx]) if dane_startowe[idx] else "")
            entries[p] = e
            current_row += 1

        # Sekcja POJAZDY
        left_v_frame = tk.Frame(okno, bg="#2f3542")
        left_v_frame.grid(row=current_row, column=0, sticky="nw", padx=10, pady=5)
        tk.Label(left_v_frame, text="POJAZDY", bg="#2f3542", fg="#f1c40f", font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Button(left_v_frame, text="➕ DODAJ", bg="#2980b9", fg="white", font=("Arial", 7, "bold"), 
                  command=add_v_row, width=10).pack(anchor="w", pady=(5, 0))

        vehicle_frame = tk.Frame(okno, bg="#353b48", padx=5, pady=5)
        vehicle_frame.grid(row=current_row, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        current_row += 1

        # Sekcja środkowa
        for p in labels_mid:
            tk.Label(okno, text=p, bg="#2f3542", fg="white").grid(row=current_row, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(okno, width=50)
            e.grid(row=current_row, column=1, columnspan=2)
            if dane_startowe:
                idx = 5 if p == "Adresy" else 6
                e.insert(0, str(dane_startowe[idx]) if dane_startowe[idx] else "")
            entries[p] = e
            current_row += 1

        # Sekcja TELEFONY
        left_p_frame = tk.Frame(okno, bg="#2f3542")
        left_p_frame.grid(row=current_row, column=0, sticky="nw", padx=10, pady=5)
        tk.Label(left_p_frame, text="TELEFONY", bg="#2f3542", fg="#f1c40f", font=("Arial", 9, "bold")).pack(anchor="w")
        tk.Button(left_p_frame, text="➕ DODAJ", bg="#2980b9", fg="white", font=("Arial", 7, "bold"), 
                  command=add_p_row, width=10).pack(anchor="w", pady=(5, 0))

        phone_frame = tk.Frame(okno, bg="#353b48", padx=5, pady=5)
        phone_frame.grid(row=current_row, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        current_row += 1

        # Notatka
        tk.Label(okno, text="Notatka", bg="#2f3542", fg="white").grid(row=current_row, column=0, sticky="w", padx=10)
        notatka = tk.Text(okno, width=38, height=4)
        notatka.grid(row=current_row, column=1, columnspan=2, pady=5, sticky="w", padx=10)
        if dane_startowe: notatka.insert("1.0", str(dane_startowe[8]) if dane_startowe[8] else "")
        current_row += 1

        # Foto
        self.temp_foto = dane_startowe[9] if dane_startowe else None
        lbl_mini = tk.Label(okno, bg="#2f3542")
        lbl_mini.grid(row=current_row, column=1, pady=5, sticky="w", padx=10)
        
        def set_mini():
            if self.temp_foto:
                try:
                    img = Image.open(io.BytesIO(self.temp_foto))
                    img.thumbnail((100,100))
                    ph = ImageTk.PhotoImage(img)
                    lbl_mini.config(image=ph); lbl_mini.image = ph
                except: lbl_mini.config(image='', width=0, height=0)
            else:
                lbl_mini.config(image='', width=0, height=0); lbl_mini.image = None
            auto_resize()

        def wybierz_f():
            p = filedialog.askopenfilename(filetypes=[("Obrazy", "*.jpg *.png *.jpeg")])
            if p: 
                with open(p, "rb") as f: self.temp_foto = f.read()
                set_mini()

        foto_btns = tk.Frame(okno, bg="#2f3542")
        foto_btns.grid(row=current_row, column=0, padx=10, sticky="nw", pady=5)
        tk.Button(foto_btns, text="📸 FOTO", command=wybierz_f, width=10).pack(pady=2, anchor="w")
        tk.Button(foto_btns, text="🗑️ USUŃ", command=lambda: [setattr(self, 'temp_foto', None), set_mini()], 
                  bg="#c23616", fg="white", font=("Arial", 7, "bold"), width=10).pack(pady=2, anchor="w")

        # Wczytywanie startowych dynamik
        if dane_startowe:
            if dane_startowe[4]:
                for v in dane_startowe[4].split(" | "):
                    if " [" in v: 
                        parts = v.replace("]", "").split(" [")
                        add_v_row(parts[0], parts[1])
            if dane_startowe[7]:
                for t in str(dane_startowe[7]).split(", "): add_p_row(t)
        else:
            add_v_row(); add_p_row()

        def zapisz():
            v_str = " | ".join([f"{b.get().strip()} [{p.get().strip()}]" for b, p in rows_vehicles if b.get() or p.get()])
            p_str = ", ".join([e.get().strip() for e in rows_phones if e.get().strip()])
            
            data = [entries["Imię"].get(), entries["Nazwisko"].get(), entries["Klub"].get(), 
                    v_str, entries["Adresy"].get(), entries["Nr sprawy"].get(), 
                    p_str, notatka.get("1.0", tk.END).strip(), self.temp_foto]
            
            conn = sqlite3.connect(self.db_name)
            if edycja_id:
                conn.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, pojazdy=?, adresy=?, nr_sprawy=?, telefon=?, notatka=?, foto=? WHERE id=?", (*data, edycja_id))
            else:
                conn.execute("INSERT INTO osoby (imie, nazwisko, klub, pojazdy, adresy, nr_sprawy, telefon, notatka, foto) VALUES (?,?,?,?,?,?,?,?,?)", data)
            conn.commit(); conn.close()
            okno.destroy(); self.odswiez_liste()

        tk.Button(okno, text="ZAPISZ DANE", command=zapisz, bg="#44bd32", fg="white", font=("Arial", 10, "bold"), width=30).grid(row=current_row+1, columnspan=3, pady=20)
        
        set_mini()
        okno.deiconify()

    def pokaz_detale(self):
        sel = self.tree.selection()
        if not sel: return
        id_os = self.tree.item(sel[0])['values'][0]
        
        conn = sqlite3.connect(self.db_name)
        res = conn.execute("SELECT * FROM osoby WHERE id=?", (id_os,)).fetchone()
        conn.close()
        
        if res:
            d = tk.Toplevel(self.root)
            d.title(f"Detale: {res[1]} {res[2]}")
            d.configure(bg="#1e272e")
            self.center_window(d, 550, 750)
            
            canvas_area = tk.Canvas(d, bg="#1e272e", highlightthickness=0)
            scrollbar = ttk.Scrollbar(d, orient="vertical", command=canvas_area.yview)
            scroll_frame = tk.Frame(canvas_area, bg="#1e272e")

            scroll_frame.bind("<Configure>", lambda e: canvas_area.configure(scrollregion=canvas_area.bbox("all")))
            canvas_area.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas_area.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side="right", fill="y")
            canvas_area.pack(side="left", fill="both", expand=True)

            if res[9]:
                try:
                    img = Image.open(io.BytesIO(res[9]))
                    img.thumbnail((300, 300))
                    ph = ImageTk.PhotoImage(img)
                    lbl_img = tk.Label(scroll_frame, image=ph, bg="#1e272e")
                    lbl_img.image = ph
                    lbl_img.pack(pady=15)
                except: pass

            header_font = ("Arial", 12, "bold")
            data_font = ("Arial", 10)
            
            def add_section(title, content, color="#f1c40f"):
                if content and content.strip():
                    tk.Label(scroll_frame, text=title, bg="#1e272e", fg=color, font=header_font).pack(anchor="w", padx=30, pady=(10, 2))
                    tk.Label(scroll_frame, text=content, bg="#1e272e", fg="white", font=data_font, justify=tk.LEFT).pack(anchor="w", padx=45)

            add_section("👤 OSOBA:", f"{res[1]} {res[2]}")
            add_section("🏘️ KLUB:", res[3], color="#e74c3c")
            add_section("📁 NUMER SPRAWY:", res[6])
            add_section("📍 ADRESY:", res[5])

            if res[4]:
                tk.Label(scroll_frame, text="🚗 POJAZDY:", bg="#1e272e", fg="#3498db", font=header_font).pack(anchor="w", padx=30, pady=(10, 2))
                for v in res[4].split(" | "):
                    tk.Label(scroll_frame, text=f"• {v}", bg="#1e272e", fg="white", font=data_font).pack(anchor="w", padx=45)

            if res[7]:
                tk.Label(scroll_frame, text="📞 TELEFONY:", bg="#1e272e", fg="#2ecc71", font=header_font).pack(anchor="w", padx=30, pady=(10, 2))
                for t in res[7].split(", "):
                    tk.Label(scroll_frame, text=f"• {t}", bg="#1e272e", fg="white", font=data_font).pack(anchor="w", padx=45)

            add_section("📝 NOTATKA:", res[8])

            btn_frame = tk.Frame(scroll_frame, bg="#1e272e")
            btn_frame.pack(pady=30)
            tk.Button(btn_frame, text="✏️ EDYTUJ", width=15, bg="#f39c12", fg="white", font=("Arial", 9, "bold"),
                      command=lambda: [d.destroy(), self.okno_dodawania(id_os, res)]).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="📄 PDF", width=15, bg="#2980b9", fg="white", font=("Arial", 9, "bold"),
                      command=lambda: self.generuj_pdf(res)).pack(side=tk.LEFT, padx=10)

    def generuj_pdf(self, dane):
        fname = f"Kartoteka_{dane[1]}_{dane[2]}".replace(" ", "_")
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{fname}.pdf")
        if not path: return

        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, height - 50, "KARTA OPERACYJNA OSOBY")
        c.setLineWidth(1)
        c.line(50, height - 60, width - 50, height - 60)

        if dane[9]:
            try:
                img_data = io.BytesIO(dane[9])
                img = Image.open(img_data)
                tmp_path = "temp_print_img.jpg"
                img.convert("RGB").save(tmp_path, "JPEG")
                c.drawImage(tmp_path, width - 200, height - 250, width=150, height=180)
                os.remove(tmp_path)
            except Exception as e:
                print(f"Błąd PDF Foto: {e}")

        y = height - 100
        sections = [
            ("IMIE I NAZWISKO:", f"{dane[1]} {dane[2]}"),
            ("KLUB:", dane[3]),
            ("NUMER SPRAWY:", dane[6]),
            ("ADRESY:", dane[5])
        ]

        for label, text in sections:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, label)
            c.setFont("Helvetica", 11)
            c.drawString(180, y, str(text) if text else "---")
            y -= 25

        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "ZAREJESTROWANE POJAZDY:")
        y -= 20
        c.setFont("Helvetica", 11)
        if dane[4]:
            for v in dane[4].split(" | "):
                c.drawString(70, y, f"- {v}")
                y -= 18
        else:
            c.drawString(70, y, "Brak danych o pojazdach")
            y -= 18

        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "NUMERY TELEFONU:")
        y -= 20
        c.setFont("Helvetica", 11)
        if dane[7]:
            for t in str(dane[7]).split(", "):
                c.drawString(70, y, f"- {t}")
                y -= 18
        else:
            c.drawString(70, y, "Brak danych o telefonach")
            y -= 18

        y -= 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "NOTATKI / OBSERWACJE:")
        y -= 20
        c.setFont("Helvetica", 10)
        
        notatka = dane[8] if dane[8] else "Brak dodatkowych notatek."
        lines = notatka.split('\n')
        for line in lines:
            c.drawString(50, y, line[:100])
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(50, 30, "Wygenerowano z systemu Organizator Kryminalny - scisle tajne.")
        
        c.save()
        messagebox.showinfo("PDF", f"Raport dla {dane[1]} {dane[2]} został zapisany.")

    def importuj_baze(self):
        p = filedialog.askopenfilename(filetypes=[("Baza", "*.db")])
        if not p: return
        ans = messagebox.askyesnocancel("Import", "TAK - Zastąp\nNIE - Uzupełnij\nAnuluj - Wyjdź")
        if ans is None: return
        if ans: 
            import shutil; shutil.copy2(p, self.db_name); self.odswiez_liste()
        else:
            c_new = sqlite3.connect(p); n_data = c_new.execute("SELECT * FROM osoby").fetchall(); c_new.close()
            c_old = sqlite3.connect(self.db_name)
            for r in n_data:
                ex = c_old.execute("SELECT 1 FROM osoby WHERE imie=? AND nazwisko=?", (r[1], r[2])).fetchone()
                if not ex: c_old.execute("INSERT INTO osoby (imie, nazwisko, klub, pojazdy, adresy, nr_sprawy, telefon, notatka, foto) VALUES (?,?,?,?,?,?,?,?,?)", r[1:])
            c_old.commit(); c_old.close(); self.odswiez_liste()

    def usun_osobe(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("!", "Usunąć zaznaczoną osobę?"):
            conn = sqlite3.connect(self.db_name)
            conn.execute("DELETE FROM osoby WHERE id=?", (self.tree.item(sel[0])['values'][0],))
            conn.commit(); conn.close(); self.odswiez_liste()

    def eksportuj_baze(self):
        p = filedialog.asksaveasfilename(defaultextension=".db")
        if p: import shutil; shutil.copy2(self.db_name, p)

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizatorKryminalny(root)
    root.mainloop()
