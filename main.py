import flet as ft
import sqlite3
import os
import sys

# --- BEZPIECZNE USTALANIE ŚCIEŻKI DO BAZY ---
def get_db_path():
    try:
        # Jeśli Android/iOS - szukamy bezpiecznego katalogu dokumentów
        # Flet nie udostępnia tego wprost w module os, ale spróbujemy zapisać w katalogu domowym
        if "ANDROID_DATA" in os.environ:
            # Specyficzne dla Androida - katalog plików aplikacji
            # Zazwyczaj /data/data/com.twoja.nazwa/files
            storage = os.environ.get("EXTERNAL_STORAGE", os.environ.get("HOME", "."))
            return os.path.join(storage, "kryminalne.db")
        else:
            # Windows/Linux/Mac
            return "kryminalne.db"
    except Exception:
        return "kryminalne.db"

# --- BAZA DANYCH ---
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
    # --- KONFIGURACJA OKNA ---
    page.title = "Organizator Spraw Kryminalnych"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive" # Ważne dla Androida, żeby można było przewijać

    # --- TRYB AWARYJNY (TRY-EXCEPT) ---
    # Cała logika jest w bloku try, żeby wyłapać błąd czarnego ekranu
    try:
        db_path = get_db_path()
        
        # Próba połączenia z bazą
        try:
            conn = init_db(db_path)
        except Exception as db_e:
            page.add(ft.Text(f"BŁĄD KRYTYCZNY BAZY DANYCH:\n{db_e}\nŚcieżka: {db_path}", color="red", size=20))
            return

        selected_osoba_id = None
        selected_foto_path = None

        # --- KOMPONENTY UI ---
        txt_imie = ft.TextField(label="Imię", expand=True)
        txt_nazwisko = ft.TextField(label="Nazwisko", expand=True)
        txt_klub = ft.TextField(label="Klub/Organizacja", expand=True)
        txt_adres = ft.TextField(label="Adres", expand=True)
        txt_info = ft.TextField(label="Notatki", multiline=True, min_lines=2)
        img_profile = ft.Image(src="https://via.placeholder.com/150", width=150, height=150, fit=ft.ImageFit.CONTAIN)
        
        # Używamy Column zamiast ListView wewnątrz Row dla lepszej kontroli błędów
        lista_osob_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        lista_aut = ft.Column(spacing=5)

        # --- OBSŁUGA PLIKÓW ---
        def on_file_result(e: ft.FilePickerResultEvent):
            nonlocal selected_foto_path
            if e.files:
                selected_foto_path = e.files[0].path
                img_profile.src = selected_foto_path
                page.update()

        file_picker = ft.FilePicker(on_result=on_file_result)
        page.overlay.append(file_picker)

        # --- LOGIKA APLIKACJI ---
        def odswiez_liste(e=None):
            lista_osob_container.controls.clear()
            c = conn.cursor()
            search = f"%{search_bar.value if search_bar.value else ''}%"
            
            try:
                query = """
                    SELECT DISTINCT o.id, o.imie, o.nazwisko, o.klub 
                    FROM osoby o 
                    LEFT JOIN pojazdy p ON o.id = p.osoba_id
                    WHERE o.nazwisko LIKE ? OR p.rej LIKE ?
                    ORDER BY o.nazwisko ASC
                """
                c.execute(query, (search, search))
                rows = c.fetchall()
                
                if not rows:
                    lista_osob_container.controls.append(ft.Text("Brak wyników", italic=True))
                
                for row in rows:
                    lista_osob_container.controls.append(
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.SHIELD_PERSON),
                            title=ft.Text(f"{row[2]} {row[1]}", weight="bold"),
                            subtitle=ft.Text(f"{row[3]}"),
                            on_click=lambda _, idx=row[0]: pokaz_szczegoly(idx)
                        )
                    )
            except Exception as e:
                lista_osob_container.controls.append(ft.Text(f"Błąd odczytu: {e}", color="red"))
            
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
                
                # Na telefonie przełączamy widok na detale (opcjonalnie)
                # Tu dla prostoty zostawiamy widok dzielony
                page.update()

        def zapisz_osobe(e):
            try:
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
            except Exception as e:
                page.snack_bar = ft.SnackBar(ft.Text(f"Błąd zapisu: {e}"))
                page.snack_bar.open = True
                page.update()

        def dodaj_pojazd(e):
            if selected_osoba_id is None: 
                page.snack_bar = ft.SnackBar(ft.Text("Wybierz najpierw osobę!"))
                page.snack_bar.open = True
                page.update()
                return
            
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
                content=ft.Column([m_input, r_input], tight=True, height=150),
                actions=[ft.TextButton("Zapisz", on_click=save_car)]
            )
            page.dialog = dialog
            dialog.open = True
            page.update()

        # --- BUDOWANIE LAYOUTU ---
        search_bar = ft.TextField(
            label="Szukaj...", 
            prefix_icon=ft.icons.SEARCH, 
            on_change=odswiez_liste
        )

        detale_column = ft.Column([
            ft.Row([
                img_profile,
                ft.Column([
                    ft.ElevatedButton("FOTO", icon=ft.icons.IMAGE, 
                                     on_click=lambda _: file_picker.pick_files(allow_multiple=False)),
                    ft.Text("Dane podstawowe", weight="bold")
                ])
            ]),
            txt_imie, txt_nazwisko,
            txt_klub, txt_adres,
            txt_info,
            ft.Divider(),
            ft.Row([
                ft.Text("POJAZDY", weight="bold"),
                ft.IconButton(ft.icons.ADD_CIRCLE, on_click=dodaj_pojazd)
            ]),
            lista_aut,
            ft.ElevatedButton("ZAPISZ", icon=ft.icons.SAVE, on_click=zapisz_osobe)
        ], scroll=ft.ScrollMode.AUTO, expand=True)

        # Responsywny widok
        layout = ft.Row([
            ft.Column([search_bar, lista_osob_container], expand=1),
            ft.VerticalDivider(width=1),
            ft.Column([detale_column], expand=2)
        ], expand=True)

        if page.window_width < 600:
             # Tryb mobilny - jedna kolumna (uproszczony)
             # W pełnej wersji użylibyśmy nawigacji Tabs
             pass 

        page.add(
            ft.Text("Organizator Spraw Kryminalnych", size=20, weight="bold"),
            layout
        )
        
        odswiez_liste()

    except Exception as e:
        # TO JEST KLUCZOWE - jeśli coś wybuchnie, zobaczysz to na ekranie
        page.add(ft.Text(f"CRITICAL ERROR STARTUP:\n{e}", color="red", size=20))

ft.app(target=main)
        
