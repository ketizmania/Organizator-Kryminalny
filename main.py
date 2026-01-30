import flet as ft
import sqlite3
import os

def get_db_path():
    # Zmieniamy nazwę na nową, by uniknąć konfliktów z poprzednimi wersjami
    db_name = "osk_database_v30.db"
    if "ANDROID_DATA" in os.environ:
        return os.path.join(os.environ.get("HOME", "."), db_name)
    return db_name

def init_db():
    path = get_db_path()
    try:
        # Próba połączenia
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute('''CREATE TABLE IF NOT EXISTS osoby 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      imie TEXT, nazwisko TEXT, klub TEXT, 
                      info TEXT, pojazdy TEXT)''')
        conn.commit()
        return conn
    except Exception as e:
        # Jeśli baza jest uszkodzona/zablokowana - usuwamy ją i tworzymy od nowa
        if os.path.exists(path):
            os.remove(path)
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.execute('''CREATE TABLE IF NOT EXISTS osoby 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      imie TEXT, nazwisko TEXT, klub TEXT, 
                      info TEXT, pojazdy TEXT)''')
        return conn

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "OSK v3.0 - Stabilny"
    
    # Funkcja do kopiowania błędu (na wszelki wypadek)
    def copy_err(text):
        page.set_clipboard(text)
        page.snack_bar = ft.SnackBar(ft.Text("Skopiowano błąd!"))
        page.snack_bar.open = True
        page.update()

    try:
        conn = init_db()

        t_imie = ft.TextField(label="Imię")
        t_nazwisko = ft.TextField(label="Nazwisko")
        t_klub = ft.TextField(label="Klub")
        t_pojazdy = ft.TextField(label="Pojazdy", multiline=True)
        t_info = ft.TextField(label="Notatki", multiline=True)
        lista = ft.Column()

        def zapisz(e):
            if t_nazwisko.value:
                conn.execute("INSERT INTO osoby (imie, nazwisko, klub, info, pojazdy) VALUES (?,?,?,?,?)", 
                             (t_imie.value, t_nazwisko.value, t_klub.value, t_info.value, t_pojazdy.value))
                conn.commit()
                t_imie.value = t_nazwisko.value = t_klub.value = t_info.value = t_pojazdy.value = ""
                odswiez()

        def odswiez(e=None):
            lista.controls.clear()
            cur = conn.execute("SELECT imie, nazwisko FROM osoby ORDER BY id DESC LIMIT 10")
            for r in cur:
                lista.controls.append(ft.Text(f"• {r[1]} {r[0]}", size=16))
            page.update()

        page.add(
            ft.Text("SYSTEM OPERACYJNY v3.0", size=22, weight="bold", color=ft.colors.BLUE_400),
            t_imie, t_nazwisko, t_klub, t_pojazdy, t_info,
            ft.Row([
                ft.ElevatedButton("ZAPISZ", on_click=zapisz, icon=ft.icons.SAVE),
                ft.ElevatedButton("ODŚWIEŻ", on_click=odswiez, icon=ft.icons.REFRESH)
            ]),
            ft.Divider(),
            ft.Text("OSTATNIE WPISY:"),
            lista
        )
        odswiez()

    except Exception as ex:
        # WYŚWIETLANIE BŁĘDU JEŚLI APLIKACJA NIE RUSZY
        err_msg = str(ex)
        page.add(
            ft.Container(
                padding=20, bgcolor=ft.colors.RED_900, border_radius=10,
                content=ft.Column([
                    ft.Text("BŁĄD STARTU:", weight="bold"),
                    ft.Text(err_msg, selectable=True),
                    ft.ElevatedButton("KOPIUJ BŁĄD", on_click=lambda _: copy_err(err_msg))
                ])
            )
        )
        page.update()

ft.app(target=main)
