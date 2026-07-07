import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess
import sys
import os
import yaml
import locale
import copy
import time
import threading
from pathlib import Path
import ctypes

# ========== Default configuration (embedded in code) ==========
DEFAULT_CONFIG = {
    "settings": {
        "script_path": "ttl_fix.py",
        "config_path": "config.yaml",
        "ipv4_enabled": True,
        "ipv4_ttl": 65,
        "ipv6_enabled": True,
        "ipv6_ttl": 129,
        "skip_local": True,
        "auto_start": False,
        "lang": None,
        "fallback_lang": "en",
        "traffic_counter_enabled": True,
        "traffic_indicator_enabled": True,
    },
    "locales": {
        "en": {
            "title": "TTL Fix",
            "script_path": "Script path",
            "config_path": "Config path",
            "browse": "Browse script",
            "browse_config": "Browse config",
            "ipv4_enable": "Enable TTL change for IPv4",
            "ipv4_ttl_label": "IPv4 target TTL:",
            "ipv6_enable": "Enable TTL change for IPv6",
            "ipv6_ttl_label": "IPv6 target Hop Limit:",
            "skip_local": "Do not change TTL for local IP addresses",
            "status_stopped": "Status: Stopped",
            "status_running": "Status: Running",
            "start": "Start",
            "stop": "Stop",
            "error_ttl_integer": "TTL must be an integer",
            "error_no_script": "Specify the script path",
            "error_no_config": "Specify the config path",
            "error_file_not_found": "File not found:\n{path}",
            "error_config_not_found": "Config file not found:\n{path}",
            "error_launch": "Launch error:\n{error}",
            "error_install": "Installation error: {error}",
            "msg_pyyaml_not_found": "PyYAML not found. Installing...",
            "msg_pyyaml_installed": "PyYAML installed successfully.",
            "msg_pyyaml_manual": "Try manually: pip install pyyaml",
            "msg_pydivert_not_found": "PyDivert not found. Installing...",
            "msg_pydivert_installed": "PyDivert installed successfully.",
            "msg_pydivert_manual": "Try manually: pip install pydivert",
            "msg_running": "TTL Fix running.",
            "msg_ipv4_ttl": "IPv4 TTL: {ttl}",
            "msg_ipv6_ttl": "IPv6 Hop Limit: {ttl}",
            "msg_skip_local": "Local traffic skipped.",
            "msg_press_ctrlc": "Press Ctrl+C to stop.",
            "msg_stopped": "Stopped.",
            "error_no_protocol": "Neither IPv4 nor IPv6 selected. Nothing to do.",
            "lang_label": "Language:",
            "reset_defaults": "Reset to defaults",
            "reset_confirm": "Reset all settings to defaults?",
            "reset_confirm_title": "Reset",
            "traffic_counter": "Traffic counter",
            "traffic_indicator": "Traffic indicator",
            "packets_processed": "Packets: {count}",
        },
        "ru": {
            "title": "TTL Fix",
            "script_path": "Путь к скрипту",
            "config_path": "Путь к конфигу",
            "browse": "Обзор скрипта",
            "browse_config": "Обзор конфига",
            "ipv4_enable": "Включить смену TTL для IPv4",
            "ipv4_ttl_label": "IPv4 целевой TTL:",
            "ipv6_enable": "Включить смену TTL для IPv6",
            "ipv6_ttl_label": "IPv6 целевой Hop Limit:",
            "skip_local": "Не менять TTL для локальных IP адресов",
            "status_stopped": "Статус: Остановлено",
            "status_running": "Статус: Запущено",
            "start": "Старт",
            "stop": "Стоп",
            "error_ttl_integer": "TTL должен быть целым числом",
            "error_no_script": "Укажите путь к скрипту",
            "error_no_config": "Укажите путь к конфигу",
            "error_file_not_found": "Файл не найден:\n{path}",
            "error_config_not_found": "Файл конфига не найден:\n{path}",
            "error_launch": "Ошибка запуска:\n{error}",
            "error_install": "Ошибка установки: {error}",
            "msg_pyyaml_not_found": "PyYAML не найден. Устанавливаем...",
            "msg_pyyaml_installed": "PyYAML успешно установлен.",
            "msg_pyyaml_manual": "Попробуйте вручную: pip install pyyaml",
            "msg_pydivert_not_found": "PyDivert не найден. Устанавливаем...",
            "msg_pydivert_installed": "PyDivert успешно установлен.",
            "msg_pydivert_manual": "Попробуйте вручную: pip install pydivert",
            "msg_running": "TTL Fix запущен.",
            "msg_ipv4_ttl": "IPv4 TTL: {ttl}",
            "msg_ipv6_ttl": "IPv6 Hop Limit: {ttl}",
            "msg_skip_local": "Локальный трафик пропускается.",
            "msg_press_ctrlc": "Нажмите Ctrl+C для остановки.",
            "msg_stopped": "Остановлено.",
            "error_no_protocol": "Не выбран ни IPv4, ни IPv6. Нечего делать.",
            "lang_label": "Язык:",
            "reset_defaults": "Сбросить настройки",
            "reset_confirm": "Сбросить все настройки на значения по умолчанию?",
            "reset_confirm_title": "Сброс",
            "traffic_counter": "Счетчик трафика",
            "traffic_indicator": "Индикатор трафика",
            "packets_processed": "Пакетов: {count}",
        }
    }
}

