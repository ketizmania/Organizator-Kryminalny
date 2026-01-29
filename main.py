import flet as ft
import sqlite3
import os
import sys

# --- POPRAWKA DLA PYINSTALLERA (WINDOWS) ---
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# --- BEZPIECZNA ŚCIEŻKA DO BAZY (ANDROID / WINDOWS) ---
def get_db_path():
    try:
        if "ANDROID_DATA" in os.environ:
            # Prywatny folder aplikacji na Androidzie
            storage = os.environ.get("HOME", ".")
            return os.path.join(storage, "kryminalne.db")
        else:
            # Lokalny folder na Windows
            return "kryminalne.db"
    except:
        return "kryminalne.db"

# --- INICJALIZACJA BAZY DANYCH ---
def init_db(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS osoby 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, imie TEXT, nazwisko TEXT, 
                  klub TEXT, adres TEXT, foto_path TEXT, info TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pojazdy 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, osoba_id INTEGER, model TEXT, rej TEXT)''')
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "Organizator Spraw Kryminalnych"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"

    # Funkcja kopiowania błędu
    def copy_error(e_text):
        page.set_clipboard(e_text)
        page.snack_bar = ft.SnackBar(ft.Text("Skopiowano błąd do schowka!"))
        page.snack_bar.open = True
        page.update()

    try:
        db_path = get_db_path()
        conn = init_db(db_path)

        state = {"id": None, "foto": None}

        # --- ELEMENTY UI ---
        txt_imie = ft.TextField(label="Imię")
        txt_nazwisko = ft.TextField(label="Nazwisko")
        txt_klub = ft.TextField(label="Klub/Organizacja")
        txt_adres = ft.TextField(label="Adres")
        txt_info = ft.TextField(label="Notatki", multiline=True)
        img_profile = ft.Image(src="https://via.placeholder.com/150", width=100, height=100)
        
        lista_osob = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        lista_aut = ft.Column(spacing=5)

        # Obsługa wyboru zdjęcia
        def handle_file_result(e):
            if e.files:
                state["foto"] = e.files[0].path
                img_profile.src = state["foto"]
                page.update()

        file_picker = ft.FilePicker()
        file_picker.on_result = handle_file_result
        page.overlay.append(file_picker)

        def odswiez_liste(e=None):
            lista_osob.controls.clear()
            c = conn.cursor()
            val = search_bar.value if search_bar.value else ""
            search = f"%{val}%"
            c.execute("SELECT id, imie, nazwisko, klub FROM osoby WHERE nazwisko LIKE ? OR imie LIKE ? ORDER BY nazwisko ASC", (search, search))
            for row in c.fetchall():
                lista_osob.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"{row[2]} {row[1]}", weight="bold"),
                        subtitle=ft.Text(f"{row[3]}"),
                        on_click=lambda _, idx=row[0]: pokaz_szczegoly(idx)
                    )
                )
            page.update()

        def pokaz_szczegoly(id_osoby):
            state["id"] = id_osoby
            c = conn.cursor()
            c.execute("SELECT * FROM osoby WHERE id=?", (id_osoby,))
            r = c.fetchone()
            if r:
                txt_imie.value, txt_nazwisko.value = r[1], r[2]
                txt_klub.value, txt_adres.value = r[3], r[4]
                state["foto"] = r[5]
                txt_info.value = r[6]
                img_profile.src = state["foto"] if state["foto"] else "https://via.placeholder.com/150"
                
                lista_aut.controls.clear()
                c.execute("SELECT model, rej FROM pojazdy WHERE osoba_id=?", (id_osoby,))
                for v in c.fetchall():
                    lista_aut.controls.append(ft.Text(f"• {v[0]} [{v[1]}]"))
                page.update()

        def zapisz_osobe(e):
            c = conn.cursor()
            d = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_adres.value, state["foto"], txt_info.value)
            if state["id"] is None:
                c.execute("INSERT INTO osoby (imie, nazwisko, klub, adres, foto_path, info) VALUES (?,?,?,?,?,?)", d)
            else:
                c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, adres=?, foto_path=?, info=? WHERE id=?", d + (state["id"],))
            conn.commit()
            page.snack_bar = ft.SnackBar(ft.Text("Dane zapisane!"))
            page.snack_bar.open = True
            odswiez_liste()

        def dodaj_pojazd(e):
            if state["id"] is None:
                page.snack_bar = ft.SnackBar(ft.Text("Wybierz osobę z listy!"))
                page.snack_bar.open = True
                page.update()
                return

            def save_car(ev):
                c = conn.cursor()
                c.execute("INSERT INTO pojazdy (osoba_id, model, rej) VALUES (?,?,?)", (state["id"], m_i.value, r_i.value))
                conn.commit()
                dlg.open = False
                pokaz_szczegoly(state["id"])
                page.update()

            m_i, r_i = ft.TextField(label="Model"), ft.TextField(label="Rejestracja")
            dlg = ft.AlertDialog(
                title=ft.Text("Dodaj pojazd"),
                content=ft.Column([m_i, r_i], tight=True),
                actions=[ft.TextButton("Dodaj", on_click=save_car)]
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        search_bar = ft.TextField(label="Szukaj po nazwisku...", on_change=odswiez_liste)

        # --- BUDOWA LAYOUTU ---
        page.add(
            ft.Text("Organizator Spraw Kryminalnych", size=22, weight="bold"),
            search_bar,
            ft.Container(content=lista_osob, height=180, border=ft.border.all(1, ft.colors.GREY_700), border_radius=10),
            ft.Divider(),
            ft.Row([
                img_profile, 
                ft.ElevatedButton("ZDJĘCIE", icon=ft.icons.CAMERA_ALT, on_click=lambda _: file_picker.pick_files())
            ]),
            txt_imie, 
            txt_nazwisko, 
            txt_klub, 
            txt_adres, 
            txt_info,
            ft.Row([
                ft.Text("POJAZDY", weight="bold"), 
                ft.IconButton(ft.icons.ADD_CIRCLE, on_click=dodaj_pojazd)
            ]),
            lista_aut,
            ft.Container(height=10),
            ft.ElevatedButton("ZAPISZ DANE OSOBY", icon=ft.icons.SAVE, on_click=zapisz_osobe, width=float("inf")),
            ft.Container(height=20)
        )
        odswiez_liste()

    except Exception as ex:
        err_msg = str(ex)
        page.add(
            ft.Column([
                ft.Text("WYSTĄPIŁ BŁĄD SYSTEMOWY:", color="red", weight="bold"),
                ft.Text(err_msg, color="red", selectable=True),
                ft.ElevatedButton("KOPIUJ BŁĄD", icon=ft.icons.COPY, on_click=lambda _: copy_error(err_msg))
            ])
        )

ft.app(target=main)
        
