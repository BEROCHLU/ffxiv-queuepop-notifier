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
# マルチスケール候補 (0.5, 0.6, ..., 1.5)
SCALES = [round(0.5 + 0.1 * i, 2) for i in range(11)]
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


def load_templates() -> dict[str, np.ndarray]:
    """起動時に一度だけテンプレート画像を読み込んでキャッシュする。"""
    templates: dict[str, np.ndarray] = {}
    for key, path in IMAGE_PATHS.items():
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            logging.warning("テンプレート読込失敗: %s", path)
            continue
        templates[key] = img
    return templates


def find_image(templates: dict[str, np.ndarray], confidence: float) -> Optional[tuple[int, int]]:
    """マルチスケールでテンプレートマッチングを行う。"""
    screenshot = pyautogui.screenshot()
    screen_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    for key, template in templates.items():
        found_score: float = 0.0
        found_loc: Optional[tuple[int, int]] = None
        found_size: Optional[tuple[int, int]] = None

        for scale in SCALES:
            tw = int(template.shape[1] * scale)
            th = int(template.shape[0] * scale)
            if tw < 5 or th < 5:
                continue
            if tw > screen_gray.shape[1] or th > screen_gray.shape[0]:
                continue

            resized = cv2.resize(template, (tw, th), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(screen_gray, resized, cv2.TM_CCOEFF_NORMED)
            _, max_score, _, max_loc = cv2.minMaxLoc(result)

            if max_score > found_score:
                found_score = max_score
                found_loc = max_loc  # type: ignore
                found_size = (tw, th)

        if found_loc and found_size and found_score >= confidence:
            cx = found_loc[0] + found_size[0] // 2
            cy = found_loc[1] + found_size[1] // 2
            logging.info("Found: %s, x: %d, y: %d, score: %.3f", key, cx, cy, found_score)
            return (cx, cy)

    return None


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


def enable_dpi_awareness() -> None:
    """Windows の DPI スケーリングに正しく対応させる。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PER_MONITOR_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            logging.warning("DPI awareness の設定に失敗しました")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    enable_dpi_awareness()
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

        templates = load_templates()
        if not templates:
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
            if find_image(templates, confidence):
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
