import flet as ft
import sqlite3
import os
import sys

# --- LOGIKA ŚCIEŻEK ---
def get_db_path():
    try:
        if "ANDROID_DATA" in os.environ:
            return os.path.join(os.environ.get("HOME", "."), "kryminalne.db")
        return "kryminalne.db"
    except:
        return "kryminalne.db"

# --- INICJALIZACJA BAZY ---
def init_db():
    path = get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS osoby 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  imie TEXT, nazwisko TEXT, klub TEXT, 
                  adres TEXT, info TEXT, pojazdy TEXT)''')
    try:
        c.execute("ALTER TABLE osoby ADD COLUMN pojazdy TEXT")
    except:
        pass
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "OSK v2.8"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 15
    page.scroll = "adaptive"

    def copy_error_to_clipboard(err_text):
        page.set_clipboard(err_text)
        page.snack_bar = ft.SnackBar(ft.Text("Skopiowano błąd do schowka!"))
        page.snack_bar.open = True
        page.update()

    try:
        conn = init_db()
        state = {"id": None}

        # --- POLA TEKSTOWE ---
        txt_imie = ft.TextField(label="Imię", border_color=ft.colors.BLUE_700)
        txt_nazwisko = ft.TextField(label="Nazwisko", border_color=ft.colors.BLUE_700)
        txt_klub = ft.TextField(label="Klub / Powiązania", prefix_icon=ft.icons.GROUP)
        txt_pojazdy = ft.TextField(label="Pojazdy", multiline=True, prefix_icon=ft.icons.DIRECTIONS_CAR)
        txt_info = ft.TextField(label="Notatki", multiline=True, min_lines=3)
        
        lista_wynikow = ft.Column(spacing=10)

        def odswiez_liste(e=None):
            lista_wynikow.controls.clear()
            c = conn.cursor()
            val = f"%{search_bar.value}%" if search_bar.value else "%"
            c.execute("SELECT id, imie, nazwisko, klub FROM osoby WHERE nazwisko LIKE ? OR imie LIKE ? LIMIT 20", (val, val))
            
            for row in c.fetchall():
                lista_wynikow.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            title=ft.Text(f"{row[2]} {row[1]}", weight="bold"),
                            subtitle=ft.Text(f"Klub: {row[3]}"),
                            trailing=ft.Icon(ft.icons.EDIT, size=20),
                            on_click=lambda _, idx=row[0]: wczytaj_osobe(idx)
                        ),
                        bgcolor=ft.colors.GREY_900,
                        border_radius=8,
                        border=ft.border.all(1, ft.colors.GREY_800)
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
                page.snack_bar = ft.SnackBar(ft.Text("Wczytano dane"))
                page.snack_bar.open = True
                page.update()

        def zapisz(e):
            if not txt_nazwisko.value:
                page.snack_bar = ft.SnackBar(ft.Text("Błąd: Nazwisko jest wymagane!"))
                page.snack_bar.open = True
                page.update()
                return
            
            c = conn.cursor()
            d = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_info.value, txt_pojazdy.value)
            if state["id"] is None:
                c.execute("INSERT INTO osoby (imie, nazwisko, klub, info, pojazdy) VALUES (?,?,?,?,?)", d)
            else:
                c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, info=?, pojazdy=? WHERE id=?", d + (state["id"],))
            conn.commit()
            odswiez_liste()
            page.snack_bar = ft.SnackBar(ft.Text("Zapisano pomyślnie"))
            page.snack_bar.open = True
            page.update()

        def usun(e):
            if state["id"]:
                c = conn.cursor()
                c.execute("DELETE FROM osoby WHERE id=?", (state["id"],))
                conn.commit()
                state["id"] = None
                txt_imie.value = txt_nazwisko.value = txt_klub.value = txt_pojazdy.value = txt_info.value = ""
                odswiez_liste()
                page.update()

        search_bar = ft.TextField(
            label="Wyszukiwarka...", 
            prefix_icon=ft.icons.SEARCH,
            on_change=odswiez_liste
        )

        page.add(
            ft.Text("OSK SYSTEM 2.8", size=24, weight="bold", color=ft.colors.BLUE_400),
            ft.Divider(),
            search_bar,
            lista_wynikow,
            ft.Divider(height=40),
            txt_imie,
            txt_nazwisko,
            txt_klub,
            txt_pojazdy,
            txt_info,
            ft.Row([
                ft.ElevatedButton("ZAPISZ", icon=ft.icons.SAVE, on_click=zapisz, expand=True),
                ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_400, on_click=usun)
            ]),
            ft.ElevatedButton("NOWY WPIS", on_click=lambda _: [setattr(txt_imie, 'value', ''), setattr(txt_nazwisko, 'value', ''), setattr(state, 'id', None), page.update()]),
            ft.Container(height=50)
        )
        odswiez_liste()

    except Exception as ex:
        err_msg = str(ex)
        page.clean()
        page.add(
            ft.Container(
                padding=20,
                bgcolor=ft.colors.RED_900,
                border_radius=10,
                content=ft.Column([
                    ft.Text("BŁĄD KRYTYCZNY", weight="bold", size=20, color=ft.colors.WHITE),
                    ft.Text(err_msg, color=ft.colors.WHITE),
                    ft.ElevatedButton(
                        "KOPIUJ TREŚĆ BŁĘDU", 
                        icon=ft.icons.COPY, 
                        on_click=lambda _: copy_error_to_clipboard(err_msg)
                    )
                ])
            )
        )
        page.update()

ft.app(target=main)
            
