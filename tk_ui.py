import tkinter as tk
import tkinter.ttk as ttk
import hotkeys
from tkinter import filedialog, messagebox
from os.path import relpath
from copy import copy
from configparser import ConfigParser
from glossarymanager import GlossaryManager
from collections import OrderedDict

class GlossaryManagerGUI():
    
    def __init__(self, master):
        self.master = master
        self._setup_attributes()
        self._setup_bindings()       
        self._create_input_group()
        self._create_output_group()
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

    def _setup_bindings(self):
        self.master.bind('<Control-s>', self.save_all)
        self.master.bind('<Control-q>', self.exit)
        self.master.bind('<Control-w>', self.exit)
        self.master.bind('<Control-o>', self.open)
        self.master.bind('<Control-n>', self.new)
        self.master.protocol('WM_DELETE_WINDOW', self.exit)

    def _create_input_group(self):
        input_group = tk.Frame(self.master)
        input_group.pack(fill='x')
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

    def _create_output_group(self):
        output_group = tk.Frame(self.master)
        output_group.pack(fill='both', expand=True)
        output_group.grid_columnconfigure(0, weight=1)
        output_group.grid_rowconfigure(0, weight=1)

        # TREEVIEW #
        column_headings = ['Source', 'Translation', 'Context', 'Glossary', 'Result']
        displayed_columns = ['Source', 'Translation', 'Context', 'Glossary']
        self.tree = ttk.Treeview(columns=column_headings, displaycolumns=displayed_columns, show='headings')
        for c in displayed_columns:
            self.tree.heading(c, text=c)
            self.tree.column(c,minwidth=100)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=output_group)
        ttk.Style().configure('Treeview', font=self.config['font1'])
        ttk.Style().configure('Treeview.Heading', font=self.config['font2'])          

        # SCROLLBARS #
        vertical_scroll = ttk.Scrollbar(orient='vertical', command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(orient='horizontal', command=self.tree.xview)
        vertical_scroll.grid(column=1, row=0, sticky='ns', in_=output_group)
        horizontal_scroll.grid(column=0, row=1, sticky='ew', in_=output_group)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
        
        # STATUS BAR #
        self.status = tk.StringVar()
        status_bar = tk.Label(
            textvariable=self.status
            , font=self.config['font2']
            , justify='left'
            , anchor='w'
            )
        status_bar.bind('<Configure>', lambda event: status_bar.configure(wraplength=event.width))
        status_bar.grid(column=0, row=2, sticky='ew', in_=output_group)

        # SIZE GRIP #
        size_grip = ttk.Sizegrip()
        size_grip.grid(column=1, row=2, sticky='se', in_= output_group)

        # TREE CONTEXT MENUS #
        cell_context = tk.Menu(tearoff=0)
        cell_context.add_command(label='Edit', command=self.edit)
        cell_context.add_command(label='Delete', command=self.delete)
        
        def context_menu(event):
            cell_context.entryconfig(0, state='normal')
            self.cell_x = event.x_root - self.tree.winfo_rootx()
            self.cell_y = event.y_root - self.tree.winfo_rooty()
            if self.tree.identify_region(self.cell_x, self.cell_y) == 'cell':
                if not self.tree.identify_row(self.cell_y) in self.tree.selection():
                    self.tree.selection_set(self.tree.identify_row(self.cell_y))
                if self.tree.identify_column(self.cell_x) == '#4':
                    cell_context.entryconfig(0, state='disabled')
                cell_context.post(event.x_root, event.y_root)

        def double_click_action(event):
            self.cell_x = event.x_root - self.tree.winfo_rootx()
            self.cell_y = event.y_root - self.tree.winfo_rooty()
            if self.tree.identify_region(self.cell_x, self.cell_y) == 'cell':
                if not self.tree.identify_column(self.cell_x) == '#4':
                    self.edit()

        self.tree.bind('<Button-3>', context_menu)
        self.tree.bind('<Double-Button-1>', double_click_action)
        self.tree.bind('<Delete>', self.delete)

    def _create_menu_bar(self):
        menu_bar = tk.Menu(self.master)

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

        self.master.config(menu=menu_bar)

    def _setup_window(self):
        self.master.title(self.config['title'])
        self.master.minsize(self.config['minimum_x'], self.config['minimum_y'])
        if self.config.getboolean('start_minimized'):
            self.master.iconify()
        self.master.update()

    def setup_gm(self):
        self.gm = GlossaryManager(self.config['path'])
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
        """Search for a keyword. Returns search results in the format:
OrderedDict([{source, translation, context, glossary, index, ratio}])"""
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
        self.display_results(self.search_results)

    def display_results(self, search_results):
        """Display the results of a search in the ttk tree."""
        self.tree.delete(*self.tree.get_children())
        i = 0
        for r in search_results:
            item = (r['source'], r['translation'], r['context'], r['glossary'], i)
            iid = self.tree.insert('', 'end', values=item)
            i += 1

    def edit(self, event=None):
        """Identify what cell was clicked on, create an editable popup, then update the cell when the popup is closed."""
        # Identify what cell was clicked on #
        column = self.tree.identify_column(self.cell_x)
        iid = self.tree.identify_row(self.cell_y)
        x,y,w,h = self.tree.bbox(iid, column)
        mid_y = int(y + h / 2)

        # Create an editable popup containing the text from that cell. #
        edit_text = tk.StringVar()
        edit_text.set(self.tree.set(iid, column))
        self.cell_popup = tk.Entry(self.tree, textvariable=edit_text, font=self.config['font1'])
        self.cell_popup.place(x=x, y=mid_y, anchor='w', width=w)
        self.cell_popup.focus()
        self.master.update()

        # Position the cursor within the popup at the click. #
        relative_x = self.cell_popup.winfo_pointerx() - self.tree.winfo_rootx() - x
        self.cell_popup.icursor(self.cell_popup.index('@{}'.format(relative_x)))

        def click_off(event):
            event_x = event.x_root - self.tree.winfo_rootx()
            event_y = event.y_root - self.tree.winfo_rooty()
            if (not event_x in range(x+2, x+w-2)) or (not event_y in range(y+2, y+h-2)):
                self.cell_popup.config(takefocus=0)
                close_popup(event)

        def close_popup(event):
            self.tree.set(iid, column, edit_text.get())
            result_number = int(self.tree.set(iid, 'Result'))
            key = self.tree.heading(column)['text'].lower()
            self.search_results[result_number][key] = edit_text.get()
            self.gm.replace_entry(self.search_results[result_number])
            escape_popup(event)

        def escape_popup(event):
            self.cell_popup.destroy()
            self.master.unbind('<Button>')
            self.master.unbind('<Escape>')
            
        self.cell_popup.bind('<Return>', close_popup)
        self.cell_popup.bind('<FocusOut>', escape_popup)
        self.master.bind('<Button>', click_off)
        self.master.bind('<Escape>', escape_popup)

    def delete(self, event=None):
        """Delete a cell and delete its contents from the glossary."""
        iids = self.tree.selection()
        offset = 0
        for iid in iids:
            result_number = int(self.tree.set(iid, 'Result'))- offset
            self.gm.delete(self.search_results[result_number])
            self.search_results.pop(result_number)
            offset += 1
        self.display_results(self.search_results)

    def add(self, arg):
        """Create a dialogue for adding a row to a glossary."""
        if self.active_glossary.get() == '':
            return
        add_dialogue = tk.Toplevel(self.master)
        add_dialogue.title('Add new entry')

        # HEADERS #
        headers = ('Source', 'Translation', 'Context', 'Glossary')
        for i in range(len(headers)):
            label = tk.Label(add_dialogue, text=headers[i])
            label.grid(row=0, column=i)

        # ENTRY FIELDS #
        source_entry = tk.Entry(add_dialogue, font=self.config['font1'])
        translation_entry = tk.Entry(add_dialogue, font=self.config['font1'])
        context_entry = tk.Entry(add_dialogue, font=self.config['font1'])

        source_entry.insert(0, arg)
        translation_entry.focus_set()

        # GLOSSARY DROPDOWN #
        glossary_button = tk.Menubutton(
            add_dialogue
            , textvariable=self.active_glossary
            , font=self.config['font1']
            , bg='#fff'
            , activebackground='#fff'
            , relief='sunken'
            , width='20'
            , anchor='w'
            , pady=1
            , padx=1
            )
        glossary_menu = tk.Menu(glossary_button, bg='#fff', tearoff=False)

        for glossary in self.gm.list_glossaries():
            glossary_menu.add_radiobutton(label=glossary, variable=self.active_glossary, value=glossary)
        glossary_button.configure(menu=glossary_menu)

        second_row = [source_entry, translation_entry, context_entry, glossary_button]
        for i in range(len(second_row)):
            second_row[i].grid(row=1, column=i, sticky='ew', padx=1)

        def add_to_glossary():
            new_entry = OrderedDict([
                ('source', source_entry.get())
                , ('translation', translation_entry.get())
                , ('context', context_entry.get())
                 ])
            if not new_entry['source'] == '':
                self.gm.add_entry(new_entry, self.active_glossary.get())
                self.search(source_entry.get())
                add_dialogue.destroy()

        #CONFIRMATION BUTTONS #
        add_button = tk.Button(add_dialogue, text='Add', command=add_to_glossary)
        add_button.grid(row=2, column=2, sticky='ew', pady=5)
        cancel_button = tk.Button(add_dialogue, text='Cancel', command=add_dialogue.destroy)
        cancel_button.grid(row=2, column=3, sticky='ew', pady=5)
        
        add_dialogue.grab_set()
        add_dialogue.grid_rowconfigure(1, weight=1)

        add_dialogue.bind('<Return>', lambda event: add_button.invoke())
        add_dialogue.bind('<Escape>', lambda event: cancel_button.invoke())

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
        self.gm.new_glossary(filepath, filename)
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
        filename = filepath[filepath.rfind('/') + 1:]
        if filename in self.gm.list_glossaries():
            messagebox.showwarning(
            'File not imported',
            'There is already a glossary with the name {}.'.format(filename)
            )
            return
        try: self.gm.add_glossary(filepath, filename)
        except Exception as e: messagebox.showerror('Import error', str(e))
        self.display_results(self.gm.display_contents(filename))
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))

    def change_gm_path(self, event=None):
        """Create a dialog for changing the default directory of the manager."""
        new_path = filedialog.askdirectory(
            initialdir=self.config['path']
            , title='Change glossary directory'
            , mustexist=True
            )
        if new_path == '': return
        new_path = relpath(new_path)
        self.config_parser.set('USER', 'path', new_path)
        with open('config.ini', 'w', encoding='utf-8') as conf:
            self.config_parser.write(conf)
        self.setup_gm()

    def about(self, event=None):
        """Display an about box with the copyright licence."""
        about_text = str
        with open('licence.txt') as f: about_text = f.read()
        messagebox.showinfo(title='About', message=about_text)

    def save_all(self, event=None):
        """Save all changes to all glossaries."""
        saved = self.gm.save()
        if saved: self.status.set('Saved: ' + saved)

    def exit(self, event=None):
        """Exit the tkinter loop."""
        if self.gm.unsaved_changes():
            save = messagebox.askyesno(
                title='Save on close'
                , message='Save changes to glossaries before closing?'
                )
            if save:
                self.save_all()
        self.master.destroy()

    def hotkey_listen(self):
        """ Instantiate the global hotkey listener, which returns highlighted text from other
programs via the clipboard, then search for that text. """
        self.hotkey_listener = hotkeys.GlobalHotkeyListener(
            self.config['hotkey_mod']
            , self.config['hotkey_key']
            , self.config.getfloat('hotkey_sleep_time')
            , self.master
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
    listbox = GlossaryManagerGUI(root)
    root.lift()
    root.update()
    root.mainloop()

