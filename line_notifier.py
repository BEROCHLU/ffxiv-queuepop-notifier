import configparser
import ctypes
import time
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
import pyautogui
import requests
import win32con
import win32gui

ctypes.windll.user32.SetProcessDPIAware()

SCALES = [round(0.5 + 0.1 * i, 2) for i in range(11)]  # 0.5, 0.6, ..., 1.5

URL = "https://api.line.me/v2/bot/message/push"
IMAGE_PATHS = {
    "突入": "./img/totsunyu_scale100.png",
    "commence": "./img/commence_scale100.png",
}

print_now = lambda: print(datetime.now().strftime("%F %T"))


def post_line(message: str) -> None:
    """Push send a message to LINE."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }
    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}],
    }

    r = requests.post(URL, headers=headers, json=data, timeout=6)

    if not r.ok:
        print("LINE送信エラー:", r.status_code, r.text)


def find_image(confidence: float) -> Optional[tuple[int, int]]:
    """Locates the specified image on the screen."""
    for key, path in IMAGE_PATHS.items():
        try:
            image_location = pyautogui.locateCenterOnScreen(path, confidence=confidence)
        except pyautogui.ImageNotFoundException:  # 画像が見つからなかった場合、エラーが発生する
            image_location = None

        if image_location:
            print(f"Found: {key}, x: {int(image_location.x)}, y: {int(image_location.y)}")
            return image_location

    return None


def find_image_multiscale(confidence: float) -> Optional[tuple[int, int]]:
    """Multi-scale template matching using OpenCV (fallback for resolution/scale mismatch)."""
    screen_gray = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2GRAY)
    best_score, best_key, best_scale, best_center = 0.0, None, None, None

    for key, path in IMAGE_PATHS.items():
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            continue

        for scale in SCALES:
            resized = cv2.resize(template, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w = resized.shape
            if h > screen_gray.shape[0] or w > screen_gray.shape[1]:
                continue

            result = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val > best_score:
                best_score = max_val
                best_key, best_scale = key, scale
                best_center = (max_loc[0] + w // 2, max_loc[1] + h // 2)

    if best_score >= confidence and best_center is not None:
        print(f"Found(MS): {best_key} scale={best_scale:.2f} conf={best_score:.3f}, x: {best_center[0]}, y: {best_center[1]}")
        return best_center

    return None


def set_foreground_window(hwnd: int) -> None:
    """Sets the specified window to the foreground."""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # To avoid error, send unuseless key to a window before SetForegroundWindow
    pyautogui.press("altleft")
    win32gui.SetForegroundWindow(hwnd)
    # ctypes.windll.user32.SetForegroundWindow(hwnd)


def set_topmost_once(hwnd: int, flags: int) -> None:
    """Restore if minimized, force topmost once, then unset and focus."""
    # 最小化されていたら復元
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # 強制的に最前面化
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
    # 強制最前面化解除
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    # フォーカスを設定
    win32gui.SetForegroundWindow(hwnd)


def set_topmost(hwnd: int, flags: int) -> None:
    """Restore if minimized, keep window always on top, and focus."""
    # 最小化されていたら復元
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # 強制的に最前面化
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
    # フォーカスを設定
    win32gui.SetForegroundWindow(hwnd)


if __name__ == "__main__":
    print_now()
    hwnd = None
    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE

    try:
        cfg = configparser.ConfigParser()
        cfg.read("config.ini")

        ACCESS_TOKEN = cfg.get("LINE", "ACCESS_TOKEN")
        USER_ID = cfg.get("LINE", "USER_ID")
        WINDOW_TITLE = cfg.get("LINE", "WINDOW_TITLE")
        TOPMOST = cfg.getboolean("LINE", "TOPMOST")
        INTERVAL_SEC = cfg.getfloat("LINE", "INTERVAL_SEC")
        CONFIDENCE = cfg.getfloat("LINE", "CONFIDENCE")

        imageFound = None
        hwnd = win32gui.FindWindow(None, WINDOW_TITLE)

        if not hwnd:
            raise RuntimeError(f"ウィンドウが見つかりません: {WINDOW_TITLE}")

        if TOPMOST:
            set_topmost(hwnd, flags)
        else:
            # 正常に動かない場合、set_topmost_once()に切り替える
            set_foreground_window(hwnd)
            # set_topmost_once(hwnd, flags)

        while not imageFound:
            time.sleep(INTERVAL_SEC)
            imageFound = find_image(CONFIDENCE) or find_image_multiscale(CONFIDENCE)

        post_line("Commence!⚔️")
    except KeyboardInterrupt:
        print("\n key interrupted")
    finally:
        if TOPMOST and hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
        print_now()
