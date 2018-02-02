import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from os.path import relpath
from copy import copy
from configparser import ConfigParser
from collections import OrderedDict
from gm.glossary_manager import GlossaryManager
from hotkeys import GlobalHotkeyListener
from tk_custom.spreadsheet import Spreadsheet
from tk_custom.add_dialogue import AddDialogue
import licence

class GlossaryManagerGUI(tk.Frame):
    
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.pack(fill='both', expand=True)
        self.parent = root
        self._setup_attributes()
        self._setup_bindings()       
        self._create_widgets()
        self._create_menu_bar() 
        self._setup_window()
        self.setup_gm()
        self.search_box.focus()

    def _setup_attributes(self):
        self.config_parser = ConfigParser()
        self.config_parser.read('config.ini', encoding='utf-8')
        self.config = self.config_parser['USER']
        self.history = []
        self.filters = {'fuzzy' : tk.BooleanVar(), 'reverse' : tk.BooleanVar()}
        self.active_glossary = tk.StringVar()
        self.active_glossary.trace('w', self.change_default_glossary)
        self.status = tk.StringVar()
        self.gm = GlossaryManager(self.config['path'])

    def _setup_bindings(self):
        self.parent.bind('<Control-s>', self.save_all)
        self.parent.bind('<Control-q>', self.exit)
        self.parent.bind('<Control-w>', self.exit)
        self.parent.bind('<Control-o>', self.open)
        self.parent.bind('<Control-n>', self.new)
        self.parent.protocol('WM_DELETE_WINDOW', self.exit)

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        input_group = tk.Frame(self)
        input_group.grid(row=0, sticky='new', columnspan=2)
        input_group.grid_columnconfigure(0, weight=1)

        # SEARCH BOX #
        self.search_box = tk.Entry(font = self.config['font1'])
        self.search_box.grid(row=0, column=0, sticky='ew', padx=2, pady=2, in_=input_group)
        self.search_box.bind('<Return>', lambda event: search_button.invoke())
        self.search_box.bind('<Insert>', lambda event: add_button.invoke())
        search_button = tk.Button(text='Search', command=lambda: self.search(self.search_box.get()))
        search_button.grid(row=0, column=1, sticky='e', padx=2, pady=2, in_=input_group)

        # HISTORY DROPDOWN #
        history_button = tk.Menubutton(
            text='↓'
            , font=self.config['font2']
            , bg='#fff'
            , activebackground='#fff'
            , cursor='hand2'
            , pady=1
            , padx=3
            )
        history_button.grid(row=0, column=0, sticky='e', in_=input_group, padx=3)
        self.history_menu = tk.Menu(history_button, bg='#fff', tearoff=False)
        history_button.configure(menu=self.history_menu)

        # FILTER BUTTONS #
        filter_buttons = tk.Frame()
        filter_buttons.grid(row=1, column=0, sticky='w', in_=input_group)
        for f in self.filters:
            self.filters[f].set(False)
            button = tk.Checkbutton(text=f.title(), padx=2, variable=self.filters[f])
            button.pack(side='left', in_=filter_buttons)

        # ADD BUTTON #
        add_button = tk.Button(text='Add', command=lambda: self.add(self.search_box.get()))
        add_button.grid(row=1, column=1, sticky='ew', padx=2, pady=2, in_=input_group)

        # OUTPUT #
        self.output = Spreadsheet(self, self.gm, self.config)
        self.output.grid(row=1, sticky='nesw', columnspan=2)
        self.grid_rowconfigure(1, weight=8)

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

    def _create_menu_bar(self):
        menu_bar = tk.Menu(self)

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

        # HELP MENU #
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About', command=self.about)

        self.parent.config(menu=menu_bar)

    def _setup_window(self):
        self.parent.title(self.config['title'])
        self.parent.minsize(self.config['minimum_x'], self.config['minimum_y'])
        if self.config.getboolean('start_minimized'):
            selfroot.iconify()
        self.parent.update()

    def setup_gm(self):
        self.gm.load()
        try:
            if self.config['default_glossary'] in self.gm.list_glossaries():
                self.active_glossary.set(self.config['default_glossary'])  
            else:
                self.active_glossary.set(self.gm.list_glossaries()[0])
            self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))
        except IndexError:
            self.active_glossary.set('')
            self.status.set('No glossaries loaded: <{}> either does not exist or contains no glossary files.'.format(self.config['path']))

    def search(self, arg='', fuzzy=0.0, column='source'):
        """Search for a keyword. Returns search results in the format OrderedDict([{source, translation, context, glossary, index, ratio}])"""
        if arg == '': return
        self.history_menu.add_command(
            label=arg
            , command=lambda: (self.search_box.delete(0, tk.END), self.search_box.insert(0, arg))
            )
        if self.filters['fuzzy'].get(): fuzzy = self.config.getfloat('minimum_match')
        if self.filters['reverse'].get(): column = 'translation'
        self.search_results = self.gm.search(arg, fuzzy, column)
        if len(self.search_results) == 0: self.status.set('No results found.')
        else: self.status.set('Found {} results.'.format(len(self.search_results)))
        self.output.display(self.search_results)

    def add(self, arg):
        """Create a dialogue for adding a row to a glossary."""
        if self.active_glossary.get() == '':
            return
        add_dialogue = AddDialogue(self, arg)
        if add_dialogue.new_entry:
            self.gm.add_entry(add_dialogue.new_entry, self.active_glossary.get())
            self.search(add_dialogue.new_entry['source'])

    def new(self, event=None):
        """Create a dialogue for adding a new glossary to the manager."""
        filepath = filedialog.asksaveasfilename(
            initialdir=self.config['path']
            ,title='New glossary'
            ,filetypes=(
                ('Comma-separated values', '*.csv')
                , ('All files', '*.*')
                )
            )
        if filepath == '': return
        if not filepath[-4:] == '.csv': filepath = filepath + '.csv'
        filename = filepath[filepath.rfind('/') + 1:]
        if filename in self.gm.list_glossaries():
            messagebox.showwarning(
            'File not created',
            'There is already a glossary with the name {}.'.format(filename)
            )
            return
        self.gm.add_glossary(filepath, filename, mode='new')
        self.active_glossary.set(filename)
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))

    def open(self, event=None):
        """Create a dialogue for importing an existing glossary into the manager."""
        filepath = filedialog.askopenfilename(
            initialdir=self.config['path']
            ,title='Import file'
            ,filetypes=(
                ('Comma-separated values', '*.csv')
                , ('Excel 2003 spreadsheet', '*.xls')
                , ('Excel 2007 spreadsheet', '*.xlsx')
                , ('All files', '*.*')
                )
            )
        if filepath == '': return
        name = filepath[filepath.rfind('/') + 1:filepath.rfind('.')]
        filename = name
        i = 2
        while filename + '.csv' in self.gm.list_glossaries():
            if relpath(filepath[:filepath.rfind('/')], self.config['path']) == '.': return
            filename = name + str(i)
            i += 1
        filename = filename + '.csv'
        try: self.gm.add_glossary(filepath, filename, mode='open')
        except Exception:
            messagebox.showerror('Import error', 'An error occurred while importing that file.')
            raise
        self.output.display(self.gm.display_contents(filename))
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))

    def change_gm_path(self, event=None):
        """Create a dialog for changing the default directory of the manager."""
        new_path = filedialog.askdirectory(
            initialdir=self.config['path']
            , title='Change glossary directory'
            , mustexist=True
            )
        if new_path == '': return
        try:
            new_path = relpath(new_path)
        except:
            pass
        self.config_parser.set('USER', 'path', new_path)
        with open('config.ini', 'w', encoding='utf-8') as conf:
            self.config_parser.write(conf)
        self.setup_gm()

    def change_default_glossary(self, *args):
        self.config_parser.set('USER', 'default_glossary', self.active_glossary.get())
        with open('config.ini', 'w', encoding='utf-8') as conf:
            self.config_parser.write(conf)

    def about(self, event=None):
        """Display an about box with the copyright licence."""
        about_text = str
        messagebox.showinfo(title='About', message=licence._)

    def save_all(self, event=None):
        """Save all changes to all glossaries."""
        saved = self.gm.save()
        if saved: self.status.set('Saved: ' + saved)

    def exit(self, event=None):
        """Exit the tkinter loop."""
        try:
            if self.gm.unsaved_changes():
                save = messagebox.askyesnocancel(
                    title='Save on close'
                    , message='Save changes to glossaries before closing?'
                    )
                if save == None:
                    return
                elif save:
                    self.save_all()
        except Exception as e:
            print(e)
            pass
        self.parent.destroy()

    def hotkey_listen(self):
        """ Instantiate the global hotkey listener, which returns highlighted text from other
programs via the clipboard, then search for that text. """
        self.hotkey_listener = GlobalHotkeyListener(
            self.config['hotkey_mod']
            , self.config['hotkey_key']
            , self.config.getfloat('hotkey_sleep_time')
            , self
            )
        while True:
            paste = self.hotkey_listener.listen()
            paste = paste.strip()
            self.search_box.delete(0, tk.END)
            self.search_box.insert(0, paste)
            self.search(paste)
            self.master.deiconify()
            self.search_box.focus()

if __name__ == '__main__':
    root = tk.Tk()
    ui = GlossaryManagerGUI(root)
    root.mainloop()
