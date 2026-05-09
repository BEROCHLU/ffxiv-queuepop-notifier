import configparser
import ctypes
import logging
import time
from typing import Optional

import cv2
import numpy as np
import pyautogui
import requests
import win32con
import win32gui

URL = "https://api.line.me/v2/bot/message/push"
IMAGE_PATHS = {
    "突入": "./img/totsunyu_scale100.png",
    "commence": "./img/commence_scale100.png",
}
# マルチスケール候補 (0.6, 0.7, ..., 1.4)
SCALES = [round(0.6 + 0.1 * i, 2) for i in range(9)]
REQUEST_TIMEOUT = 10


def post_line(message: str, access_token: str, user_id: str) -> None:
    """LINE にメッセージをプッシュ送信。"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    try:
        r = requests.post(URL, headers=headers, json=data, timeout=REQUEST_TIMEOUT)
        if not r.ok:
            logging.error("LINE送信エラー: %s %s", r.status_code, r.text)
    except requests.exceptions.RequestException as e:
        logging.error("LINE送信失敗: %s", e)


def load_cache() -> dict[str, np.ndarray]:
    """起動時に一度だけテンプレート画像を読み込んでキャッシュする。"""
    cache_image: dict[str, np.ndarray] = {}
    for key, path in IMAGE_PATHS.items():
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            logging.warning("テンプレート読込失敗: %s", path)
            continue
        cache_image[key] = img
    return cache_image


def find_image_multiscale(cache_image: dict[str, np.ndarray], confidence: float) -> bool:
    """Multi-scale template matching using OpenCV (fallback for resolution/scale mismatch)."""
    screenshot = pyautogui.screenshot()
    screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    for key, cache in cache_image.items():
        for scale in SCALES:
            resized = cv2.resize(cache, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w = resized.shape[:2]  # (h, w, 3) の先頭2つだけ取る
            if h > screen_bgr.shape[0] or w > screen_bgr.shape[1]:
                continue

            result = cv2.matchTemplate(screen_bgr, resized, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                center_loc = (max_loc[0] + w // 2, max_loc[1] + h // 2)
                logging.info(
                    f"Found: {key} scale: {scale:.2f} score: {max_val:.2f}  x: {center_loc[0]}, y: {center_loc[1]}"
                )
                return True

    return False


def set_foreground_window(hwnd: int) -> None:
    """指定したウィンドウを前面にする。"""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    # SetForegroundWindow の実行前に無害なキー入力を送るとエラーを避けやすい
    pyautogui.press("altleft")
    win32gui.SetForegroundWindow(hwnd)


def set_topmost_once(hwnd: int, flags: int) -> None:
    """最前面化を一度だけ強制してから解除しフォーカス。"""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    win32gui.SetForegroundWindow(hwnd)


def set_topmost(hwnd: int, flags: int) -> None:
    """ウィンドウを最前面に固定してフォーカス。"""
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, flags)
    win32gui.SetForegroundWindow(hwnd)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
    logging.info("起動")

    hwnd = 0
    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
    topmost = False

    try:
        cfg = configparser.ConfigParser()
        cfg.read("config.ini")

        access_token = cfg.get("LINE", "ACCESS_TOKEN")
        user_id = cfg.get("LINE", "USER_ID")
        window_title = cfg.get("LINE", "WINDOW_TITLE")
        topmost = cfg.getboolean("LINE", "TOPMOST")
        interval_sec = cfg.getfloat("LINE", "INTERVAL_SEC")
        confidence = cfg.getfloat("LINE", "CONFIDENCE")

        cache_image = load_cache()
        if not cache_image:
            raise RuntimeError("有効なテンプレート画像がありません")

        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            raise RuntimeError(f"ウィンドウが見つかりません: {window_title}")

        if topmost:
            set_topmost(hwnd, flags)
        else:
            # 正常に動かない場合は set_topmost_once(hwnd, flags) に切り替え
            set_foreground_window(hwnd)

        while True:
            time.sleep(interval_sec)
            if find_image_multiscale(cache_image, confidence):
                break

        post_line("Commence!⚔️", access_token, user_id)

    except KeyboardInterrupt:
        logging.info("キー割り込み")
    except Exception as e:
        logging.exception("エラー発生: %s", e)
    finally:
        if topmost and hwnd:
            win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, flags)
        logging.info("終了")


if __name__ == "__main__":
    main()
