from tk_ui import GlossaryManagerGUI
from threading import Thread
import tkinter as tk

def run():
    root = tk.Tk()
    ui = GlossaryManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    run()