# ========== Hide console on Windows ==========
def hide_console():
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

# ========== Auto-restart via pythonw.exe ==========
def ensure_pythonw():
    if sys.executable.lower().endswith("pythonw.exe"):
        return
    
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    
    if os.path.exists(pythonw):
        script = sys.argv[0]
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "open", pythonw, f'"{script}" {params}', None, 1)
        sys.exit(0)

# ========== UAC elevation ==========
def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True

    script = sys.argv[0]
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

# ========== Auto-install dependencies ==========
def ensure_dependencies(config=None):
    """Ensure pyyaml and pydivert are installed."""
    missing = []
    try:
        import yaml
    except ImportError:
        missing.append("pyyaml")
    
    try:
        import pydivert
    except ImportError:
        missing.append("pydivert")
    
    if missing:
        for pkg in missing:
            if pkg == "pyyaml":
                print(t("msg_pyyaml_not_found", config))
            else:
                print(t("msg_pydivert_not_found", config))
        
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            for pkg in missing:
                if pkg == "pyyaml":
                    print(t("msg_pyyaml_installed", config))
                else:
                    print(t("msg_pydivert_installed", config))
        except subprocess.CalledProcessError as e:
            print(t("error_install", config, error=e))
            for pkg in missing:
                if pkg == "pyyaml":
                    print(t("msg_pyyaml_manual", config))
                else:
                    print(t("msg_pydivert_manual", config))
            input("Press Enter to exit...")
            sys.exit(1)

# ========== Localization ==========
def get_system_lang():
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            return lang.split('_')[0].lower()
    except Exception:
        pass
    
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        lang_map = {0x0419: 'ru', 0x0409: 'en'}
        return lang_map.get(lang_id, 'en')
    except Exception:
        return 'en'

def resolve_config_path(config_path_str):
    """Resolve config path relative to script directory or absolute."""
    if not config_path_str:
        return None
    path = Path(config_path_str)
    if not path.is_absolute():
        script_dir = Path(__file__).parent
        path = script_dir / path
    return path.resolve()

def merge_with_defaults(user_config):
    """Merge user config with defaults. Missing keys are filled from defaults."""
    merged = copy.deepcopy(DEFAULT_CONFIG)
    
    if user_config:
        for section in ["settings", "locales"]:
            if section in user_config and isinstance(user_config[section], dict):
                if section == "locales":
                    for lang_code, lang_data in user_config[section].items():
                        if isinstance(lang_data, dict):
                            if lang_code not in merged[section]:
                                merged[section][lang_code] = {}
                            merged[section][lang_code].update(lang_data)
                else:
                    merged[section].update(user_config[section])
    
    return merged

