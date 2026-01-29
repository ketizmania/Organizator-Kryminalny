import flet as ft
import sqlite3
import os
import sys

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
    c.execute('CREATE TABLE IF NOT EXISTS osoby (id INTEGER PRIMARY KEY AUTOINCREMENT, imie TEXT, nazwisko TEXT, klub TEXT, adres TEXT, info TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS pojazdy (id INTEGER PRIMARY KEY AUTOINCREMENT, osoba_id INTEGER, model TEXT, rej TEXT)')
    conn.commit()
    return conn

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    
    db_path = get_db_path()
    conn = init_db(db_path)
    state = {"id": None}

    txt_imie = ft.TextField(label="Imię")
    txt_nazwisko = ft.TextField(label="Nazwisko")
    txt_klub = ft.TextField(label="Klub")
    txt_info = ft.TextField(label="Notatki", multiline=True)
    lista_osob = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    lista_aut = ft.Column()

    def odswiez_liste(e=None):
        lista_osob.controls.clear()
        c = conn.cursor()
        val = f"%{search_bar.value}%" if search_bar.value else "%"
        c.execute("SELECT id, imie, nazwisko FROM osoby WHERE nazwisko LIKE ?", (val,))
        for row in c.fetchall():
            lista_osob.controls.append(ft.ListTile(title=ft.Text(f"{row[2]} {row[1]}"), on_click=lambda _, idx=row[0]: pokaz_szczegoly(idx)))
        page.update()

    def pokaz_szczegoly(id_osoby):
        state["id"] = id_osoby
        c = conn.cursor()
        c.execute("SELECT * FROM osoby WHERE id=?", (id_osoby,))
        r = c.fetchone()
        if r:
            txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_info.value = r[1], r[2], r[3], r[5]
            lista_aut.controls.clear()
            c.execute("SELECT model, rej FROM pojazdy WHERE osoba_id=?", (id_osoby,))
            for v in c.fetchall():
                lista_aut.controls.append(ft.Text(f"• {v[0]} [{v[1]}]"))
            page.update()

    def zapisz_osobe(e):
        c = conn.cursor()
        d = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_info.value)
        if state["id"] is None:
            c.execute("INSERT INTO osoby (imie, nazwisko, klub, info) VALUES (?,?,?,?)", d)
        else:
            c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, info=? WHERE id=?", d + (state["id"],))
        conn.commit()
        odswiez_liste()

    search_bar = ft.TextField(label="Szukaj nazwiska...", on_change=odswiez_liste)

    page.add(
        ft.Text("OSK - Baza Danych", size=25, weight="bold"),
        search_bar,
        ft.Container(content=lista_osob, height=200, border=ft.border.all(1, "white")),
        txt_imie, txt_nazwisko, txt_klub, txt_info,
        ft.ElevatedButton("ZAPISZ OSOBĘ", on_click=zapisz_osobe),
        ft.Text("Pojazdy:", weight="bold"),
        lista_aut
    )
    odswiez_liste()

ft.app(target=main)
