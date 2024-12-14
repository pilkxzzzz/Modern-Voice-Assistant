import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": [
        "speech_recognition",
        "pyttsx3",
        "customtkinter",
        "keyboard",
        "pyautogui",
        "winshell"
    ],
    "include_files": [
        "saved_commands.json",
        ("C:\\Windows\\System32\\Speech\\Common\\sapi.dll", "sapi.dll"),
    ],
    "include_msvcr": True,
}

setup(
    name="Voice Assistant",
    version="1.0",
    description="Modern Voice Assistant",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "voice_assistant.py",
            base="Win32GUI",
            target_name="voice_assistant.exe"
        )
    ]
) 