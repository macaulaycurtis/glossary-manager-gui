from tk_ui import Glossary_Manager_GUI
from threading import Thread
import tkinter as tk

def run():
    root = tk.Tk()
    ui = GlossaryManagerGUI(root)

    listen_thread = Thread(target=ui.hotkey_listen, daemon=True)
    listen_thread.start()

    root.mainloop()
    ui.hotkey_listener.unregister()

if __name__ == '__main__':
    run()
