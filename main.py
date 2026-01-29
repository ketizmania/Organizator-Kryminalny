import flet as ft
import sqlite3
import os

# --- BEZPIECZNA ŚCIEŻKA DLA ANDROIDA ---
def get_db_path():
    try:
        if "ANDROID_DATA" in os.environ:
            storage = os.environ.get("HOME", ".")
            return os.path.join(storage, "kryminalne.db")
        else:
            return "kryminalne.db"
    except Exception:
        return "kryminalne.db"

def init_db(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS osoby 
                 (id INTEGER PRIMARY KEY, imie TEXT, nazwisko TEXT, 
                  klub TEXT, adres TEXT, foto_path TEXT, info TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pojazdy 
                 (id INTEGER PRIMARY KEY, osoba_id INTEGER, model TEXT, rej TEXT)''')
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "Organizator Spraw Kryminalnych"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive" 

    try:
        db_path = get_db_path()
        conn = init_db(db_path)

        selected_osoba_id = None
        selected_foto_path = None

        # --- KOMPONENTY UI ---
        txt_imie = ft.TextField(label="Imię", expand=True)
        txt_nazwisko = ft.TextField(label="Nazwisko", expand=True)
        txt_klub = ft.TextField(label="Klub/Organizacja", expand=True)
        txt_adres = ft.TextField(label="Adres", expand=True)
        txt_info = ft.TextField(label="Notatki", multiline=True, min_lines=2)
        
        # POPRAWKA: Usunięcie problematycznego ImageFit i uproszczenie Image
        img_profile = ft.Image(
            src="https://via.placeholder.com/150", 
            width=150, 
            height=150
        )
        
        lista_osob_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        lista_aut = ft.Column(spacing=5)

        def on_file_result(e: ft.FilePickerResultEvent):
            nonlocal selected_foto_path
            if e.files:
                selected_foto_path = e.files[0].path
                img_profile.src = selected_foto_path
                page.update()

        file_picker = ft.FilePicker(on_result=on_file_result)
        page.overlay.append(file_picker)

        def odswiez_liste(e=None):
            lista_osob_container.controls.clear()
            c = conn.cursor()
            search = f"%{search_bar.value if search_bar.value else ''}%"
            query = """
                SELECT DISTINCT o.id, o.imie, o.nazwisko, o.klub 
                FROM osoby o 
                LEFT JOIN pojazdy p ON o.id = p.osoba_id
                WHERE o.nazwisko LIKE ? OR p.rej LIKE ?
                ORDER BY o.nazwisko ASC
            """
            c.execute(query, (search, search))
            rows = c.fetchall()
            for row in rows:
                lista_osob_container.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.SHIELD_PERSON),
                        title=ft.Text(f"{row[2]} {row[1]}", weight="bold"),
                        subtitle=ft.Text(f"{row[3]}"),
                        on_click=lambda _, idx=row[0]: pokaz_szczegoly(idx)
                    )
                )
            page.update()

        def pokaz_szczegoly(id_osoby):
            nonlocal selected_osoba_id, selected_foto_path
            selected_osoba_id = id_osoby
            c = conn.cursor()
            c.execute("SELECT * FROM osoby WHERE id=?", (id_osoby,))
            r = c.fetchone()
            if r:
                txt_imie.value = r[1]
                txt_nazwisko.value = r[2]
                txt_klub.value = r[3]
                txt_adres.value = r[4]
                selected_foto_path = r[5]
                txt_info.value = r[6]
                img_profile.src = selected_foto_path if selected_foto_path else "https://via.placeholder.com/150"
                
                lista_aut.controls.clear()
                c.execute("SELECT model, rej FROM pojazdy WHERE osoba_id=?", (id_osoby,))
                for v in c.fetchall():
                    lista_aut.controls.append(ft.Text(f"• {v[0]} [{v[1]}]", size=16))
                page.update()

        def zapisz_osobe(e):
            c = conn.cursor()
            dane = (txt_imie.value, txt_nazwisko.value, txt_klub.value, txt_adres.value, selected_foto_path, txt_info.value)
            if selected_osoba_id is None:
                c.execute("INSERT INTO osoby (imie, nazwisko, klub, adres, foto_path, info) VALUES (?,?,?,?,?,?)", dane)
            else:
                c.execute("UPDATE osoby SET imie=?, nazwisko=?, klub=?, adres=?, foto_path=?, info=? WHERE id=?", 
                          dane + (selected_osoba_id,))
            conn.commit()
            page.snack_bar = ft.SnackBar(ft.Text("Zapisano!"))
            page.snack_bar.open = True
            odswiez_liste()

        def dodaj_pojazd(e):
            if selected_osoba_id is None: return
            def save_car(ev):
                c = conn.cursor()
                c.execute("INSERT INTO pojazdy (osoba_id, model, rej) VALUES (?,?,?)", 
                          (selected_osoba_id, m_input.value, r_input.value))
                conn.commit()
                dialog.open = False
                pokaz_szczegoly(selected_osoba_id)
                page.update()

            m_input = ft.TextField(label="Marka/Model")
            r_input = ft.TextField(label="Nr Rejestracyjny")
            dialog = ft.AlertDialog(
                title=ft.Text("Dodaj pojazd"),
                content=ft.Column([m_input, r_input], tight=True, height=140),
                actions=[ft.TextButton("Zapisz", on_click=save_car)]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        search_bar = ft.TextField(label="Szukaj...", on_change=odswiez_liste)

        detale_column = ft.Column([
            ft.Row([img_profile, ft.ElevatedButton("FOTO", on_click=lambda _: file_picker.pick_files())]),
            txt_imie, txt_nazwisko, txt_klub, txt_adres, txt_info,
            ft.Row([ft.Text("POJAZDY", weight="bold"), ft.IconButton(ft.icons.ADD_CIRCLE, on_click=dodaj_pojazd)]),
            lista_aut,
            ft.ElevatedButton("ZAPISZ DANE", icon=ft.icons.SAVE, on_click=zapisz_osobe)
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        page.add(
            ft.Text("Organizator Spraw Kryminalnych", size=20, weight="bold"),
            ft.Column([
                search_bar,
                ft.Container(content=lista_osob_container, height=150, border=ft.border.all(1, "grey")),
                detale_column
            ], expand=True)
        )
        odswiez_liste()

    except Exception as e:
        page.add(ft.Text(f"BŁĄD: {e}", color="red"))

ft.app(target=main)
