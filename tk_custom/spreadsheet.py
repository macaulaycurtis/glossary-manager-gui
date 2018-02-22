import tkinter as tk
from tkinter import ttk

class Spreadsheet(tk.Frame):

    def __init__(self, parent, gm, config):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.gm = gm
        self.config = config
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._create_treeview()
        self._create_scrollbars()
        self._setup_context_menus()

    def _create_treeview(self):
        column_headings = ['Source', 'Translation', 'Context', 'Glossary', 'Result']
        displayed_columns = ['Source', 'Translation', 'Context', 'Glossary']
        self.tree = ttk.Treeview(columns=column_headings, displaycolumns=displayed_columns, show='headings')
        for c in displayed_columns:
            self.tree.heading(c, text=c)
            self.tree.column(c,minwidth=100)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self)
        ttk.Style().configure('Treeview', font=self.config['font1'])
        ttk.Style().configure('Treeview.Heading', font=self.config['font2'])

    def _create_scrollbars(self):
        vertical_scroll = ttk.Scrollbar(orient='vertical', command=self.tree.yview)
        horizontal_scroll = ttk.Scrollbar(orient='horizontal', command=self.tree.xview)
        vertical_scroll.grid(column=1, row=0, sticky='ns', in_=self)
        horizontal_scroll.grid(column=0, row=1, sticky='ew', in_=self)
        self.tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

    def _setup_context_menus(self):
        self.cell_context_menu = tk.Menu(tearoff=0)
        self.cell_context_menu.add_command(label='Edit', command=self.edit)
        self.cell_context_menu.add_command(label='Delete', command=self.delete)

        self.tree.bind('<Button-3>', self.context_menu)
        self.tree.bind('<Double-Button-1>', self.double_click_action)
        self.tree.bind('<Delete>', self.delete)

    def display(self, data):
        """Display the results of a search in the ttk tree."""
        self.data = data
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.data):
            item = (r['source'], r['translation'], r['context'], r['glossary'], i)
            iid = self.tree.insert('', 'end', values=item)

    def context_menu(self, event):
        self.cell_context_menu.entryconfig(0, state='normal')
        self.cell_x = event.x_root - self.tree.winfo_rootx()
        self.cell_y = event.y_root - self.tree.winfo_rooty()
        if self.tree.identify_region(self.cell_x, self.cell_y) == 'cell':
            if not self.tree.identify_row(self.cell_y) in self.tree.selection():
                self.tree.selection_set(self.tree.identify_row(self.cell_y))
            if self.tree.identify_column(self.cell_x) == '#4':
                self.cell_context_menu.entryconfig(0, state='disabled')
            self.cell_context_menu.post(event.x_root, event.y_root)

    def double_click_action(self, event):
        self.cell_x = event.x_root - self.tree.winfo_rootx()
        self.cell_y = event.y_root - self.tree.winfo_rooty()
        if self.tree.identify_region(self.cell_x, self.cell_y) == 'cell':
            if not self.tree.identify_column(self.cell_x) == '#4':
                self.edit()

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
        self.cell_popup = tk.Entry(self.tree, textvariable=edit_text, font=self.parent.config['font1'])
        self.cell_popup.place(x=x, y=mid_y, anchor='w', width=w)
        self.cell_popup.focus()

        # Position the cursor within the popup at the click. #
        self.update()
        relative_x = self.cell_popup.winfo_pointerx() - self.tree.winfo_rootx() - x
        self.cell_popup.icursor('@{}'.format(relative_x))

        def click_off(event):
            event_x = event.x_root - self.tree.winfo_rootx()
            event_y = event.y_root - self.tree.winfo_rooty()
            if (not event_x in range(x+2, x+w-2)) or (not event_y in range(y+2, y+h-2)):
                #self.cell_popup.config(takefocus=0)
                close_popup(event)

        def close_popup(event):
            self.tree.set(iid, column, edit_text.get())
            result_number = int(self.tree.set(iid, 'Result'))
            key = self.tree.heading(column)['text'].lower()
            self.data[result_number][key] = edit_text.get()
            self.gm.replace_entry(self.data[result_number])
            escape_popup(event)

        def escape_popup(event):
            self.cell_popup.destroy()
            self.parent.unbind('<Button>')
            self.parent.unbind('<Escape>')
            
        self.cell_popup.bind('<Return>', close_popup)
        self.cell_popup.bind('<FocusOut>', escape_popup)
        self.parent.parent.bind('<Button>', click_off)
        self.parent.parent.bind('<Escape>', escape_popup)

    def delete(self, event=None):
        """Delete a cell and delete its contents from the glossary."""
        iids = self.tree.selection()
        for offset, iid in enumerate(iids):
            result_number = int(self.tree.set(iid, 'Result')) - offset
            self.gm.delete(self.data[result_number])
            self.data.pop(result_number)
        self.display(self.data)
