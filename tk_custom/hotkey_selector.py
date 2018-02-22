import tkinter as tk
from pynput.keyboard import Listener

class HotkeySelector(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self._create_widgets()
        self._setup_window()
        self._setup_bindings()
        self.hotkey_mod = None
        self.hotkey_key = None
        self.confirmed = False

    def _setup_window(self):
        self.title('Select new global hotkey')
        self.resizable(False, False)
        self.focus_set()
        self.grab_set()
        self.transient(self.parent)

    def _setup_bindings(self):
        self.bind('<Return>', lambda event: self.confirm())
        self.bind('<Escape>', lambda event: self.cancel())
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def _create_widgets(self):
        self.grid_rowconfigure(1, weight=1)
        
        instructions = tk.Label(self
                         , wraplength=350
                         , font=self.parent.config['font2']
                         , text='Click "Detect" and enter a key combination to set a new global hotkey. If you highlight a word in a different program and press the global hotkey combination, a search will automatically be performed.'
                         )
        instructions.grid(row=0, column=0, columnspan=2)

        self.result = tk.StringVar()

        self.detect_button = tk.Button(self, text='Detect', font=self.parent.config['font1'], command=self.detect)
        self.detect_button.grid(row=1, column=0, sticky='ew', padx=10, pady=5, columnspan=2)
        self.detecting_button = tk.Button(self, text='Detecting - Click to cancel', font=self.parent.config['font1'], command=self.interrupt, fg='#f00')
        self.detecting_button.grid(row=1, column=0, sticky='ew', padx=10, pady=5, columnspan=2)
        self.detect_button.lift(self.detecting_button)

        default = '{} + {}'.format(self.parent.config['hotkey_mod'], self.parent.config['hotkey_key'])
        default_label = tk.Label(self, text='Current hotkey:', font=self.parent.config['font1'])
        default_label.grid(row=2, column=0, sticky='ew', padx=5)
        default_display = tk.Label(self, text=default, font=self.parent.config['font1'], fg='#009900', bg='#fff', width=20)
        default_display.grid(row=3, column=0, sticky='ew', padx=5)
        detected_label = tk.Label(self, text='Detected:', font=self.parent.config['font1'])
        detected_label.grid(row=2, column=1, sticky='ew', padx=5)
        result_display = tk.Label(self, textvariable=self.result, font=self.parent.config['font1'], fg='#f00', bg='#fff', width=20)
        result_display.grid(row=3, column=1, sticky='ew', padx=5)


        ok_button = tk.Button(self, font=self.parent.config['font2'], text='OK', command=self.confirm)
        ok_button.grid(row=4, column=0, sticky='ew', padx=5, pady=5)
        cancel_button = tk.Button(self, font=self.parent.config['font2'], text='Cancel', command=self.cancel)
        cancel_button.grid(row=4, column=1, sticky='ew', padx=5, pady=5)

    def detect(self):
        self.detect_button.lower(self.detecting_button)
        self.hotkey_mod = None
        self.hotkey_key = None

        def on_press(key):
            if not self.hotkey_mod:
                self.hotkey_mod = str(key)
            elif not self.hotkey_key:
                self.hotkey_key = str(key)
                self.listener.stop()
                self.result.set('{} + {}'.format(self.hotkey_mod, self.hotkey_key))
                self.detect_button.lift(self.detecting_button)
        
        self.listener = Listener(on_press=on_press)
        self.listener.start()

    def interrupt(self):
        self.listener.stop()
        self.detect_button.lift(self.detecting_button)

    def confirm(self):
        self.confirmed = True
        self.destroy()

    def cancel(self):
        self.destroy()
