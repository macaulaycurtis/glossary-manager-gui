import time
import pyperclip
from pynput.keyboard import Key, Controller, Listener
import tkinter as tk

class GlobalHotkeyListener(Listener):

    def __init__(self, hotkeys, sleeptime, callback, parent=None):
        Listener.__init__(self, on_press=self.on_press, on_release=self.on_release)

        self.keyboard = Controller()
        self.parent = parent
        self.sleeptime = sleeptime
        self.callback = callback
        self.mod = hotkeys[0]
        self.key = hotkeys[1]
        
        self.mod_pressed = False
        self.key_pressed = False
        self.validated = False

    def on_press(self, key):
        if str(key) == self.mod:
            self.mod_pressed = True
        if str(key) == self.key:
            self.key_pressed = True
        if self.mod_pressed and self.key_pressed:
            self.validated = True

    def on_release(self, key):
        if str(key) == self.mod:
            self.mod_pressed = False
        if str(key) == self.key:
            self.key_pressed = False
        if self.validated and not (self.mod_pressed or self.key_pressed):
            self.validated = False
            self.get_selection()

    def get_selection(self):
        """Save clipboard, borrow it for a second to copy the highlighted text, then restore the original.
        (Only works on programs that use ctrl+c to copy.)"""
        if self.parent == None or self.parent.focus_get() == None: #Make sure the parent doesn't have focus
            original_clipboard = pyperclip.paste()
            with self.keyboard.pressed(Key.ctrl):
                self.keyboard.press('c')
                time.sleep(self.sleeptime) #Sleep to allow the program to detect the virtual keypress.
                self.keyboard.release('c')
            time.sleep(self.sleeptime) #Sleep to allow the program to respond.           
            return_value = pyperclip.paste()
            pyperclip.copy(original_clipboard)
            self.callback(return_value)
    
if __name__ == '__main__':
    ghk = GlobalHotkeyListener(('Key.ctrl_r', "'\\x1d'"), 0.05, lambda x: print(x))
    ghk.start()
