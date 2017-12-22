import tkinter as tk
import tkinter.ttk as ttk
from copy import copy
from configparser import ConfigParser
from glossarymanager import GlossaryManager
import hotkeys

class Glossary_Manager_GUI():
    
    def __init__(self, master):
        self.master = master
        self._setup_gm()
        self._create_input_group()
        self._create_output_group()
        self._setup_window()

        self.search_box.focus()

    def _setup_gm(self):
        self.config = ConfigParser()
        self.config.read('config.ini')
        self.config = self.config['DEFAULT']
        self.gm = GlossaryManager(self.config['path'])
        self.history = []
        self.master.bind('<Control-s>', self.save_all)

    def _create_input_group(self):
        input_group = tk.LabelFrame(self.master, text='Enter search query', font = self.config['font2'])
        input_group.pack(fill='x')
        input_group.grid_columnconfigure(0, weight=1)

        # SEARCH BOX #
        self.search_box = tk.Entry(font = self.config['font1'])
        self.search_box.grid(row=0, column=0, sticky='ew', padx=2, pady=2, in_=input_group)
        self.search_box.bind('<Return>', lambda event: search_button.invoke())
        self.search_box.bind('<Insert>', lambda event: add_button.invoke())
        search_button = tk.Button(text='Search', command=lambda *args: self.search(self.search_box.get()))
        search_button.grid(row=0, column=1, sticky='e', padx=2, pady=2, in_=input_group)

        # HISTORY DROPDOWN #
        history_button = tk.Menubutton(text='↓'
                                       , font=self.config['font2']
                                       , bg='#fff'
                                       , activebackground='#fff'
                                       , cursor='hand2'
                                       , pady=2
                                       , padx=3)
        history_button.grid(row=0, column=0, sticky='e', in_=input_group, padx=3)
        self.history_menu = tk.Menu(history_button, bg='#fff', tearoff=False)
        history_button.configure(menu=self.history_menu)

        # FILTER BUTTONS #
        filter_buttons = tk.Frame()
        filter_buttons.grid(row=1, column=0, sticky='w', in_=input_group)
        self.filters = {}
        for f in ['fuzzy', 'reverse']:
            self.filters.update({f : tk.BooleanVar()})
            self.filters[f].set(False)
            button = tk.Checkbutton(text=f.title(), padx=2, variable=self.filters[f])
            button.pack(side='left', in_=filter_buttons)

        # ADD BUTTON #
        add_button = tk.Button(text='Add', command=lambda *args: self.add(self.search_box.get()))
        add_button.grid(row=1, column=1, sticky='ew', padx=2, pady=2, in_=input_group)

    def _create_output_group(self):
        output_group = tk.LabelFrame(self.master, text="Results", font = self.config['font2'])
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

        # TREE CONTEXT MENUS #
        cell_context = tk.Menu(tearoff=0)
        cell_context.add_command(label='Edit', command=self.edit)
        cell_context.add_command(label='Delete', command=self.delete)
        
        self.cell_x = int
        self.cell_y = int
        
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
            

        # SCROLLBARS #
        vertical_scroll = ttk.Scrollbar(orient='vertical', command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(orient='horizontal', command=self.tree.xview)
        vertical_scroll.grid(column=1, row=0, sticky='ns', in_=output_group)
        horizontal_scroll.grid(column=0, row=1, sticky='ew', in_=output_group)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)
        
        # STATUS BAR #
        self.status = tk.StringVar()
        self.status.set('Loaded glossaries: {}'.format('; '.join(self.gm.list_glossaries())))
        status_bar = tk.Label(textvariable=self.status
                                   , font=self.config['font2']
                                   , justify='left'
                                   , anchor='w')
        status_bar.bind('<Configure>', lambda event: status_bar.configure(wraplength=event.width))
        status_bar.grid(column=0, row=2, sticky='ew', in_=output_group)

        # SIZE GRIP #
        size_grip = ttk.Sizegrip()
        size_grip.grid(column=1, row=2, sticky='se', in_= output_group)

    def _setup_window(self):
        self.master.title(self.config['title'])
        self.master.minsize(self.config['minimum_x'], self.config['minimum_y'])
        if self.config.getboolean('start_minimized'):
            self.master.iconify()
        self.master.update()

    def search(self, arg='', fuzzy=0.0, column='source'):
        """ Search for a keyword.
         Returns search results in the format OrderedDict([{source, translation, context, glossary, index, ratio}]) """
        if arg == '': return
        self.history_menu.add_command(label=arg, command=lambda *args: (self.search_box.delete(0, tk.END),
                                                                self.search_box.insert(0, arg) ))
        if self.filters['fuzzy'].get(): fuzzy = self.config.getfloat('minimum_match')
        if self.filters['reverse'].get(): column = 'translation'
        self.search_results = self.gm.search(arg, fuzzy, column)
        if len(self.search_results) == 0: self.status.set('No results found.')
        else: self.status.set('Found {} results.'.format(len(self.search_results)))
        self.display_results()

    def display_results(self):
        self.tree.delete(*self.tree.get_children())
        i = 0
        for r in self.search_results:
            item = (r['source'], r['translation'], r['context'], r['glossary'], i)
            iid = self.tree.insert('', 'end', values=item)
            i += 1

    def edit(self, *args):
        column = self.tree.identify_column(self.cell_x)
        iid = self.tree.identify_row(self.cell_y)
        x,y,w,h = self.tree.bbox(iid, column)
        mid_y = int(y + h / 2)
        edit_text = tk.StringVar()
        edit_text.set(self.tree.set(iid, column))
        self.cell_popup = tk.Entry(self.tree, textvariable=edit_text, font=self.config['font1'])
        self.cell_popup.place(x=x, y=mid_y, anchor='w', width=w)
        self.cell_popup.focus()
        self.master.update()
        relative_x = self.cell_popup.winfo_pointerx() - self.tree.winfo_rootx() - x
        self.cell_popup.icursor(self.cell_popup.index('@{}'.format(relative_x)))

        def close_popup(event):
            self.tree.set(iid, column, edit_text.get())
            result_number = int(self.tree.set(iid, 'Result'))
            key = self.tree.heading(column)['text'].lower()
            self.search_results[result_number][key] = edit_text.get()
            self.gm.replace_entry(self.search_results[result_number])
            self.cell_popup.destroy()
            self.master.unbind('<Button>')
            self.master.unbind('<Escape>')

        def escape_popup(event):
            self.cell_popup.destroy()
            self.master.unbind('<Button>')
            self.master.unbind('<Escape>')

        def click_off(event):
            event_x = event.x_root - self.tree.winfo_rootx()
            event_y = event.y_root - self.tree.winfo_rooty()
            if (not event_x in range(x+2, x+w-2)) or (not event_y in range(y+2, y+h-2)):
                self.cell_popup.config(takefocus=0)
                close_popup(event)
            
        self.cell_popup.bind('<Return>', close_popup)
        self.cell_popup.bind('<FocusOut>', escape_popup)
        self.master.bind('<Button>', click_off)
        self.master.bind('<Escape>', escape_popup)

    def delete(self, *args):
        iids = self.tree.selection()
        offset = 0
        for iid in iids:
            result_number = int(self.tree.set(iid, 'Result'))- offset
            self.gm.delete(self.search_results[result_number])
            self.search_results.pop(result_number)
            offset += 1
        self.display_results()

    def add(self, arg):
        add_dialogue = tk.Toplevel(self.master)
        add_dialogue.title('Add new entry')
        add_dialogue.transient(self.master)
        
        label = tk.Label(add_dialogue, text=arg)
        label.grid(row=0, column=0)
        
        add_dialogue.grab_set()
        add_dialogue.grid_rowconfigure(1, weight=1)
        

    def save_all(self, event):
        saved = self.gm.save()
        if saved: self.status.set('Saved: ' + saved)
        else: pass

    def hotkey_listen(self):
        """ Instantiate the global hotkey listener, which returns highlighted text from other
       programs via the clipboard, then search for that text. """
        hotkey_listener = hotkeys.GlobalHotkeyListener(self.master
                                                       , self.config['hotkey_mod']
                                                       , self.config['hotkey_key']
                                                       , self.config.getfloat('hotkey_sleep_time'))
        while True:
            paste = hotkey_listener.listen()
            paste = paste.strip()
            self.search_box.delete(0, tk.END)
            self.search_box.insert(0, paste)
            self.search(paste)
            self.master.deiconify()
            self.search_box.focus()

if __name__ == '__main__':
    root = tk.Tk()
    listbox = Glossary_Manager_GUI(root)
    root.lift()
    root.update()
    root.mainloop()

