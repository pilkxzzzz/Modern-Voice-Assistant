import speech_recognition as sr
import pyttsx3
from datetime import datetime
import webbrowser
import customtkinter as ctk
import math
import os
import subprocess
import winshell
import threading
import time
import pyautogui
import keyboard
import json
import os.path
import random
import difflib

class KeyboardController:
    @staticmethod
    def press_hotkey(*args):
        """Безпечне натискання комбінації клавіш"""
        try:
            # Натискаємо всі клавіші
            for key in args:
                keyboard.press(key)
            time.sleep(0.1)  # Невелика затримка
            # Відпускаємо в зворотному порядку
            for key in reversed(args):
                keyboard.release(key)
            time.sleep(0.1)  # Затримка після відпускання
        except Exception as e:
            print(f"Помилка при натисканні клавіш: {e}")

    @staticmethod
    def type_text(text):
        """Безпечний ввід тексту"""
        try:
            keyboard.write(text)
        except Exception as e:
            print(f"Помилка при вводі тексту: {e}")

class ModernVoiceAssistant:
    def __init__(self):
        # Налаштування вікна
        self.window = ctk.CTk()
        self.window.title("Voice Assistant")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        self.window.attributes('-alpha', 0.95)  # Напівпрозорість вікна
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Додаємо стилі для анімацій
        self.button_hover_color = "#1f538d"
        self.button_normal_color = "#1f408d"
        self.animation_duration = 300  # мс
        
        # Ініціалізація компонентів розпізнавання
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.is_dictating = False
        
        # Налаштування української мови та голосу
        voices = self.engine.getProperty('voices')
        ukrainian_voice = None
        russian_voice = None
        
        # Шукаємо український або російський голос
        for voice in voices:
            if 'ukrainian' in voice.name.lower():
                ukrainian_voice = voice.id
                break
            elif 'russian' in voice.name.lower():
                russian_voice = voice.id
        
        # Встановлюємо знайдений голос
        if ukrainian_voice:
            self.engine.setProperty('voice', ukrainian_voice)
        elif russian_voice:
            self.engine.setProperty('voice', russian_voice)
        
        # Налаштування швидкості та гучності
        self.engine.setProperty('rate', 150)     # Зменшуємо швидкість для кращого розуміння
        self.engine.setProperty('volume', 1.0)   # Максимальна гучність
        
        # Шлях до файлу з командами
        self.commands_file = "saved_commands.json"
        
        # Оновлені стилі для кнопок
        self.button_style = {
            "fg_color": "#2B2B2B",          # Темний фон
            "hover_color": "#3B3B3B",       # Світліший фон при наведенні
            "text_color": "#FFFFFF",         # Білий текст
            "border_color": "#404040",       # Колір рамки
            "border_width": 2,               # Товщина рамки
            "corner_radius": 10,             # Заокруглення кутів
            "height": 40,                    # Висота кнопки
            "font": ("Helvetica", 14)        # Шрифт
        }
        
        self.setup_ui()
        self.setup_commands()
        # Завантажуємо збережені команди
        self.load_commands()

    def setup_ui(self):
        # Головний контейнер з прозорістю
        self.main_frame = ctk.CTkFrame(
            self.window,
            fg_color=("#E0E0E0", "#1E1E1E")  # Світла і темна тема
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Заголовок з ефектом світіння
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Голосовий Асистент",
            font=("Helvetica", 24, "bold"),
            text_color=("#000000", "#FFFFFF")  # Чорний для світлої теми, білий для темної
        )
        self.title_label.pack(pady=20)
        
        # Анімована кнопка прослуховування
        self.listen_button = AnimatedButton(
            self.main_frame,
            text="Почати прослуховування",
            command=self.toggle_listening,
            width=200,
            **self.button_style
        )
        self.listen_button.pack(pady=20)
        
        # Статус з анімацією переходу
        self.status_label = AnimatedLabel(
            self.main_frame,
            text="Очікую команди...",
            font=("Helvetica", 14)
        )
        self.status_label.pack(pady=10)
        
        # Покращений індикатор активності
        self.activity_indicator = ctk.CTkProgressBar(
            self.main_frame,
            width=400,
            mode="indeterminate",
            progress_color=self.button_hover_color,
            corner_radius=10
        )
        self.activity_indicator.pack(pady=10)
        self.activity_indicator.set(0)
        
        # Анімовані кнопки меню
        self.commands_button = AnimatedButton(
            self.main_frame,
            text="Показати команди",
            command=self.show_commands_window,
            width=200,
            **self.button_style
        )
        self.commands_button.pack(pady=10)
        
        self.theme_button = AnimatedButton(
            self.main_frame,
            text="Змінити тему",
            command=self.show_theme_window,
            width=200,
            **self.button_style
        )
        self.theme_button.pack(pady=10)

    def setup_commands(self):
        kb = KeyboardController()
        
        # Оновлюємо словник з базовими запитаннями та відповідями
        self.qa_dict = {
            "привіт": ["Привіт! Чим можу допомогти?", "Доброго дня! Я вас слухаю!", "Вітаю! Готовий допомогти!"],
            "як справи": ["У мене все чудово! Готовий вам допомагати!", "Дякую, що питаєте. Все добре!", "Працюю в штатному режимі!"],
            "як тебе звати": "Мене звати Голосовий Помічник. Я створений щоб допомагати вам з різними завданнями.",
            "що ти вмієш": "Я можу виконувати різні команди: відкривати програми та сайти, керувати системою, шукати інформацію та відповідати на запитання.",
            "котра година": self.tell_time,
            "яка дата": lambda: self.speak(f"Сьогодні {datetime.now().strftime('%d %B %Y')} року"),
            "який день": lambda: self.speak(f"Сьогодні {datetime.now().strftime('%A')}"),
            "хто тебе створив": "Мене створили як проект голосового помічника для допомоги користувачам.",
            "дякую": ["Будь ласка! Радий допомогти!", "Звертайтесь ще!", "Завжди радий допомогти!"],
            "бувай": ["До побачення! Гарного дня!", "До зустрічі! Буду радий допомогти знову!", "Бувайте! Звертайтесь ще!"],
            "що робиш": ["Очікую ваших команд та готовий допомагати!", "Завжди готовий до роботи!", "Чекаю на ваші завдання!"],
            "розкажи жарт": [
                "Чому програмісти плутають Хеловін і Різдво? Тому що 31 Oct дорівнює 25 Dec!",
                "Заходить програміст в ліфт, а його питають: Вверх? А він відповідає: True!",
                "Два байти зустрічаються. Перший питає: У тебе біт не позичений?",
                "Що каже програміст коли фотографується? Сиииир... JSON!",
            ],
            "допомога": "Скажіть 'показати команди' щоб побачити список доступних команд.",
        }

        # Додаємо всі інші команди як раніше
        self.commands = {
            # Існуючі команди
            ("час", "година"): self.tell_time,
            ("відкрий браузер", "гугл"): lambda: webbrowser.open("http://google.com"),
            ("ютуб", "youtube"): lambda: webbrowser.open("https://youtube.com"),
            ("soundcloud", "саундклауд"): lambda: webbrowser.open("https://soundcloud.com"),
            ("телеграм", "telegram"): lambda: self.open_program("telegram.exe"),
            ("очисти кошик", "спорожни кошик"): self.clear_recycle_bin,
            ("командний рядок", "термінал"): lambda: subprocess.Popen("cmd.exe"),
            ("пауза", "зупинись"): self.stop_listening,
            ("нотатки", "блокнот"): lambda: self.open_program("notepad.exe"),
            ("калькулятор"): lambda: self.open_program("calc.exe"),
            
            # Медіа команди (виправлені)
            ("пауза музики", "зупини музику"): 
                lambda: keyboard.send('play/pause media'),  # Використовуємо keyboard.send замість press_hotkey
            ("наступний трек", "наступна пісня"): 
                lambda: keyboard.send('next track'),  # Правильна назва клавіші
            ("попередній трек", "попередня пісня"): 
                lambda: keyboard.send('previous track'),  # Правильна назва клавіші
            ("вимкнути звук", "без звуку"): 
                lambda: keyboard.send('volume mute'),  # Правильна назва клавіші
            ("гучність більше", "збільш звук"): 
                lambda: keyboard.send('volume up'),  # Використовуємо volume up
            ("гучність менше", "зменш звук"): 
                lambda: keyboard.send('volume down'),  # Використовуємо volume down
            
            # Системні команди
            ("перезавантаження", "рестарт"): self.restart_computer,
            ("вимкнути комп'ютер", "shutdown"): self.shutdown_computer,
            ("сон", "режим сну"): lambda: os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0"),
            ("заблокувати", "блокування"): lambda: os.system("rundll32.exe user32.dll,LockWorkStation"),
            
            # Команди вікон (виправлені)
            ("закрити вікно", "закрий вікно", "закрити", "закрий"): 
                lambda: kb.press_hotkey('alt', 'f4'),
            
            ("згорнути вікно", "згорни вікно", "згорнути", "згорни"): 
                lambda: kb.press_hotkey('win', 'down'),
            
            ("розгорнути вікно", "розгорни вікно", "розгорнути", "розгорни"): 
                lambda: kb.press_hotkey('win', 'up'),
            
            ("згорнути все", "мінімізувати все"): 
                lambda: kb.press_hotkey('win', 'm'),  # win+m для згортання всіх вікон
            
            ("розгорнути все", "розгорнути всі вікна", "відновити все"): 
                lambda: kb.press_hotkey('win', 'shift', 'm'),
            
            ("перемкнути вікно", "перемкнути", "альт таб"): 
                lambda: kb.press_hotkey('alt', 'tab'),
            
            ("показати робочий стіл", "робочий стіл", "згорнути всі вікна"): 
                lambda: kb.press_hotkey('win', 'd'),  # Використовуємо win+d для показу робочого столу
                
            ("закріпити вікно", "закріпити"): 
                lambda: [kb.press_hotkey('win', 'up'), time.sleep(0.1), kb.press_hotkey('win', 'up')],
                
            ("відкріпити вікно", "відкріпити"): 
                lambda: [kb.press_hotkey('win', 'down'), time.sleep(0.1), kb.press_hotkey('win', 'down')],
                
            ("перемістити вліво", "вліво"): 
                lambda: kb.press_hotkey('win', 'left'),
                
            ("перемістити вправо", "вправо"): 
                lambda: kb.press_hotkey('win', 'right'),
            
            # Програми та сайти
            ("скайп", "skype"): lambda: self.open_program("skype.exe"),
            ("вайбер", "viber"): lambda: self.open_program("viber.exe"),
            ("ворд", "word"): lambda: self.open_program("winword.exe"),
            ("ексель", "excel"): lambda: self.open_program("excel.exe"),
            ("пошта", "outlook"): lambda: self.open_program("outlook.exe"),
            ("фотошоп", "photoshop"): lambda: self.open_program("photoshop.exe"),
            ("paint", "пйнт"): lambda: self.open_program("mspaint.exe"),
            ("spotify", "спотіфай"): lambda: self.open_program("spotify.exe"),
            
            # Веб-сайти
            ("фейсбук", "facebook"): lambda: webbrowser.open("https://facebook.com"),
            ("інстаграм", "instagram"): lambda: webbrowser.open("https://instagram.com"),
            ("тіттер", "twitter"): lambda: webbrowser.open("https://twitter.com"),
            ("лінкедін", "linkedin"): lambda: webbrowser.open("https://linkedin.com"),
            ("гітхаб", "github"): lambda: webbrowser.open("https://github.com"),
            ("новини"): lambda: webbrowser.open("https://news.google.com"),
            
            # Утиліти
            ("скріншот", "знімок екрану"): lambda: pyautogui.screenshot(f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"),
            ("пошук", "знайти"): self.web_search,
            ("погода"): lambda: webbrowser.open("https://weather.com"),
            ("перекладач", "translate"): lambda: webbrowser.open("https://translate.google.com"),
            ("карти", "maps"): lambda: webbrowser.open("https://maps.google.com"),
            
            # Розважальні
            ("музика", "music"): lambda: webbrowser.open("https://music.youtube.com"),
            ("фільми", "movies"): lambda: webbrowser.open("https://netflix.com"),
            ("ігри", "games"): lambda: self.open_program("steam.exe"),
            ("твіч", "twitch"): lambda: webbrowser.open("https://twitch.tv"),
            
            # Робочі інструменти
            ("код", "visual studio code"): lambda: self.open_program("code.exe"),
            ("діскорд", "discord"): lambda: self.open_program("discord.exe"),
            ("зум", "zoom"): lambda: self.open_program("zoom.exe"),
            ("slack", "слак"): lambda: self.open_program("slack.exe"),
            ("notion"): lambda: webbrowser.open("https://notion.so"),
            ("trello", "трелло"): lambda: webbrowser.open("https://trello.com"),
            
            # Додаткові корисні комбінації
            ("копіювати", "копія"): 
                lambda: kb.press_hotkey('ctrl', 'c'),
            
            ("вставити", "вставка"): 
                lambda: kb.press_hotkey('ctrl', 'v'),
            
            ("вирізати"): 
                lambda: kb.press_hotkey('ctrl', 'x'),
            
            ("відмінити", "назад"): 
                lambda: kb.press_hotkey('ctrl', 'z'),
            
            ("повторити", "вперед"): 
                lambda: kb.press_hotkey('ctrl', 'y'),
            
            ("зберегти"): 
                lambda: kb.press_hotkey('ctrl', 's'),
            
            ("виділити все"): 
                lambda: kb.press_hotkey('ctrl', 'a'),
            
            ("оновити", "оновити сторінку"): 
                lambda: kb.press_hotkey('f5'),
            
            ("пошук на сторінці"): 
                lambda: kb.press_hotkey('ctrl', 'f'),
            
            # Браузери
            ("відкрий хром", "запусти хром", "хром", "chrome"): lambda: self.open_program("chrome.exe"),
            ("відкрий браузер", "браузер"): lambda: self.open_program("chrome.exe"),
            ("відкрий файрфокс", "firefox", "файрфокс"): lambda: self.open_program("firefox.exe"),
            ("відкрий едж", "edge", "едж"): lambda: self.open_program("msedge.exe"),
        }

    def run(self):
        self.window.mainloop()

    def web_search(self, query):
        """Пошук в інтернеті через браузер за замовчуванням"""
        try:
            # Кодуємо пошуковий запит для URL
            encoded_query = query.replace(' ', '+')
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            # Відкриваємо браузер за замовчуванням
            webbrowser.open(search_url)
            self.speak(f"Шукаю {query}")
        except Exception as e:
            self.speak("Виникла помилка при відкритті браузера")
            print(f"Error: {e}")

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def tell_time(self):
        current_time = datetime.now().strftime("%H:%M")
        self.speak(f"Зараз {current_time}")

    def clear_recycle_bin(self):
        self.speak("Очищую кошик")
        winshell.recycle_bin().empty(confirm=False)
        self.speak("Кошик очищено")

    def open_program(self, program_path):
        """Відкриття програми за повнім шляхом або назвою"""
        try:
            # Словник відомих програм та їх можливих шляхів
            known_programs = {
                "telegram.exe": [
                    r"C:\Program Files\Telegram Desktop\Telegram.exe",
                    r"C:\Users\{}\AppData\Roaming\Telegram Desktop\Telegram.exe".format(os.getenv('USERNAME')),
                    r"D:\Telegram Desktop\Telegram.exe"
                ],
                "chrome.exe": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
                    r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
                ],
                "firefox.exe": [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
                ],
                "steam.exe": [
                    r"C:\Program Files (x86)\Steam\Steam.exe",
                    r"D:\Steam\Steam.exe"
                ],
                "discord.exe": [
                    r"C:\Users\{}\AppData\Local\Discord\app-1.0.9004\Discord.exe".format(os.getenv('USERNAME')),
                    r"C:\Users\{}\AppData\Local\Discord\Update.exe".format(os.getenv('USERNAME'))
                ],
                "code.exe": [
                    r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(os.getenv('USERNAME')),
                    r"C:\Program Files\Microsoft VS Code\Code.exe"
                ]
            }

            # Спочатку перевіряємо прямий шлях
            if os.path.exists(program_path):
                subprocess.Popen(program_path)
                self.speak(f"Відкриваю програму")
                return

            # Отримуємо ім'я файлу з шляху
            program_name = os.path.basename(program_path).lower()

            # Перевіряємо відомі програми
            if program_name in known_programs:
                for path in known_programs[program_name]:
                    if os.path.exists(path):
                        subprocess.Popen(path)
                        self.speak(f"Відкриваю програму")
                        return

            # Шукаємо в системних директоріях
            system_paths = [
                os.environ.get('PROGRAMFILES', ''),
                os.environ.get('PROGRAMFILES(X86)', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('APPDATA', ''),
                r"C:\Windows\System32",
                r"C:\Windows",
            ]

            # Додаємо шляхи з PATH
            system_paths.extend(os.environ.get('PATH', '').split(';'))

            # Шукаємо програму в системних директоріях
            for directory in system_paths:
                if directory and os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            if file.lower() == program_name:
                                full_path = os.path.join(root, file)
                                subprocess.Popen(full_path)
                                self.speak(f"Відкриваю програму")
                                return

            # Якщо програму не знайдено, пробуємо запустити через cmd
            try:
                subprocess.Popen(program_name, shell=True)
                self.speak(f"Відкриваю програму")
                return
            except:
                pass

            self.speak(f"Не вдалося знайти програму. Перевірте, чи вона встановлена")

        except Exception as e:
            self.speak("Виникла помилка при запуску програми")
            print(f"Error: {e}")

    def stop_listening(self):
        """Зупиняє прослуховування"""
        self.is_listening = False
        self.listen_button.configure(text="Почати прослуховування")
        self.status_label.configure(text="Прослуховування зупинено")
        self.activity_indicator.stop()

    def change_volume(self, action):
        """Керування гучністю"""
        if action == '+':
            pyautogui.press('volumeup', 5)
            self.speak("Гучність збільшено")
        elif action == '-':
            pyautogui.press('volumedown', 5)
            self.speak("Гучність зменшено")
        elif action == 'mute':
            pyautogui.press('volumemute')
            self.speak("Звук вимкнено")

    def restart_computer(self):
        """Перезавантаження комп'ютера"""
        self.speak("Перезавантаження комп'ютера через 10 секунд")
        os.system("shutdown /r /t 10")

    def shutdown_computer(self):
        """Вимкнення комп'ютера"""
        self.speak("Вимкнення комп'ютера через 10 секунд")
        os.system("shutdown /s /t 10")

    def continue_listening(self):
        """Відновлює прослуховування після виконання команди"""
        if self.is_listening:
            self.status_label.configure(text="Очікую наступну команду...")
            # Запускаємо нове прослуховування в окремому потоці
            threading.Thread(target=self.listen_for_command, daemon=True).start()

    def listen_for_command(self):
        """Прослуховування команд"""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            
            while self.is_listening:
                try:
                    self.status_label.configure(text="Слухаю...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    
                    try:
                        command = self.recognizer.recognize_google(audio, language='uk-UA')
                        self.status_label.configure(text=f"Розпізнано: {command}")
                        self.process_command(command)
                        break  # Виходимо з циклу після обробки команди
                    except sr.UnknownValueError:
                        self.status_label.configure(text="Не розпізнано. Спробуйте ще раз...")
                    except sr.RequestError:
                        self.status_label.configure(text="Помилка сервісу. Спробуйте ще раз...")
                    
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    print(f"Error: {e}")
                    continue

    def toggle_listening(self):
        """Вмикає/вимикає прослуховування"""
        if not self.is_listening:
            self.is_listening = True
            self.listen_button.configure(text="Зупинити прослуховування")
            self.status_label.configure(text="Починаю слухати...")
            self.activity_indicator.start()
            # Запускаємо прослуховування в окремому потоці
            threading.Thread(target=self.listen_for_command, daemon=True).start()
        else:
            self.stop_listening()

    def show_add_command_window(self):
        """Відкриває вікно для додавання нової команди"""
        add_window = ctk.CTkToplevel(self.commands_window)
        add_window.title("Додати нову команду")
        add_window.geometry("500x500")
        add_window.resizable(False, False)
        add_window.attributes('-topmost', True)
        add_window.lift()
        add_window.focus_force()
        add_window.grab_set()
        
        # Заголовок
        title = ctk.CTkLabel(
            add_window,
            text="Додати нову команду",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=20)
        
        # Фрейм для введення команди
        command_frame = ctk.CTkFrame(add_window)
        command_frame.pack(pady=10, padx=20, fill="x")
        
        command_label = ctk.CTkLabel(
            command_frame,
            text="Фраза для активації (можна кілька через /)",
            font=("Helvetica", 12)
        )
        command_label.pack(pady=5)
        
        command_entry = ctk.CTkEntry(
            command_frame,
            placeholder_text="Наприклад: відкрий програму / запусти програму",
            width=400
        )
        command_entry.pack(pady=5)
        
        # Вибір типу дії
        action_type_frame = ctk.CTkFrame(add_window)
        action_type_frame.pack(pady=10, padx=20, fill="x")
        
        action_type_label = ctk.CTkLabel(
            action_type_frame,
            text="Виберіть тип дії:",
            font=("Helvetica", 12)
        )
        action_type_label.pack(pady=5)
        
        action_type = ctk.StringVar(value="program")
        
        types_frame = ctk.CTkFrame(action_type_frame)
        types_frame.pack(fill="x")
        
        def update_action_frame(*args):
            # Очищаємо попередній фрейм дії
            if hasattr(add_window, 'action_input_frame'):
                add_window.action_input_frame.destroy()
            
            # Ств��рюємо новий фрейм для введення дії
            add_window.action_input_frame = ctk.CTkFrame(add_window)
            add_window.action_input_frame.pack(pady=10, padx=20, fill="x")
            
            if action_type.get() == "program":
                action_label = ctk.CTkLabel(
                    add_window.action_input_frame,
                    text="Шлях до програми:",
                    font=("Helvetica", 12)
                )
                action_label.pack(pady=5)
                
                action_entry = ctk.CTkEntry(
                    add_window.action_input_frame,
                    placeholder_text="Наприклад: notepad.exe або повний шлях",
                    width=400
                )
                action_entry.pack(pady=5)
                
            elif action_type.get() == "website":
                action_label = ctk.CTkLabel(
                    add_window.action_input_frame,
                    text="URL веб-сайту:",
                    font=("Helvetica", 12)
                )
                action_label.pack(pady=5)
                
                action_entry = ctk.CTkEntry(
                    add_window.action_input_frame,
                    placeholder_text="Наприклад: https://google.com",
                    width=400
                )
                action_entry.pack(pady=5)
                
            elif action_type.get() == "system":
                action_label = ctk.CTkLabel(
                    add_window.action_input_frame,
                    text="Системна команда:",
                    font=("Helvetica", 12)
                )
                action_label.pack(pady=5)
                
                action_entry = ctk.CTkEntry(
                    add_window.action_input_frame,
                    placeholder_text="Наприклад: shutdown /s /t 10",
                    width=400
                )
                action_entry.pack(pady=5)
            
            add_window.action_entry = action_entry
        
        # Радіокнопки для вибору типу
        ctk.CTkRadioButton(
            types_frame,
            text="Запуск програми",
            variable=action_type,
            value="program",
            command=update_action_frame
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            types_frame,
            text="Відкриття сайту",
            variable=action_type,
            value="website",
            command=update_action_frame
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            types_frame,
            text="Системна команда",
            variable=action_type,
            value="system",
            command=update_action_frame
        ).pack(side="left", padx=10)
        
        # Початкове створення фрейму дії
        update_action_frame()
        
        def add_new_command():
            command = command_entry.get().strip()
            action = add_window.action_entry.get().strip()
            
            if command and action:
                command_phrases = tuple(phrase.strip() for phrase in command.split('/'))
                
                # Створюємо команду відповідно до типу
                if action_type.get() == "program":
                    self.commands[command_phrases] = lambda path=action: self.open_program(path)
                    command_type = 'program'
                elif action_type.get() == "website":
                    self.commands[command_phrases] = lambda url=action: webbrowser.open(url)
                    command_type = 'website'
                elif action_type.get() == "system":
                    self.commands[command_phrases] = lambda cmd=action: os.system(cmd)
                    command_type = 'system'
                
                # Зберігаємо команду в JSON
                try:
                    commands_to_save = {}
                    if os.path.exists(self.commands_file):
                        with open(self.commands_file, 'r', encoding='utf-8') as f:
                            commands_to_save = json.load(f)
                    
                    # Додаємо нову команду
                    commands_to_save[str(command_phrases)] = {
                        'type': command_type,
                        'value': action
                    }
                    
                    # Зберігаємо оновлений словник
                    with open(self.commands_file, 'w', encoding='utf-8') as f:
                        json.dump(commands_to_save, f, ensure_ascii=False, indent=4)
                        
                except Exception as e:
                    print(f"Помилка при збереженні команди: {e}")
                
                self.speak(f"Додано нову команду")
                add_window.destroy()
                self.commands_window.destroy()
                self.show_commands_window()
            else:
                self.speak("Будь ласка, заповніть всі поля")
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(add_window)
        buttons_frame.pack(pady=20)
        
        add_button = ctk.CTkButton(
            buttons_frame,
            text="Додати",
            command=add_new_command,
            width=140
        )
        add_button.pack(side="left", padx=5)
        
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Скасувати",
            command=add_window.destroy,
            width=140
        )
        cancel_button.pack(side="left", padx=5)

    def show_commands_window(self):
        """Відкриває вікно з командами"""
        self.commands_window = ctk.CTkToplevel(self.window)
        self.commands_window.title("Команди асистента")
        self.commands_window.geometry("800x700")
        self.commands_window.resizable(False, False)
        self.commands_window.attributes('-topmost', True)
        self.commands_window.lift()
        self.commands_window.focus_force()
        
        # Фрейм для пошуку та додавання
        top_frame = ctk.CTkFrame(self.commands_window)
        top_frame.pack(pady=10, padx=20, fill="x")
        
        # Функція редагування команди
        def edit_command(cmd_key):
            edit_window = ctk.CTkToplevel(self.commands_window)
            edit_window.title("Редагування команди")
            edit_window.geometry("400x300")
            edit_window.resizable(False, False)
            edit_window.attributes('-topmost', True)
            edit_window.lift()
            edit_window.focus_force()
            edit_window.grab_set()
            
            # Фрейм для введення
            input_frame = ctk.CTkFrame(edit_window)
            input_frame.pack(pady=20, padx=20, fill="x")
            
            # Поле для команди
            command_label = ctk.CTkLabel(
                input_frame,
                text="Команда (фрази через /):",
                font=("Helvetica", 12)
            )
            command_label.pack(pady=5)
            
            command_entry = ctk.CTkEntry(
                input_frame,
                width=300,
                placeholder_text="Наприклад: відкрий програму / запусти програму"
            )
            if isinstance(cmd_key, tuple):
                command_entry.insert(0, " / ".join(cmd_key))
            else:
                command_entry.insert(0, cmd_key)
            
            command_entry.pack(pady=5)
            
            # Поле для дії
            action_label = ctk.CTkLabel(
                input_frame,
                text="Дія (шлях до програми або URL):",
                font=("Helvetica", 12)
            )
            action_label.pack(pady=5)
            
            action_entry = ctk.CTkEntry(
                input_frame,
                width=300,
                placeholder_text="Наприклад: notepad.exe або https://google.com"
            )
            
            # Отримуємо поточне значення дії
            current_action = ""
            if cmd_key in self.commands:
                action_code = str(self.commands[cmd_key].__code__.co_code)
                if hasattr(self.commands[cmd_key], '__defaults__') and self.commands[cmd_key].__defaults__:
                    current_action = self.commands[cmd_key].__defaults__[0]
            
            action_entry.insert(0, current_action)
            action_entry.pack(pady=5)
            
            def save_changes():
                new_command = command_entry.get().strip()
                new_action = action_entry.get().strip()
                
                if new_command and new_action:
                    # Видаляємо стару команду
                    if cmd_key in self.commands:
                        del self.commands[cmd_key]
                    
                    # Додаємо нову команду
                    new_key = tuple(phrase.strip() for phrase in new_command.split('/'))
                    if new_action.startswith('http'):
                        self.commands[new_key] = lambda url=new_action: webbrowser.open(url)
                    else:
                        self.commands[new_key] = lambda path=new_action: self.open_program(path)
                    
                    # Зберігаємо зміни
                    self.save_commands()
                    
                    self.speak("Команду оновлено")
                    edit_window.destroy()
                    self.commands_window.destroy()
                    self.show_commands_window()
                else:
                    self.speak("Будь ласка, заповніть обидва поля")
            
            # Кнопки
            buttons_frame = ctk.CTkFrame(edit_window)
            buttons_frame.pack(pady=20)
            
            save_button = ctk.CTkButton(
                buttons_frame,
                text="Зберегти",
                command=save_changes,
                width=140
            )
            save_button.pack(side="left", padx=5)
            
            cancel_button = ctk.CTkButton(
                buttons_frame,
                text="Скасувати",
                command=edit_window.destroy,
                width=140
            )
            cancel_button.pack(side="left", padx=5)
        
        # Функція видалення команди
        def delete_command(cmd_key):
            if cmd_key in self.commands:
                del self.commands[cmd_key]
                # Зберігаємо команду після видалння
                self.save_commands()
                self.speak("Команду видалено")
                self.commands_window.destroy()
                self.show_commands_window()
        
        # Ліва частина з пошуком
        search_frame = ctk.CTkFrame(top_frame)
        search_frame.pack(side="left", fill="x", expand=True)
        
        search_label = ctk.CTkLabel(
            search_frame,
            text="Пошук команди:",
            font=("Helvetica", 14)
        )
        search_label.pack(side="left", padx=10)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            width=300,
            placeholder_text="Введіть текст для пошуку..."
        )
        search_entry.pack(side="left", padx=10)
        
        # Створюємо фрейм для списку команд
        commands_frame = ctk.CTkScrollableFrame(
            self.commands_window,
            width=750,
            height=500
        )
        commands_frame.pack(pady=20, padx=20)
        
        def filter_commands(event=None):
            # Очищаємо фрейм зі списком команд
            for widget in commands_frame.winfo_children():
                widget.destroy()
            
            search_text = search_entry.get().lower()
            
            # Відображаємо команди
            for key_phrases, action in self.commands.items():
                if isinstance(key_phrases, tuple):
                    command_text = " / ".join(key_phrases)
                else:
                    command_text = key_phrases
                
                # Перевіряємо, чи містить команда пошуковий текст
                if search_text in command_text.lower() or not search_text:
                    command_frame = ctk.CTkFrame(commands_frame)
                    command_frame.pack(pady=5, fill="x", padx=5)
                    
                    command_label = ctk.CTkLabel(
                        command_frame,
                        text=f"• {command_text}",
                        font=("Helvetica", 12),
                        wraplength=400
                    )
                    command_label.pack(side="left", pady=5, padx=5)
                    
                    buttons_frame = ctk.CTkFrame(command_frame)
                    buttons_frame.pack(side="right", padx=5)
                    
                    edit_btn = ctk.CTkButton(
                        buttons_frame,
                        text="Редагувати",
                        command=lambda k=key_phrases: edit_command(k),
                        width=100,
                        height=30
                    )
                    edit_btn.pack(side="left", padx=2)
                    
                    delete_btn = ctk.CTkButton(
                        buttons_frame,
                        text="Видалити",
                        command=lambda k=key_phrases: delete_command(k),
                        width=100,
                        height=30,
                        fg_color="#FF4444",
                        hover_color="#DD2222"
                    )
                    delete_btn.pack(side="left", padx=2)
        
        # Кнопка очищення пошуку
        clear_button = ctk.CTkButton(
            search_frame,
            text="Очистити",
            command=lambda: (search_entry.delete(0, 'end'), filter_commands()),
            width=100
        )
        clear_button.pack(side="left", padx=10)
        
        # Права частина з кнопкою додавання
        add_button = ctk.CTkButton(
            top_frame,
            text="Додати команду",
            command=self.show_add_command_window,
            width=150,
            height=32
        )
        add_button.pack(side="right", padx=10)
        
        # Прив'язуємо функцію фільтрації до події зміни тексту
        search_entry.bind('<KeyRelease>', filter_commands)
        
        # Початкове відображення всіх команд
        filter_commands()

    def show_theme_window(self):
        """Відкриває вікно вибору теми"""
        theme_window = ctk.CTkToplevel(self.window)
        theme_window.title("Вибір теми")
        theme_window.geometry("400x500")
        theme_window.resizable(False, False)
        theme_window.attributes('-topmost', True)
        theme_window.lift()
        theme_window.focus_force()
        theme_window.grab_set()
        
        # Заголовок
        title = ctk.CTkLabel(
            theme_window,
            text="Оберіть тему",
            font=("Helvetica", 16, "bold")
        )
        title.pack(pady=20)
        
        # Фрейм для тем
        themes_frame = ctk.CTkScrollableFrame(
            theme_window,
            width=350,
            height=400
        )
        themes_frame.pack(pady=10, padx=20)
        
        # Словник тем (назва: [режим, тема])
        themes = {
            "Темна": ["dark", "blue"],
            "Світла": ["light", "blue"],
            "Синя": ["dark", "dark-blue"],
            "Зелена": ["dark", "green"],
            "Червона": ["dark", "sweetkind"]
        }
        
        def create_theme_button(theme_name, appearance, theme_style):
            def theme_action():
                ctk.set_appearance_mode(appearance)
                ctk.set_default_color_theme(theme_style)
                self.current_theme = [appearance, theme_style]
                self.window.update()
                if hasattr(self, 'commands_window') and self.commands_window.winfo_exists():
                    self.commands_window.destroy()
                    self.show_commands_window()
                theme_window.destroy()
                self.speak("Тему змінено")
            return theme_action
        
        # Створюємо кнопки для кожної теми
        for theme_name, theme_settings in themes.items():
            theme_frame = ctk.CTkFrame(themes_frame)
            theme_frame.pack(pady=5, fill="x", padx=5)
            
            # Назва теми
            theme_label = ctk.CTkLabel(
                theme_frame,
                text=theme_name,
                font=("Helvetica", 12)
            )
            theme_label.pack(side="left", padx=10)
            
            # Кнопка застосування
            apply_button = ctk.CTkButton(
                theme_frame,
                text="Застосувати",
                command=create_theme_button(theme_name, theme_settings[0], theme_settings[1]),
                width=100,
                height=30
            )
            apply_button.pack(side="right", padx=10)
        
        # Кнопка закриття
        close_button = ctk.CTkButton(
            theme_window,
            text="Закрити",
            command=theme_window.destroy,
            width=200
        )
        close_button.pack(pady=10)

    def save_commands(self):
        """Зберігає команди у JSON файл"""
        try:
            commands_to_save = {}
            
            # Завантажуємо існуючі команди, якщо файл існує
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    commands_to_save = json.load(f)
            
            # Додаємо/оновлюємо команди
            for key, action in self.commands.items():
                # Перетворюємо кортеж в рядок для збереження
                key_str = str(key)
                
                # Визначаємо тип команди та її значення
                if 'webbrowser.open' in str(action.__code__.co_code):
                    action_value = action.__defaults__[0]
                    action_type = 'website'
                elif 'self.open_program' in str(action.__code__.co_code):
                    action_value = action.__defaults__[0]
                    action_type = 'program'
                elif 'os.system' in str(action.__code__.co_code):
                    action_value = action.__defaults__[0]
                    action_type = 'system'
                else:
                    continue  # Пропускаємо вбудовані команди
                
                commands_to_save[key_str] = {
                    'type': action_type,
                    'value': action_value
                }
            
            # Зберігаємо у файл
            with open(self.commands_file, 'w', encoding='utf-8') as f:
                json.dump(commands_to_save, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Помилка при збереженні команд: {e}")

    def load_commands(self):
        """Завантажує команди з JSON файлу"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, 'r', encoding='utf-8') as f:
                    saved_commands = json.load(f)
                
                for key_str, data in saved_commands.items():
                    # Перетворюємо рядок назад у кортеж
                    key = tuple(eval(key_str))
                    
                    # Створюємо відповідну функцію
                    if data['type'] == 'website':
                        self.commands[key] = lambda url=data['value']: webbrowser.open(url)
                    elif data['type'] == 'program':
                        self.commands[key] = lambda path=data['value']: self.open_program(path)
                    elif data['type'] == 'system':
                        self.commands[key] = lambda cmd=data['value']: os.system(cmd)
                        
        except Exception as e:
            print(f"Помилка при завантаженні команд: {e}")

    def find_closest_command(self, command):
        """Знаходить найбільш схожу команду"""
        best_ratio = 0
        best_match = None
        
        # Перевіряємо запитання
        for question in self.qa_dict.keys():
            ratio = difflib.SequenceMatcher(None, command, question).ratio()
            if ratio > best_ratio and ratio > 0.6:  # Мінімальний поріг схожості
                best_ratio = ratio
                best_match = ("question", question)
        
        # Перевіряємо команди
        for key_phrases in self.commands.keys():
            if isinstance(key_phrases, tuple):
                for phrase in key_phrases:
                    ratio = difflib.SequenceMatcher(None, command, phrase).ratio()
                    if ratio > best_ratio and ratio > 0.6:
                        best_ratio = ratio
                        best_match = ("command", key_phrases)
            else:
                ratio = difflib.SequenceMatcher(None, command, key_phrases).ratio()
                if ratio > best_ratio and ratio > 0.6:
                    best_ratio = ratio
                    best_match = ("command", key_phrases)
        
        return best_match

    def process_command(self, command):
        """Обробка розпізнаної команди"""
        command = command.lower()
        
        # Спочатку перевіряємо чи це не запитання
        for question, answer in self.qa_dict.items():
            if question in command:
                if callable(answer):
                    answer()
                elif isinstance(answer, list):
                    self.speak(random.choice(answer))
                else:
                    self.speak(answer)
                self.continue_listening()
                return
        
        # Далі перевіряємо команди пошуку
        for search_phrase in ["пошук", "знайти"]:
            if command.startswith(search_phrase):
                search_query = command[len(search_phrase):].strip()
                if search_query:
                    self.web_search(search_query)
                    self.status_label.configure(text=f"Шукаю: {search_query}")
                    self.continue_listening()
                    return
        
        # Перевіряємо інші команди
        command_found = False
        for key_phrases, action in self.commands.items():
            if isinstance(key_phrases, tuple):
                if any(phrase in command for phrase in key_phrases):
                    try:
                        action()
                        self.status_label.configure(text=f"Виконано: {command}")
                        command_found = True
                        break
                    except Exception as e:
                        self.status_label.configure(text=f"Помилка: {str(e)}")
            else:
                if key_phrases in command:
                    try:
                        action()
                        self.status_label.configure(text=f"Виконано: {command}")
                        command_found = True
                        break
                    except Exception as e:
                        self.status_label.configure(text=f"Помилка: {str(e)}")
        
        if not command_found:
            # Шукаємо найбільш схожу команду
            closest = self.find_closest_command(command)
            if closest:
                type_, match = closest
                if type_ == "question":
                    self.speak(f"Можливо, ви мали на увазі '{match}'? Спробуйте сказати це.")
                else:
                    if isinstance(match, tuple):
                        suggestion = " або ".join(match)
                    else:
                        suggestion = match
                    self.speak(f"Можливо, ви мали на увазі '{suggestion}'? Спробуйте сказати це.")
            else:
                self.speak("Команду не розпізнано. Спробуйте ще раз.")
        
        self.continue_listening()

# Додаємо нові класи для анімованих елементів
class AnimatedButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        # Встановлюємо стандартні стилі, якщо не вказано інше
        kwargs.setdefault("fg_color", "#2B2B2B")
        kwargs.setdefault("hover_color", "#3B3B3B")
        kwargs.setdefault("text_color", "#FFFFFF")
        kwargs.setdefault("border_color", "#404040")
        kwargs.setdefault("border_width", 2)
        kwargs.setdefault("corner_radius", 10)
        kwargs.setdefault("height", 40)
        kwargs.setdefault("font", ("Helvetica", 14))
        
        self.normal_color = kwargs["fg_color"]
        self.hover_color = kwargs["hover_color"]
        
        super().__init__(*args, **kwargs)
        self.hover_animation = None
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, event):
        if self.hover_animation:
            self.hover_animation.cancel()
        
        def animate(progress):
            # Плавна зміна кольору при наведенні
            r1, g1, b1 = int(self.normal_color[1:3], 16), int(self.normal_color[3:5], 16), int(self.normal_color[5:7], 16)
            r2, g2, b2 = int(self.hover_color[1:3], 16), int(self.hover_color[3:5], 16), int(self.hover_color[5:7], 16)
            
            r = int(r1 + (r2 - r1) * progress)
            g = int(g1 + (g2 - g1) * progress)
            b = int(b1 + (b2 - b1) * progress)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.configure(fg_color=color)
            
            # Також змінюємо колір рамки
            border_color = f"#{min(r+20, 255):02x}{min(g+20, 255):02x}{min(b+20, 255):02x}"
            self.configure(border_color=border_color)
            
        self.hover_animation = Animation(
            self,
            animate,
            duration=150,
            easing=Easing.ease_out
        )
        self.hover_animation.start()
        
    def on_leave(self, event):
        if self.hover_animation:
            self.hover_animation.cancel()
        
        def animate(progress):
            # Плавне повернення до початкового кольору
            r1, g1, b1 = int(self.hover_color[1:3], 16), int(self.hover_color[3:5], 16), int(self.hover_color[5:7], 16)
            r2, g2, b2 = int(self.normal_color[1:3], 16), int(self.normal_color[3:5], 16), int(self.normal_color[5:7], 16)
            
            r = int(r1 + (r2 - r1) * progress)
            g = int(g1 + (g2 - g1) * progress)
            b = int(b1 + (b2 - b1) * progress)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.configure(fg_color=color)
            
            # Повертаємо початковий колір рамки
            self.configure(border_color="#404040")
            
        self.hover_animation = Animation(
            self,
            animate,
            duration=150,
            easing=Easing.ease_out
        )
        self.hover_animation.start()

class AnimatedLabel(ctk.CTkLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_animation = None
        
    def configure(self, **kwargs):
        if "text" in kwargs and kwargs["text"] != self._text:
            if self.text_animation:
                self.text_animation.cancel()
            
            new_text = kwargs["text"]
            super().configure(text=new_text)
            
            def animate(progress):
                opacity = int(255 * progress)
                color = f"#{opacity:02x}{opacity:02x}{opacity:02x}"
                super(AnimatedLabel, self).configure(text_color=color)
                
            self.text_animation = Animation(
                self,  # Передаємо self як віджет
                animate,
                duration=300,
                easing=Easing.ease_in_out
            )
            self.text_animation.start()
        else:
            super().configure(**kwargs)

class Animation:
    def __init__(self, widget, update_func, duration=300, easing=None):
        self.widget = widget  # Зберігаємо посилання на віджет
        self.update_func = update_func
        self.duration = duration
        self.easing = easing or Easing.linear
        self.start_time = None
        self.cancelled = False
        self.after_id = None
        
    def start(self):
        self.start_time = time.time()
        self.animate()
        
    def animate(self):
        if self.cancelled:
            return
            
        current_time = time.time()
        progress = (current_time - self.start_time) / (self.duration / 1000)
        
        if progress >= 1:
            self.update_func(1)
            return
            
        self.update_func(self.easing(progress))
        self.after_id = self.widget.after(16, self.animate)
        
    def cancel(self):
        self.cancelled = True
        if self.after_id:
            try:
                self.widget.after_cancel(self.after_id)
            except:
                pass

class Easing:
    @staticmethod
    def linear(progress):
        return progress
        
    @staticmethod
    def ease_out(progress):
        return 1 - (1 - progress) ** 2
        
    @staticmethod
    def ease_in(progress):
        return progress ** 2
        
    @staticmethod
    def ease_in_out(progress):
        if progress < 0.5:
            return 2 * progress ** 2
        return 1 - (-2 * progress + 2) ** 2 / 2

def main():
    app = ModernVoiceAssistant()
    app.run()

if __name__ == "__main__":
    main() 

