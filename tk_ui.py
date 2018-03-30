import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from os.path import relpath
from pathlib import Path
from configparser import ConfigParser
from app.hotkeys import GlobalHotkeyListener
from app.gm.glossary_manager import GlossaryManager
from app.tk_custom.spreadsheet import Spreadsheet
from app.tk_custom.add_dialogue import AddDialogue
from app.tk_custom.hotkey_selector import HotkeySelector
from app.tk_custom.context_popup import context_popup

class GlossaryManagerGUI(tk.Frame):
    
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.pack(fill='both', expand=True)
        self.root = root
        self.setup_attributes()
        self.setup_bindings()
        self.create_widgets()
        self.create_menu_bar() 
        self.setup_window()
        self.setup_gm()
        self.search_box.focus()

    def setup_attributes(self):
        self.config_parser = ConfigParser()
        self.config_parser.read('config.ini', encoding='utf-8-sig')
        self.config = self.config_parser['USER']
        self.history = []
        self.active_glossary = tk.StringVar()
        self.active_glossary.trace('w', self.change_default_glossary)
        self.minimum_match = tk.DoubleVar()
        self.reverse = tk.BooleanVar()
        self.reverse.set(False)
        self.status = tk.StringVar()
        self.path = Path(self.config['path'])
        self.gm = GlossaryManager()

    def setup_bindings(self):
        self.root.bind('<Control-s>', self.save_all)
        self.root.bind('<Control-q>', self.exit)
        self.root.bind('<Control-w>', self.exit)
        self.root.bind('<Control-o>', self.open)
        self.root.bind('<Control-n>', self.new)
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        self.setup_hotkey_listener()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        input_group = tk.Frame(self)
        input_group.grid(row=0, sticky='new', columnspan=2)
        input_group.grid_columnconfigure(0, weight=1)

        # SEARCH BOX #
        self.search_box = ttk.Combobox(values=self.history, font=self.config['font1'])
        self.root.option_add('*TCombobox*Listbox.font', self.config['font2'])
        self.search_box.grid(row=0, column=0, sticky='ew', padx=2, pady=2, in_=input_group)
        self.search_box.bind('<Return>', lambda event: search_button.invoke())
        self.search_box.bind('<Insert>', lambda event: add_button.invoke())
        search_button = tk.Button(text='Search', command=lambda: self.search(self.search_box.get()))
        search_button.grid(row=0, column=1, sticky='e', padx=2, pady=2, in_=input_group)
        self.search_box.bind('<Button-3>', context_popup)

        # FILTERS #
        filters = tk.Frame()
        filters.grid(row=1, column=0, sticky='w', in_=input_group)
        
        reverse_button = tk.Checkbutton(text='Reverse', padx=2, variable=self.reverse)
        reverse_button.grid(row=0, column=0, in_=filters)

        fuzzy = tk.BooleanVar()
        fuzzy.set(False)
        fuzzy_toggle= tk.Checkbutton(text='Fuzzy', padx=2, variable=fuzzy)
        fuzzy_toggle.grid(row=0, column=1, in_=filters)
        fuzzy_select = tk.Frame()
        fuzzy_select.grid(row=0, column=2, in_=filters)
        selector = tk.Spinbox(fuzzy_select, from_=0.05
                              , to=1.0, increment=0.05
                              , textvariable=self.minimum_match
                              , exportselection=True, width=4
                              , state='readonly', readonlybackground='white')
        selector.grid(row=0, column=0, padx=2)
        fuzzy_label = tk.Label(fuzzy_select, text='Minimum match')
        fuzzy_label.grid(row=0, column=1)

        def toggle_fuzzy():
            if fuzzy.get():
                fuzzy_select.grid()
                self.minimum_match.set(0.35)
            else:
                fuzzy_select.grid_remove()
                self.minimum_match.set(0.00)

        fuzzy_toggle.configure(command=toggle_fuzzy)
        toggle_fuzzy()

        # ADD BUTTON #
        add_button = tk.Button(text='Add', command=lambda: self.add(self.search_box.get()))
        add_button.grid(row=1, column=1, sticky='ew', padx=2, pady=2, in_=input_group)

        # OUTPUT #
        self.output = Spreadsheet(self)
        self.output.grid(row=1, sticky='nesw', columnspan=2)
        self.grid_rowconfigure(1, weight=1)

        # STATUS BAR #
        status_bar = tk.Label(
            textvariable=self.status
            , font=self.config['font2']
            , justify='left'
            , anchor='w'
            )
        status_bar.bind('<Configure>', lambda event: status_bar.configure(wraplength=event.width))
        status_bar.grid(column=0, row=2, sticky='esw', in_=self)

        # SIZE GRIP #
        size_grip = ttk.Sizegrip()
        size_grip.grid(column=1, row=2, sticky='se', in_=self)

    def create_menu_bar(self):
        menu_bar = tk.Menu(self, font=self.config['font2'])

        # FILE MENU #
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='New glossary...', command=self.new)
        file_menu.add_command(label='Import...', command=self.open)
        file_menu.add_command(label='Save', command=self.save_all)
        file_menu.add_command(label='Exit', command=self.exit)

        # OPTION MENU #
        option_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='Options', menu=option_menu)
        option_menu.add_command(label='Change glossary directory...', command=self.change_gm_path)
        option_menu.add_command(label='Change global search hotkey...', command=self.change_ghk)

        # BROWSE MENU #
        browse_menu = tk.Menu(option_menu, tearoff=0)
        option_menu.add_cascade(label='Browse glossary', menu=browse_menu)
        
        def update():
            selection = tk.StringVar()
            browse_menu.delete(0, 'end')
            for glossary in self.gm.list_glossaries():
                browse_menu.add_radiobutton(label=glossary, variable=selection, value=glossary)

            def browse(*args):
                self.output.display(self.gm.display_contents(selection.get()))

            selection.trace('w', browse)
            
        browse_menu.configure(postcommand=update)
        
        # HELP MENU #
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='Licence', command=self.licence)

        self.root.config(menu=menu_bar)

    def setup_window(self):
        self.root.title(self.config['title'])
        self.root.minsize(self.config['minimum_x'], self.config['minimum_y'])
        self.root.update()

    def setup_gm(self):
        self.gm.load(self.path)
        try:
            if self.config['default_glossary'] in self.gm.list_glossaries():
                self.active_glossary.set(self.config['default_glossary'])  
            else:
                self.active_glossary.set(self.gm.list_glossaries()[0])
            self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))
        except IndexError:
            self.active_glossary.set('')
            self.status.set('No glossaries loaded: <{}> either does not exist or contains no glossary files.'.format(self.path))

    def search(self, arg='', column='source'):
        """Search for a keyword. Returns search results in the format OrderedDict([{source, translation, context, glossary, index, ratio}])"""
        if arg == '':
            return
        self.history.append(arg)
        self.search_box['values'] = self.history
        if self.reverse.get():
            column = 'translation'
        self.search_results = self.gm.search(arg, self.minimum_match.get(), column)
        if len(self.search_results) == 0:
            self.status.set('No results found.')
        else:
            self.status.set('Found {} results.'.format(len(self.search_results)))
        self.output.display(self.search_results)

    def add(self, arg):
        """Create a dialogue for adding a row to a glossary."""
        if self.active_glossary.get() == '':
            return
        add_dialogue = AddDialogue(self, arg)
        add_dialogue.geometry('+{}+{}'.format(self.root.winfo_x(), self.root.winfo_y()))
        add_dialogue.wait_window(add_dialogue)
        if add_dialogue.new_entry:
            self.gm.add_entry(add_dialogue.new_entry, self.active_glossary.get())
            self.search(add_dialogue.new_entry['source'])

    def new(self, event=None):
        """Create a dialogue for adding a new glossary to the manager."""
        filepath = filedialog.asksaveasfilename(
            initialdir=str(self.path)
            ,title='New glossary'
            ,filetypes=(
                ('Comma-separated values', '*.csv')
                , ('All files', '*.*')
                )
            )
        if filepath == '': return
        filepath = Path(filepath)
        if not filepath.suffix == '.csv':
            filepath = filepath.with_suffix('.csv')
        filename = filepath.name
        if filename in self.gm.list_glossaries():
            messagebox.showwarning(
            'File not created',
            'There is already a glossary with the name {}.'.format(filename)
            )
            return
        self.gm.add_glossary(filepath, mode='new')
        self.active_glossary.set(filename)
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))

    def open(self, event=None):
        """Create a dialogue for importing an existing glossary into the manager."""
        filepath = filedialog.askopenfilename(
            initialdir=str(self.path)
            ,title='Import file'
            ,filetypes=(
                ('Comma-separated values', '*.csv')
                , ('Excel 2003 spreadsheet', '*.xls')
                , ('Excel 2007 spreadsheet', '*.xlsx')
                , ('All files', '*.*')
                )
            )
        if filepath == '': return
        filepath = Path(filepath)
        try: self.gm.add_glossary(filepath, mode='open')
        except Exception as e:
            messagebox.showerror('Import error', 'An error occurred while importing the file:\n{}'.format(e))
            return
        self.output.display(self.gm.display_contents(self.gm.list_glossaries()[-1]))
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))

    def change_gm_path(self, event=None):
        """Create a dialog for changing the default directory of the manager."""
        new_path = filedialog.askdirectory(
            initialdir=str(self.path)
            , title='Change glossary directory'
            , mustexist=True
            )
        if new_path == '': return
        try:
            new_path = Path(relpath(new_path))
        except:
            new_path = Path(new_path)
        self.config_parser.set('USER', 'path', str(new_path))
        with Path('config.ini').open('w', encoding='utf-8') as conf:
            self.config_parser.write(conf)
        self.path = new_path
        self.setup_gm()

    def change_ghk(self, event=None):
        """Create a dialog for changing the global hotkey."""
        self.ghk.stop()
        selector = HotkeySelector(self)
        selector.geometry('+{}+{}'.format(self.root.winfo_x(), self.root.winfo_y()))
        selector.wait_window(selector)
        if selector.confirmed and selector.hotkey_mod and selector.hotkey_key:
            self.config_parser.set('USER', 'hotkey_mod', selector.hotkey_mod)
            self.config_parser.set('USER', 'hotkey_key', selector.hotkey_key)
            with Path('config.ini').open('w', encoding='utf-8') as conf:
                self.config_parser.write(conf)
        self.setup_hotkey_listener()

    def change_default_glossary(self, *args):
        self.config_parser.set('USER', 'default_glossary', self.active_glossary.get())
        with Path('config.ini').open('w', encoding='utf-8') as conf:
            self.config_parser.write(conf)

    def licence(self, event=None):
        licence = str
        with Path('licence.txt').open('r', encoding='utf-8-sig') as f:
            licence = f.read()
        messagebox.showinfo(title='Licence', message=licence)

    def save_all(self, event=None):
       '''Save all changes to all glossaries.'''
       saved = self.gm.save()
       if saved: self.status.set('Saved: ' + saved)

    def exit(self, event=None):
        try:
            if self.gm.unsaved_changes():
                save = messagebox.askyesnocancel(title='Save on close'
                                                 , message='Save changes to glossaries before closing?')
                if save == None:
                    return
                elif save:
                    self.save_all()
        except Exception as e:
            print(e)
            pass
        self.root.destroy()

    def setup_hotkey_listener(self):
        """ Instantiate the global hotkey listener, which returns highlighted text from other
programs via the clipboard, then search for that text. """

        def hotkey_handler(paste):
            paste = paste.strip()
            self.search_box.delete(0, tk.END)
            self.search_box.insert(0, paste)
            self.search(paste)
            self.master.deiconify()
            self.search_box.focus()
        
        self.ghk = GlobalHotkeyListener(
            (self.config['hotkey_mod'], self.config['hotkey_key'])
            , self.config.getfloat('hotkey_sleep_time')
            , hotkey_handler
            )
        self.ghk.start()


if __name__ == '__main__':
    root = tk.Tk()
    ui = GlossaryManagerGUI(root)
    root.mainloop()
