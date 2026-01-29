import flet as ft
import sqlite3

# --- BAZA DANYCH (Zostaje ta sama logika) ---
def init_db():
    conn = sqlite3.connect("organizator.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS osoby 
                 (id INTEGER PRIMARY KEY, imie TEXT, nazwisko TEXT, klub TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pojazdy 
                 (id INTEGER PRIMARY KEY, osoba_id INTEGER, model TEXT, rej TEXT)''')
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "Organizator Alaska v2"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    conn = init_db()

    # --- ELEMENTY UI ---
    txt_imie = ft.TextField(label="Imię", expand=True)
    txt_nazwisko = ft.TextField(label="Nazwisko", expand=True)
    txt_klub = ft.TextField(label="Klub", expand=True)
    
    lista_osob = ft.ListView(expand=True, spacing=10)
    
    # --- FUNKCJE ---
    def odswiez_liste(e=None):
        lista_osob.controls.clear()
        c = conn.cursor()
        search = f"%{search_bar.value}%"
        c.execute("SELECT id, imie, nazwisko, klub FROM osoby WHERE nazwisko LIKE ? ORDER BY nazwisko ASC", (search,))
        for row in c.fetchall():
            lista_osob.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.PERSON),
                    title=ft.Text(f"{row[2]} {row[1]}"),
                    subtitle=ft.Text(f"Klub: {row[3]}"),
                    on_click=lambda _, idx=row[0]: pokaz_szczegoly(idx)
                )
            )
        page.update()

    def zapisz_osobe(e):
        if not txt_imie.value or not txt_nazwisko.value:
            return
        c = conn.cursor()
        c.execute("INSERT INTO osoby (imie, nazwisko, klub) VALUES (?,?,?)", 
                  (txt_imie.value, txt_nazwisko.value, txt_klub.value))
        conn.commit()
        txt_imie.value = ""; txt_nazwisko.value = ""; txt_klub.value = ""
        odswiez_liste()

    def pokaz_szczegoly(id_osoby):
        # Tutaj otwierałoby się nowe okno/widok z pojazdami
        page.snack_bar = ft.SnackBar(ft.Text(f"Wybrano ID: {id_osoby}"))
        page.snack_bar.open = True
        page.update()

    search_bar = ft.TextField(
        label="Szukaj osoby...", 
        prefix_icon=ft.icons.SEARCH, 
        on_change=odswiez_liste
    )

    # --- UKŁAD STRONY ---
    page.add(
        ft.Text("Menedżer Kontaktów", size=30, weight="bold"),
        search_bar,
        ft.Row([txt_imie, txt_nazwisko]),
        ft.Row([txt_klub, ft.ElevatedButton("DODAJ", on_click=zapisz_osobe, icon=ft.icons.ADD)]),
        ft.Divider(),
        ft.Text("Lista osób (Alfabetycznie):", color="blue"),
        lista_osob
    )
    
    odswiez_liste()

ft.app(target=main)
      
