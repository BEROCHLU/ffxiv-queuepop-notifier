# FFXIV Queue Pop LINE Notifier

This is a Windows tool that automatically detects the "Commence" button that appears when a Duty Finder queue pops in FINAL FANTASY XIV, and sends a notification to LINE. With this, you won’t miss your queue even when you step away from the screen.

-----

## Overview 🧭

This tool continuously monitors the screen of a specified game window.  
When a pre-configured image (such as the "Commence" button) appears, it instantly sends a push notification to your designated LINE account via the LINE Messaging API.

-----

## Features ✨

  * **Automatic Screen Image Detection**: Uses `pyautogui` and `opencv-python` to detect images on the screen with high accuracy.
  * **Push Notifications to LINE**: Instantly receive queue pop notifications in LINE.
  * **Always-on-Top Window**: Optionally keep the game window always on top.
  * **Easy Configuration**: Just edit the `config.ini` file to change your access token, target window, and other settings.

-----

## Requirements 📋

  * **OS**: Windows 10/11
  * **Python**: 3.10+

-----

## Installation 🛠️

1.  **Clone or Download the Repository**

    ```bash
    git clone https://github.com/BEROCHLU/ffxiv-queuepop-notifier
    cd ffxiv-queuepop-notifier
    ```

2.  **Install Required Libraries**

    In Command Prompt or PowerShell, install all dependencies listed in `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

-----

## Usage ▶️

### 1. Preparing LINE 💬

This tool uses the **LINE Messaging API**. To receive notifications, follow these steps:

1. **Creating a LINE Official Account**

   * Create a LINE Official Account and add it as a friend.
   * Click on “Use Messaging API.”
   * Create a provider and open [LINE Developers](https://developers.line.biz/en/).

2. **Issuing a Channel Access Token**

   * Log in to the LINE Developers Console, and open the channel from the provider you created.
   * In the “Messaging API settings” tab of the channel, issue a **long-term channel access token**. You will later set this token in `config.ini`.

3. **Get Your User ID**

   * In the channel’s “Basic settings” tab, scroll down to the “Your user ID” section.
   * The string starting with `U` shown there is your User ID. You will also set this in `config.ini`.

---

### 2. Preparing Detection Images 🖼️

Save screenshots of the images you want to detect in the `img` folder.

  * By default, `totsunyu_scale100.png` and `commence_scale100.png` are configured.  
  * Depending on your monitor scaling, prepare a clear screenshot of the "Commence" button and edit the `IMAGE_PATHS` dictionary in `line_notifier.py`.

---

### 3. Editing the Configuration File ⚙️

Copy `config_sample.ini` to `config.ini` and edit it with a text editor according to your environment:

```ini
[LINE]
# Your Channel Access Token from Step 1
ACCESS_TOKEN = YOUR_CHANNEL_ACCESS_TOKEN

# Your User ID from Step 1
USER_ID = YOUR_USER_ID

# Title of the window to monitor
WINDOW_TITLE = FINAL FANTASY XIV

# Keep the window always on top (true/false)
TOPMOST = false

# Interval (seconds) between detection attempts
INTERVAL_SEC = 0.5

# Detection accuracy threshold (max 1.0)
CONFIDENCE = 0.90
```

---

### 4. Running the Script ▶️

Once settings are complete, run the script:

```bash
python line_notifier.py
```

The script will start monitoring the screen.
When the specified image is detected, a LINE notification will be sent and the script will automatically terminate.

If you want to stop monitoring manually, minimize the game window and press `Ctrl + C` in the console where the script is running.

---

### 5. Device Settings for Reliable Notifications 🔔

Check the following settings on your device to ensure you receive LINE notifications:

* Wi-Fi may cause delays, so disable Wi-Fi and use mobile data for LINE notifications.
* Allow LINE to auto-start in the background.
* Exclude LINE from battery saver restrictions.

---

### 6. Troubleshooting 🧯

Window Gets Stuck on Top

If the script terminates unexpectedly while `TOPMOST = true` is set in your `config.ini`, the game window might get stuck in an "always-on-top" state. If this happens, you can resolve it by running the included `setfree_topmost.py` script:

```bash
python setfree_topmost.py
```


## Notes 📝

* LINE Messaging API allows **up to 200 free messages per month**.
* Image detection works only on the **primary monitor** in multi-monitor setups.

---

## Disclaimer ⚠️

* This tool works on Windows only.
* This tool does not interfere with the game’s memory or files, but use it at your own risk.
  The author assumes no responsibility for any damages caused by using this tool.
* If the game client is updated and the UI changes, image recognition may fail.
  In that case, capture new images for detection.

---

## License 📄

This project is licensed under the MIT License.
