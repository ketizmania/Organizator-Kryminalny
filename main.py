import flet as ft
import sqlite3
import os
import sys

# Poprawka dla PyInstallera
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

def get_db_path():
    if "ANDROID_DATA" in os.environ:
        storage = os.environ.get("HOME", ".")
        return os.path.join(storage, "kryminalne.db")
    return "kryminalne.db"

def init_db(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS osoby (id INTEGER PRIMARY KEY AUTOINCREMENT, imie TEXT, nazwisko TEXT, klub TEXT, adres TEXT, info TEXT, pojazdy TEXT)')
    # Migracja kolumny pojazdy
    try:
        c.execute("ALTER TABLE osoby ADD COLUMN pojazdy TEXT")
    except:
        pass
    conn.commit()
    return conn

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "auto"  # Zmienione na standardowe przewijanie
    
    db_path = get_db_path()
    conn = init_db(db_path)
    state = {"id": None}

    # --- ELEMENTY FORMULARZA ---
    txt_imie = ft.TextField(label="Imię")
    txt_nazwisko = ft.TextField(label="Nazwisko")
    txt_klub = ft.TextField(label="Klub")
    txt_pojazdy = ft.TextField(label="Pojazdy", multiline=True)
    txt_info = ft.TextField(label="Notatki", multiline=True)
    
    lista_osob = ft.Column() # Prosta kolumna zamiast ListView (bezpieczniejsza)

    def odswiez_liste(e=None):
        lista_osob.controls.clear()
        c = conn.cursor()
        val = f"%{search_bar.value}%" if search_bar.value else "%"
        # Wyszukiwanie po Imieniu LUB Nazwisku
        c.execute("SELECT id, imie, nazwisko FROM osoby WHERE nazwisko LIKE ? OR imie LIKE ?", (val, val))
        for row in c.fetchall():
            lista_osob.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{row[2]} {row[1]}"), 
                    on_click=lambda _, idx=row[0]: wczytaj_osobe(idx)
                )
            )
        page.update()

    def wczytaj_osobe(idx):
        state["id"] = idx
        c = conn.cursor()
        c.execute("SELECT * FROM osoby WHERE id=?", (idx,))
        r = c.fetchone()
        if r:
            txt_imie.value, txt_nazwisko.value, txt_klub.value = r[1], r[2], r[3]
            txt_info.value = r[5]
            txt_pojazdy.value = r[6] if len(r) > 6 else ""
            page.update()

    def zapisz(e):
        if not txt_nazwisko.value: return
        c = conn.cursor()
        d = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_info.value, txt_pojazdy.value)
        if state["id"] is None:
            c.execute("INSERT INTO osoby (imie, nazwisko, klub, info, pojazdy) VALUES (?,?,?,?,?)", d)
        else:
            c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, info=?, pojazdy=? WHERE id=?", d + (state["id"],))
        conn.commit()
        odswiez_liste()

    def usun(e):
        if state["id"]:
            c = conn.cursor()
            c.execute("DELETE FROM osoby WHERE id=?", (state["id"],))
            conn.commit()
            state["id"] = None
            txt_imie.value = txt_nazwisko.value = txt_klub.value = txt_pojazdy.value = txt_info.value = ""
            odswiez_liste()

    search_bar = ft.TextField(label="Szukaj (Imię/Nazwisko)", on_change=odswiez_liste)

    # --- UKŁAD STRONY (BARDZO PROSTY) ---
    page.add(
        ft.Text("Baza Danych OSK", size=20, weight="bold"),
        search_bar,
        ft.Text("WYNIKI:"),
        lista_osob,
        ft.Divider(),
        ft.Text("EDYCJA:"),
        txt_imie, 
        txt_nazwisko, 
        txt_klub, 
        txt_pojazdy, 
        txt_info,
        ft.Row([
            ft.ElevatedButton("ZAPISZ", on_click=zapisz),
            ft.IconButton(ft.icons.DELETE, icon_color="red", on_click=usun)
        ]),
        ft.ElevatedButton("NOWY / WYCZYŚĆ", on_click=lambda _: [setattr(txt_imie, 'value', ''), setattr(txt_nazwisko, 'value', ''), setattr(state, 'id', None), page.update()])
    )
    odswiez_liste()

ft.app(target=main)