def load_config_from_path(config_path):
    """Load config from specific path, merging with defaults."""
    if config_path and config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
            return merge_with_defaults(user_config)
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_CONFIG)

def save_config_to_path(config, config_path):
    """Save config to specific path."""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    except Exception as e:
        print(f"Failed to save config: {e}")

def reset_config():
    """Reset config to defaults and return fresh config."""
    return copy.deepcopy(DEFAULT_CONFIG)

def get_lang(config):
    saved_lang = config.get("settings", {}).get("lang")
    locales = config.get("locales", {})
    
    if saved_lang and saved_lang in locales:
        return saved_lang
    
    sys_lang = get_system_lang()
    if sys_lang in locales:
        return sys_lang
    
    fallback = config.get("settings", {}).get("fallback_lang", "en")
    if fallback in locales:
        return fallback
    
    if "en" in locales:
        return "en"
    
    if locales:
        return list(locales.keys())[0]
    
    return "en"

def t(key, config=None, **kwargs):
    if config is None:
        config = load_config_from_path(resolve_config_path("config.yaml"))
    lang = getattr(t, '_current_lang', get_lang(config))
    locales = config.get("locales", {})
    text = locales.get(lang, {}).get(key, locales.get('en', {}).get(key, key))
    return text.format(**kwargs) if kwargs else text

# ========== Traffic monitor thread ==========
class TrafficMonitor:
    def __init__(self, gui, update_interval=0.5):
        self.gui = gui
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.last_count = 0
        self.last_time = 0
    
    def start(self):
        self.running = True
        self.last_count = 0
        self.last_time = time.time()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _monitor_loop(self):
        while self.running:
            time.sleep(self.update_interval)
            if not self.running:
                break
            
            try:
                counter_path = Path(__file__).parent / ".ttl_counter"
                if counter_path.exists():
                    with open(counter_path, "r") as f:
                        count = int(f.read().strip())
                else:
                    count = 0
                
                current_time = time.time()
                
                self.gui.root.after(0, lambda c=count: self.gui.update_traffic(c))
                
                if count > self.last_count:
                    self.gui.root.after(0, self.gui.blink_indicator)
                
                self.last_count = count
                self.last_time = current_time
                
            except Exception:
                pass
    
    def reset(self):
        self.last_count = 0
        try:
            counter_path = Path(__file__).parent / ".ttl_counter"
            if counter_path.exists():
                with open(counter_path, "w") as f:
                    f.write("0")
        except Exception:
            pass

