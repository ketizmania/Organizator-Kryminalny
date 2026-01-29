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
    c.execute('''CREATE TABLE IF NOT EXISTS osoby 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  imie TEXT, nazwisko TEXT, klub TEXT, 
                  adres TEXT, info TEXT, pojazdy TEXT)''')
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "OSK System v2.5"
    page.theme_mode = ft.ThemeMode.DARK
    page.dark_theme = ft.Theme(color_scheme_seed=ft.colors.BLUE_ACCENT)
    page.padding = 0  # Padding ustawimy wewnątrz kontenerów
    
    db_path = get_db_path()
    conn = init_db(db_path)
    state = {"id": None}

    # --- ELEMENTY UI ---
    txt_imie = ft.TextField(label="Imię", expand=True)
    txt_nazwisko = ft.TextField(label="Nazwisko", expand=True)
    txt_klub = ft.TextField(label="Powiązania / Klub", prefix_icon=ft.icons.GROUP_OUTLINED)
    txt_pojazdy = ft.TextField(label="Pojazdy", prefix_icon=ft.icons.DIRECTIONS_CAR_FILLED, multiline=True)
    txt_info = ft.TextField(label="Notatki operacyjne", multiline=True, min_lines=5)
    
    lista_osob = ft.ListView(expand=True, spacing=10, padding=20)

    def odswiez_liste(e=None):
        lista_osob.controls.clear()
        c = conn.cursor()
        val = f"%{search_bar.value}%" if search_bar.value else "%"
        c.execute("""SELECT id, imie, nazwisko, klub FROM osoby 
                     WHERE nazwisko LIKE ? OR imie LIKE ? OR klub LIKE ? 
                     ORDER BY nazwisko ASC""", (val, val, val))
        
        for row in c.fetchall():
            lista_osob.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.CircleAvatar(content=ft.Text(row[2][0] if row[2] else "?")),
                        title=ft.Text(f"{row[2]} {row[1]}", weight="bold"),
                        subtitle=ft.Text(f"Klub: {row[3] if row[3] else 'Brak'}"),
                        on_click=lambda _, idx=row[0]: wybierz_osobe(idx)
                    ),
                    bgcolor=ft.colors.GREY_900,
                    border_radius=10,
                    border=ft.border.all(1, ft.colors.GREY_800)
                )
            )
        page.update()

    def wybierz_osobe(id_osoby):
        state["id"] = id_osoby
        c = conn.cursor()
        c.execute("SELECT * FROM osoby WHERE id=?", (id_osoby,))
        r = c.fetchone()
        if r:
            txt_imie.value, txt_nazwisko.value = r[1], r[2]
            txt_klub.value, txt_info.value = r[3], r[5]
            txt_pojazdy.value = r[6] if len(r) > 6 else ""
            tabs.selected_index = 1 # Przełącz na zakładkę "Akta"
            page.update()

    def zapisz_osobe(e):
        if not txt_nazwisko.value:
            return
        c = conn.cursor()
        d = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_info.value, txt_pojazdy.value)
        if state["id"] is None:
            c.execute("INSERT INTO osoby (imie, nazwisko, klub, info, pojazdy) VALUES (?,?,?,?,?)", d)
        else:
            c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, info=?, pojazdy=? WHERE id=?", d + (state["id"],))
        conn.commit()
        odswiez_liste()
        tabs.selected_index = 0
        page.snack_bar = ft.SnackBar(ft.Text("Zapisano zmiany"))
        page.snack_bar.open = True
        page.update()

    def potwierdz_usun(e):
        if state["id"] is None: return
        
        def usun_na_pewno(ev):
            c = conn.cursor()
            c.execute("DELETE FROM osoby WHERE id=?", (state["id"],))
            conn.commit()
            dlg.open = False
            state["id"] = None
            odswiez_liste()
            tabs.selected_index = 0
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Potwierdź usunięcie"),
            content=ft.Text("Czy na pewno chcesz trwale usunąć te akta?"),
            actions=[
                ft.TextButton("Anuluj", on_click=lambda _: setattr(dlg, "open", False)),
                ft.ElevatedButton("USUŃ", bgcolor=ft.colors.RED_900, on_click=usun_na_pewno),
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def nowa_osoba(e):
        state["id"] = None
        txt_imie.value = txt_nazwisko.value = txt_klub.value = txt_info.value = txt_pojazdy.value = ""
        tabs.selected_index = 1
        page.update()

    # --- ELEMENTY WIDOKÓW ---
    search_bar = ft.TextField(
        label="Szukaj w rejestrze...", 
        on_change=odswiez_liste,
        prefix_icon=ft.icons.SEARCH,
        border_radius=20,
        margin=20
    )

    widok_szukaj = ft.Column([
        search_bar,
        lista_osob
    ])

    widok_edycji = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Row([txt_imie, txt_nazwisko], spacing=10),
            txt_klub,
            txt_pojazdy,
            txt_info,
            ft.Divider(height=20, color="transparent"),
            ft.Row([
                ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED_400, on_click=potwierdz_usun, icon_size=30),
                ft.ElevatedButton("ZAPISZ AKTUALIZACJĘ", icon=ft.icons.SAVE, on_click=zapisz_osobe, expand=True, height=50)
            ])
        ], scroll=ft.ScrollMode.AUTO)
    )

    # --- TABS CONTROL ---
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="BAZA", icon=ft.icons.STORAGE, content=widok_szukaj),
            ft.Tab(text="AKTA", icon=ft.icons.EDIT_DOCUMENT, content=widok_edycji),
        ],
        expand=True
    )

    page.add(
        ft.Container(
            padding=ft.padding.only(top=40, bottom=10),
            content=ft.Row([ft.Text("OSK SYSTEM 2.5", size=20, weight="bold", color=ft.colors.BLUE_ACCENT)], alignment=ft.MainAxisAlignment.CENTER)
        ),
        tabs
    )
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.ADD, on_click=nowa_osoba, bgcolor=ft.colors.BLUE_ACCENT_700
    )
    
    odswiez_liste()

ft.app(target=main)
