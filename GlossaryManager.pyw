from app.tk_ui import GlossaryManagerGUI
import tkinter as tk

def run():
    root = tk.Tk()
    ui = GlossaryManagerGUI(root)
    root.mainloop()

if __name__ == '__main__':
    run()