# ========== GUI ==========
class TTLGui:
    def __init__(self, root):
        self.root = root
        self.config = None
        self.config_path = None
        self.config_path_frame = None
        self.script_path_frame = None
        self.traffic_monitor = None
        self.indicator_blinking = False
        
        self.load_config()
        
        t._current_lang = get_lang(self.config)
        
        self.root.title(t("title", self.config))
        self.root.geometry("460x620")
        self.root.resizable(False, False)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.process = None

        # --- Config path ---
        self.config_path_frame = tk.LabelFrame(root, text=t("config_path", self.config))
        self.config_path_frame.pack(fill="x", padx=15, pady=(10, 5))

        self.config_path_var = tk.StringVar(value=str(self.config_path) if self.config_path else "")
        config_entry = tk.Entry(self.config_path_frame, textvariable=self.config_path_var)
        config_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.browse_config_btn = tk.Button(self.config_path_frame, text=t("browse_config", self.config), command=self.browse_config)
        self.browse_config_btn.pack(side="right", padx=5, pady=5)

        # --- Language selector ---
        lang_frame = tk.Frame(root)
        lang_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        self.lang_label = tk.Label(lang_frame, text=t("lang_label", self.config))
        self.lang_label.pack(side="left")
        
        self.lang_var = tk.StringVar(value=t._current_lang)
        locales = self.config.get("locales", {})
        lang_names = {"en": "English", "ru": "Русский"}
        self.lang_options_map = {f"{code} - {lang_names.get(code, code)}": code for code in locales.keys()}
        lang_options = list(self.lang_options_map.keys())
        self.lang_combo = ttk.Combobox(lang_frame, values=lang_options, state="readonly", width=15)
        
        current_option = f"{t._current_lang} - {lang_names.get(t._current_lang, t._current_lang)}"
        self.lang_combo.set(current_option)
        self.lang_combo.pack(side="left", padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_lang_change)

        # --- Script path ---
        self.script_path_frame = tk.LabelFrame(root, text=t("script_path", self.config))
        self.script_path_frame.pack(fill="x", padx=15, pady=(10, 5))

        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_script = os.path.join(script_dir, self.config["settings"]["script_path"])
        self.script_path_var = tk.StringVar(value=default_script)

        path_entry = tk.Entry(self.script_path_frame, textvariable=self.script_path_var)
        path_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.browse_btn = tk.Button(self.script_path_frame, text=t("browse", self.config), command=self.browse_script)
        self.browse_btn.pack(side="right", padx=5, pady=5)

        # --- IPv4 ---
        self.ipv4_var = tk.BooleanVar(value=self.config["settings"]["ipv4_enabled"])
        self.ipv4_check = tk.Checkbutton(root, text=t("ipv4_enable", self.config), variable=self.ipv4_var, command=self.on_setting_change)
        self.ipv4_check.pack(anchor="w", padx=15, pady=(10, 0))

        self.ipv4_ttl_label = tk.Label(root, text=t("ipv4_ttl_label", self.config))
        self.ipv4_ttl_label.pack(anchor="w", padx=15)
        self.ipv4_ttl_var = tk.StringVar(value=str(self.config["settings"]["ipv4_ttl"]))
        ipv4_ttl_entry = tk.Entry(root, textvariable=self.ipv4_ttl_var)
        ipv4_ttl_entry.pack(anchor="w", padx=15, fill="x")
        ipv4_ttl_entry.bind("<FocusOut>", lambda e: self.on_setting_change())

        # --- IPv6 ---
        self.ipv6_var = tk.BooleanVar(value=self.config["settings"]["ipv6_enabled"])
        self.ipv6_check = tk.Checkbutton(root, text=t("ipv6_enable", self.config), variable=self.ipv6_var, command=self.on_setting_change)
        self.ipv6_check.pack(anchor="w", padx=15, pady=(10, 0))

        self.ipv6_ttl_label = tk.Label(root, text=t("ipv6_ttl_label", self.config))
        self.ipv6_ttl_label.pack(anchor="w", padx=15)
        self.ipv6_ttl_var = tk.StringVar(value=str(self.config["settings"]["ipv6_ttl"]))
        ipv6_ttl_entry = tk.Entry(root, textvariable=self.ipv6_ttl_var)
        ipv6_ttl_entry.pack(anchor="w", padx=15, fill="x")
        ipv6_ttl_entry.bind("<FocusOut>", lambda e: self.on_setting_change())

        # --- Skip local ---
        self.skip_local_var = tk.BooleanVar(value=self.config["settings"]["skip_local"])
        self.skip_local_check = tk.Checkbutton(root, text=t("skip_local", self.config), variable=self.skip_local_var, command=self.on_setting_change)
        self.skip_local_check.pack(anchor="w", padx=15, pady=(10, 0))

        # --- Traffic options ---
        traffic_frame = tk.LabelFrame(root, text="Traffic")
        traffic_frame.pack(fill="x", padx=15, pady=(10, 0))
        
        self.traffic_counter_var = tk.BooleanVar(value=self.config["settings"].get("traffic_counter_enabled", True))
        self.traffic_counter_check = tk.Checkbutton(traffic_frame, text=t("traffic_counter", self.config), variable=self.traffic_counter_var, command=self.on_setting_change)
        self.traffic_counter_check.pack(anchor="w", padx=5)
        
        self.traffic_indicator_var = tk.BooleanVar(value=self.config["settings"].get("traffic_indicator_enabled", True))
        self.traffic_indicator_check = tk.Checkbutton(traffic_frame, text=t("traffic_indicator", self.config), variable=self.traffic_indicator_var, command=self.on_setting_change)
        self.traffic_indicator_check.pack(anchor="w", padx=5)

        # --- Traffic display ---
        display_frame = tk.Frame(root)
        display_frame.pack(pady=(10, 0))
        
        self.traffic_label = tk.Label(display_frame, text=t("packets_processed", self.config, count=0), font=("Consolas", 12))
        self.traffic_label.pack(side="left", padx=10)
        
        self.indicator_canvas = tk.Canvas(display_frame, width=30, height=30, highlightthickness=0)
        self.indicator_canvas.pack(side="left", padx=10)
        self.indicator_circle = self.indicator_canvas.create_oval(2, 2, 28, 28, fill="black", outline="gray")
        
        self.update_traffic_visibility()

        # --- Status ---
        self.status_label = tk.Label(root, text=t("status_stopped", self.config), fg="red")
        self.status_label.pack(pady=(15, 0))

        # --- Buttons ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text=t("start", self.config), command=self.start, width=12)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = tk.Button(btn_frame, text=t("stop", self.config), command=self.stop, width=12, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        # --- Reset button ---
        reset_frame = tk.Frame(root)
        reset_frame.pack(pady=5)
        self.reset_btn = tk.Button(reset_frame, text=t("reset_defaults", self.config), command=self.reset_to_defaults, width=20)
        self.reset_btn.pack()

        # --- Auto start ---
        if self.config["settings"].get("auto_start", False):
            self.root.after(500, self.start)

    def update_traffic_visibility(self):
        """Show/hide traffic counter and indicator based on settings."""
        if self.traffic_counter_var.get():
            self.traffic_label.pack(side="left", padx=10)
        else:
            self.traffic_label.pack_forget()
        
        if self.traffic_indicator_var.get():
            self.indicator_canvas.pack(side="left", padx=10)
        else:
            self.indicator_canvas.pack_forget()

    def load_config(self):
        """Load config from path stored in settings or default."""
        initial_path = resolve_config_path("config.yaml")
        if initial_path and initial_path.exists():
            self.config = load_config_from_path(initial_path)
            self.config_path = initial_path
        else:
            self.config = copy.deepcopy(DEFAULT_CONFIG)
            self.config_path = initial_path
            save_config_to_path(self.config, self.config_path)

    def save_current_config(self):
        """Save current GUI state to config file."""
        if not self.config_path:
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        current_script = self.script_path_var.get().strip()
        rel_script = os.path.relpath(current_script, script_dir) if current_script.startswith(script_dir) else current_script
        
        current_config_path = self.config_path_var.get().strip()
        rel_config = os.path.relpath(current_config_path, script_dir) if current_config_path.startswith(script_dir) else current_config_path

        self.config["settings"]["script_path"] = rel_script
        self.config["settings"]["config_path"] = rel_config
        self.config["settings"]["ipv4_enabled"] = self.ipv4_var.get()
        self.config["settings"]["ipv4_ttl"] = int(self.ipv4_ttl_var.get()) if self.ipv4_ttl_var.get().isdigit() else 65
        self.config["settings"]["ipv6_enabled"] = self.ipv6_var.get()
        self.config["settings"]["ipv6_ttl"] = int(self.ipv6_ttl_var.get()) if self.ipv6_ttl_var.get().isdigit() else 129
        self.config["settings"]["skip_local"] = self.skip_local_var.get()
        self.config["settings"]["lang"] = t._current_lang
        self.config["settings"]["traffic_counter_enabled"] = self.traffic_counter_var.get()
        self.config["settings"]["traffic_indicator_enabled"] = self.traffic_indicator_var.get()
        
        save_config_to_path(self.config, self.config_path)

    def on_setting_change(self, event=None):
        """Save config immediately when any setting changes."""
        self.update_traffic_visibility()
        self.save_current_config()

    def on_lang_change(self, event=None):
        selected = self.lang_combo.get()
        code = self.lang_options_map.get(selected, "en")
        t._current_lang = code
        self.config["settings"]["lang"] = code
        self.save_current_config()
        self.refresh_ui()

    def refresh_ui(self):
        self.root.title(t("title", self.config))
        
        if self.config_path_frame:
            self.config_path_frame.config(text=t("config_path", self.config))
        if self.script_path_frame:
            self.script_path_frame.config(text=t("script_path", self.config))
        
        self.browse_config_btn.config(text=t("browse_config", self.config))
        self.browse_btn.config(text=t("browse", self.config))
        
        self.lang_label.config(text=t("lang_label", self.config))
        self.ipv4_check.config(text=t("ipv4_enable", self.config))
        self.ipv4_ttl_label.config(text=t("ipv4_ttl_label", self.config))
        self.ipv6_check.config(text=t("ipv6_enable", self.config))
        self.ipv6_ttl_label.config(text=t("ipv6_ttl_label", self.config))
        self.skip_local_check.config(text=t("skip_local", self.config))
        self.traffic_counter_check.config(text=t("traffic_counter", self.config))
        self.traffic_indicator_check.config(text=t("traffic_indicator", self.config))
        self.start_btn.config(text=t("start", self.config))
        self.stop_btn.config(text=t("stop", self.config))
        self.reset_btn.config(text=t("reset_defaults", self.config))
        self.traffic_label.config(text=t("packets_processed", self.config, count=0))
        
        if self.process and self.process.poll() is None:
            self.status_label.config(text=t("status_running", self.config), fg="green")
        else:
            self.status_label.config(text=t("status_stopped", self.config), fg="red")

    def browse_config(self):
        path = filedialog.askopenfilename(
            title=t("browse_config", self.config),
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if path:
            self.config_path_var.set(path)
            self.config_path = Path(path)
            self.config = load_config_from_path(self.config_path)
            self.rebuild_lang_dropdown()
            self.save_current_config()

    def rebuild_lang_dropdown(self):
        """Rebuild language dropdown with current locales."""
        locales = self.config.get("locales", {})
        lang_names = {"en": "English", "ru": "Русский"}
        self.lang_options_map = {f"{code} - {lang_names.get(code, code)}": code for code in locales.keys()}
        lang_options = list(self.lang_options_map.keys())
        self.lang_combo.config(values=lang_options)
        
        current = t._current_lang
        if current not in locales:
            current = get_lang(self.config)
            t._current_lang = current
        
        current_option = f"{current} - {lang_names.get(current, current)}"
        self.lang_combo.set(current_option)

    def browse_script(self):
        path = filedialog.askopenfilename(
            title=t("browse", self.config),
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if path:
            self.script_path_var.set(path)
            self.on_setting_change()

    def reset_to_defaults(self):
        confirm_title = t("reset_confirm_title", self.config)
        confirm_msg = t("reset_confirm", self.config)
        if messagebox.askyesno(confirm_title, confirm_msg):
            self.config = reset_config()
            t._current_lang = get_lang(self.config)
            
            if self.config_path:
                save_config_to_path(self.config, self.config_path)
            
            self.rebuild_lang_dropdown()
            self.refresh_ui()
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.script_path_var.set(os.path.join(script_dir, self.config["settings"]["script_path"]))
            self.config_path_var.set(str(self.config_path) if self.config_path else os.path.join(script_dir, self.config["settings"]["config_path"]))
            self.ipv4_var.set(self.config["settings"]["ipv4_enabled"])
            self.ipv4_ttl_var.set(str(self.config["settings"]["ipv4_ttl"]))
            self.ipv6_var.set(self.config["settings"]["ipv6_enabled"])
            self.ipv6_ttl_var.set(str(self.config["settings"]["ipv6_ttl"]))
            self.skip_local_var.set(self.config["settings"]["skip_local"])
            self.traffic_counter_var.set(self.config["settings"]["traffic_counter_enabled"])
            self.traffic_indicator_var.set(self.config["settings"]["traffic_indicator_enabled"])
            self.update_traffic_visibility()

    def update_traffic(self, count):
        """Update traffic counter label."""
        if self.traffic_counter_var.get():
            self.traffic_label.config(text=t("packets_processed", self.config, count=count))

    def blink_indicator(self):
        """Blink the circular indicator white then back to black."""
        if not self.traffic_indicator_var.get() or self.indicator_blinking:
            return
        
        self.indicator_blinking = True
        self.indicator_canvas.itemconfig(self.indicator_circle, fill="white")
        self.root.after(100, self._indicator_off)
    
    def _indicator_off(self):
        self.indicator_canvas.itemconfig(self.indicator_circle, fill="black")
        self.indicator_blinking = False

    def start(self):
        if self.process and self.process.poll() is None:
            return

        try:
            ipv4_ttl = int(self.ipv4_ttl_var.get())
            ipv6_ttl = int(self.ipv6_ttl_var.get())
        except ValueError:
            messagebox.showerror("Error", t("error_ttl_integer", self.config))
            return

        script_path = self.script_path_var.get().strip()
        if not script_path:
            messagebox.showerror("Error", t("error_no_script", self.config))
            return

        if not os.path.exists(script_path):
            messagebox.showerror("Error", t("error_file_not_found", self.config, path=script_path))
            return

        cmd = [sys.executable, script_path]

        if self.ipv4_var.get():
            cmd.append("--ipv4")
        else:
            cmd.append("--no-ipv4")

        if self.ipv6_var.get():
            cmd.append("--ipv6")
        else:
            cmd.append("--no-ipv6")

        cmd.extend(["--ipv4-ttl", str(ipv4_ttl)])
        cmd.extend(["--ipv6-ttl", str(ipv6_ttl)])

        if self.skip_local_var.get():
            cmd.append("--skip-local")
        else:
            cmd.append("--no-skip-local")

        try:
            counter_path = Path(__file__).parent / ".ttl_counter"
            with open(counter_path, "w") as f:
                f.write("0")
            
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                startupinfo=startupinfo
            )
            self.status_label.config(text=t("status_running", self.config), fg="green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            
            if self.traffic_monitor:
                self.traffic_monitor.stop()
            self.traffic_monitor = TrafficMonitor(self, update_interval=0.5)
            self.traffic_monitor.start()
            
            self.save_current_config()
        except Exception as e:
            messagebox.showerror("Error", t("error_launch", self.config, error=str(e)))

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.process = None
        
        if self.traffic_monitor:
            self.traffic_monitor.stop()
            self.traffic_monitor = None
        
        self.indicator_canvas.itemconfig(self.indicator_circle, fill="black")
        
        self.status_label.config(text=t("status_stopped", self.config), fg="red")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.traffic_label.config(text=t("packets_processed", self.config, count=0))

    def on_close(self):
        """Handle window close - stop everything."""
        self.stop()
        self.root.destroy()

if __name__ == "__main__":
    hide_console()
    ensure_pythonw()
    run_as_admin()
    
    # Load config for dependency messages
    temp_config = load_config_from_path(resolve_config_path("config.yaml"))
    t._current_lang = get_lang(temp_config)
    ensure_dependencies(temp_config)
    
    root = tk.Tk()
    app = TTLGui(root)
    root.mainloop()
