import tkinter as tk

def context_popup(e):
    """ Displays a standard context menu for any text widget - bind to button3 for basic functionality. """
    e.widget.focus()
    context = tk.Menu(tearoff=0)
    context.add_command(label="Cut", command=lambda e=e: e.widget.event_generate('<Control-x>'))
    context.add_command(label="Copy", command=lambda e=e: e.widget.event_generate('<Control-c>'))
    context.add_command(label="Paste", command=lambda e=e: e.widget.event_generate('<Control-v>'))
    context.add_command(label="Delete", command=lambda e=e: e.widget.event_generate('<Delete>'))
    try:
        context.tk_popup(e.x_root+40, e.y_root+10,entry="0")
    finally:
        context.grab_release()
