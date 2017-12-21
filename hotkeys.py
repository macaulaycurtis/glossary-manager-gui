import win32con, win32gui, win32console, win32api
import ctypes, time, pyperclip
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import HasSelection

class GlobalHotkeyListener:

    def __init__(self, hwnd, m, k):
        """Register hotkey (shift + insert)"""
        mod = {'shift' : win32con.MOD_SHIFT, 'control' : win32con.MOD_CONTROL}
        key = {'insert' : 0x2D, 'f8' : 0x77}
        ctypes.windll.user32.RegisterHotKey(None, 1, mod[m], key[k])
        self.hwnd = hwnd

    def listen(self):
        """Wait for hotkey to be triggered, then get and return highlighted text. """
        msg = ctypes.wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == win32con.WM_HOTKEY:
                try: focus_hwnd = win32gui.GetForegroundWindow()
                except: focus_hwnd = None
                if focus_hwnd != self.hwnd:
                    paste = self.get_highlighted_text()
                    return paste

    def get_highlighted_text(self):
        """Save clipboard, borrow it for a second to copy the highlighted text, then restore the original.
        (Only works on programs that use ctrl+c to copy.)"""
        original_clipboard = pyperclip.paste()

        #Emulate Ctrl+C
        time.sleep(0.15) #Sleep to allow the user's fingers to leave the keys.
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        win32api.keybd_event(0x43, 0, 0, 0)
        time.sleep(0.15) #Sleep to allow the program to detect the virtual keypress.
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x43, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.15) #Sleep to allow the program to respond.
        
        search_arg = pyperclip.paste()
        pyperclip.copy(original_clipboard)
        return search_arg
    
if __name__ == '__main__':
    ghl = GlobalHotkeyListener()
    for i in range(2):
        paste = ghl.listen()
        print(paste)
    
