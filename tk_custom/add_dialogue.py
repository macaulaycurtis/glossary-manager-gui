import tkinter as tk
from collections import OrderedDict

class AddDialogue(tk.Toplevel):

    def __init__(self, parent, arg):
        tk.Toplevel.__init__(self, parent)
        self.title('Add new entry')
        self.parent = parent
        self._create_headers()
        self._create_fields()
        self._create_buttons()
        self.grab_set()
        self.grid_rowconfigure(1, weight=1)
        self.bind('<Return>', lambda event: self.confirm())
        self.bind('<Escape>', lambda event: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.source_entry.insert(0, arg)
        self.translation_entry.focus_set()
        self.wait_window(self)

    def _create_headers(self):
        headers = ('Source', 'Translation', 'Context', 'Glossary')
        for i in range(len(headers)):
            label = tk.Label(self, text=headers[i])
            label.grid(row=0, column=i)

    def _create_fields(self):
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
        for i in range(len(second_row)):
            second_row[i].grid(row=1, column=i, sticky='ew', padx=1)



    def _create_buttons(self):
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
