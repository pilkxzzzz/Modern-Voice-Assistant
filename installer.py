import sys
import os
from cx_Freeze import setup, Executable

# Залежності, які потрібно включити
build_exe_options = {
    "packages": [
        "speech_recognition",
        "pyttsx3", 
        "datetime",
        "webbrowser",
        "customtkinter",
        "math",
        "os",
        "subprocess",
        "winshell",
        "threading",
        "time",
        "pyautogui",
        "keyboard",
        "json",
        "random",
        "difflib"
    ],
    "include_files": [
        # Додайте сюди всі додаткові файли, які потрібні програмі
        "saved_commands.json",
        # Можна додати іконку, картинки тощо
        "icon.ico"  # якщо у вас є іконка
    ]
}

# Створюємо виконуваний файл
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Voice Assistant",
    version="1.0",
    description="Modern Voice Assistant",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "voice_assistant.py",
            base=base,
            icon="icon.ico",  # якщо у вас є іконка
            shortcut_name="Voice Assistant",
            shortcut_dir="DesktopFolder"
        )
    ]
) 