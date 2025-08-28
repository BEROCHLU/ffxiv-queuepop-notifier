# -*- coding: utf-8 -*-
import win32gui
import win32con


if __name__ == "__main__":
    hwnd = win32gui.FindWindow(None, "FINAL FANTASY XIV")
    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    print("Set free TOPMOST")
