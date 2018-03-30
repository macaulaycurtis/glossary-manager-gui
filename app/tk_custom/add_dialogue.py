import tkinter as tk
from collections import OrderedDict
from app.tk_custom.context_popup import context_popup

class AddDialogue(tk.Toplevel):

    def __init__(self, parent, arg):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.create_headers()
        self.create_fields()
        self.create_buttons()
        self.setup_window()
        self.setup_bindings()
        self.source_entry.insert(0, arg)

    def setup_window(self):
        self.title('Add new entry')
        self.grab_set()
        self.transient(self.parent)
        self.resizable(False, False)
        self.translation_entry.focus_set()

    def setup_bindings(self):
        self.bind('<Return>', lambda event: self.confirm())
        self.bind('<Escape>', lambda event: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def create_headers(self):
        self.grid_rowconfigure(1, weight=1)
        headers = ('Source', 'Translation', 'Context', 'Glossary')
        for i, header in enumerate(headers):
            label = tk.Label(self, text=header, font=self.parent.config['font2'])
            label.grid(row=0, column=i)

    def create_fields(self):
        self.source_entry = tk.Entry(self, font=self.parent.config['font1'])
        self.translation_entry = tk.Entry(self, font=self.parent.config['font1'])
        self.context_entry = tk.Entry(self, font=self.parent.config['font1'])
        glossary_button = tk.Menubutton(
            self
            , textvariable=self.parent.active_glossary
            , font=self.parent.config['font1']
            , bg='#fff'
            , activebackground='#fff'
            , relief='sunken'
            , width='20'
            , anchor='w'
            , pady=1
            , padx=1
            )
        glossary_menu = tk.Menu(glossary_button, bg='#fff', tearoff=False)

        for glossary in self.parent.gm.list_glossaries():
            glossary_menu.add_radiobutton(label=glossary, variable=self.parent.active_glossary, value=glossary)
        glossary_button.configure(menu=glossary_menu)

        second_row = [self.source_entry, self.translation_entry, self.context_entry, glossary_button]
        for i, widget in enumerate(second_row):
            widget.grid(row=1, column=i, sticky='ew', padx=1)

        for widget in [self.source_entry, self.translation_entry, self.context_entry]:
            widget.bind('<Button-3>', context_popup)

    def create_buttons(self):
        add_button = tk.Button(self, text='Add', command=self.confirm)
        add_button.grid(row=2, column=2, sticky='ew', pady=5)
        cancel_button = tk.Button(self, text='Cancel', command=self.cancel)
        cancel_button.grid(row=2, column=3, sticky='ew', pady=5)

    def confirm(self):
        if not self.source_entry.get() == '':
            self.new_entry = OrderedDict([
                ('source', self.source_entry.get())
                , ('translation', self.translation_entry.get())
                , ('context', self.context_entry.get())
                ])
            self.destroy()

    def cancel(self):
        self.new_entry = None
        self.destroy()
