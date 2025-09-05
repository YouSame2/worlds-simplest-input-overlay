#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["pynput"]
# ///

import tkinter as tk
from threading import Thread, Lock
from pynput import keyboard
import time

FADE_DURATION = 1.0  # seconds
FADE_STEPS = 10

lock = Lock()
keys_list = []  # List of tuples: (key_text, age_step)
currently_pressed = set()  # Track keys currently held down


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def create_overlay():
    root = tk.Tk()
    root.title("Keypress Overlay")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.geometry("600x120+100+100")
    root.attributes("-alpha", 0.75)
    root.config(bg="black")
    try:
        root.attributes("-transparentcolor", "grey")
    except tk.TclError:
        pass

    label = tk.Label(root, text="", font=("Arial", 48, "bold"), fg="white", bg="black")
    label.pack(expand=True, fill="both", padx=20, pady=20)

    # --- Click and drag ---
    def start_move(event):
        root.x = event.x
        root.y = event.y

    def do_move(event):
        x = event.x_root - root.x
        y = event.y_root - root.y
        root.geometry(f"+{x}+{y}")

    root.bind("<Button-1>", start_move)
    root.bind("<B1-Motion>", do_move)

    # --- Update loop ---
    def update_label():
        while True:
            with lock:
                display_text = ""
                new_keys_list = []
                for key_text, step in keys_list:
                    factor = 1 - (step + 1) / FADE_STEPS
                    color = rgb_to_hex(255 * factor, 255 * factor, 255 * factor)
                    display_text += key_text + " "
                    if step + 1 < FADE_STEPS:
                        new_keys_list.append((key_text, step + 1))
                keys_list[:] = new_keys_list
            if display_text:
                label.config(text=display_text.strip(), fg=color)
            else:
                label.config(text="")
            time.sleep(FADE_DURATION / FADE_STEPS)

    t = Thread(target=update_label)
    t.daemon = True
    t.start()

    # --- Keyboard listener ---
    def on_press(key):
        try:
            key_str = key.char.upper()
        except AttributeError:
            key_str = str(key).replace("Key.", "").upper()
        with lock:
            if key_str not in currently_pressed:
                keys_list.append((key_str, 0))
                currently_pressed.add(key_str)

    def on_release(key):
        try:
            key_str = key.char.upper()
        except AttributeError:
            key_str = str(key).replace("Key.", "").upper()
        with lock:
            currently_pressed.discard(key_str)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.daemon = True
    listener.start()

    root.mainloop()


if __name__ == "__main__":
    create_overlay()
