from tk_ui import Glossary_Manager_GUI
from threading import Thread
import tkinter as tk

def run():
    root = tk.Tk()
    ui = Glossary_Manager_GUI(root)

    listen_thread = Thread(target=ui.hotkey_listen, daemon=True)
    listen_thread.start()

    root.mainloop()

if __name__ == '__main__':
    run()
