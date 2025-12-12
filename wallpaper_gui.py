import tkinter as tk
from tkinter import ttk
import subprocess
import shlex
import json
import os
import threading
import pystray
from PIL import Image, ImageTk, ImageDraw # No ImageFont for simple icon

CONFIG_FILE = "wpe_gui_config.json"
WPE_APP_ID = "431960"
LOCALE_DIR = "locales"

class I18n:
    def __init__(self, app_instance):
        self.app = app_instance
        self.locale_data = {}
        self.current_language_code_var = tk.StringVar(value="en")
        self.current_language_display_var = tk.StringVar(value="English")

        self.available_languages = {
            "en": "English",
            "ru": "Русский",
            "de": "Deutsch",
            "uk": "Українська",
            "es": "Español",
            "fr": "Français"
        }
        self.lang_codes = list(self.available_languages.keys())
        self.lang_display_names = [self.available_languages[code] for code in self.lang_codes]

    def load_translation(self, lang_code, update_gui=True):
        filepath = os.path.join(LOCALE_DIR, f"{lang_code}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.locale_data = json.load(f)
            self.current_language_code_var.set(lang_code)
            self.current_language_display_var.set(self.available_languages.get(lang_code, "English"))
            if update_gui:
                self.app.update_language_in_gui()
            return True
        except FileNotFoundError:
            self.app.safe_set_status(f"Error: Translation file not found for {lang_code}.")
            self.app.safe_set_status(f"Error: Файл перевода не найден для {lang_code}.")
            return False
        except json.JSONDecodeError:
            self.app.safe_set_status(f"Error: Invalid JSON in translation file for {lang_code}.")
            self.app.safe_set_status(f"Error: Неверный JSON в файле перевода для {lang_code}.")
            return False

    def gettext(self, key, **kwargs):
        text = self.locale_data.get(key, key)
        return text.format(**kwargs)

_ = None

class WallpaperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.i18n = I18n(self)
        global _
        _ = self.i18n.gettext

        self.current_language_code = "en"
        self.load_config()

        self.i18n.load_translation(self.current_language_code, update_gui=False) 
        
        self.title(_("app_title"))
        self.geometry("900x850")
        self.resizable(True, True)
        self.minsize(800, 700)

        self.configure_styles()

        self.preview_image_ref = None

        self.init_vars_after_lang_load()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=16)

        self.control_tab = ttk.Frame(self.notebook, style='Card.TFrame')
        self.library_tab = ttk.Frame(self.notebook, style='Card.TFrame')
        self.settings_tab = ttk.Frame(self.notebook, style='Card.TFrame')

        self.notebook.add(self.control_tab, text=_("control_tab"))
        self.notebook.add(self.library_tab, text=_("local_library_tab"))
        self.notebook.add(self.settings_tab, text=_("settings_tab"))

        self.create_control_widgets(self.control_tab)
        self.create_library_widgets(self.library_tab)
        self.create_settings_widgets(self.settings_tab)
        
        self.update_language_in_gui()

        self.i18n.current_language_code_var.trace_add('write', self._on_language_change_event)

        self.tray_icon = None
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._create_tray_icon()

        # Auto-restore wallpaper on startup if enabled
        if self.auto_restore_on_startup and self.last_wallpaper_config:
            self.after(1000, self.restore_last_wallpaper)


    def configure_styles(self):
        style = ttk.Style(self)

        # --- macOS-inspired Color Palette (Dark Theme) ---
        self.bg_primary = "#1E1E1E"      # macOS dark background
        self.bg_card = "#2D2D2D"         # Card/panel background
        self.bg_elevated = "#363636"     # Elevated elements
        self.fg_primary = "#FFFFFF"      # Primary text
        self.fg_secondary = "#98989D"    # Secondary text
        self.fg_tertiary = "#6E6E73"     # Tertiary text
        self.accent_blue = "#007AFF"     # macOS System Blue
        self.accent_blue_hover = "#0A84FF" # Hover state
        self.accent_blue_dark = "#0051D5" # Active/pressed state
        self.accent_red = "#FF3B30"      # macOS System Red
        self.accent_green = "#34C759"    # macOS System Green
        self.accent_gray = "#48484A"     # Gray accent
        self.border_subtle = "#3A3A3C"   # Subtle borders
        self.border_default = "#48484A"  # Default borders

        # Set overall background color
        self.configure(bg=self.bg_primary)

        # --- Font Definitions (macOS-inspired) ---
        # tkinter only supports: 'normal', 'bold', 'italic', 'bold italic'
        self.default_font = ('Helvetica', 12, 'normal')
        self.heading_font = ('Helvetica', 16, 'bold')
        self.button_font = ('Helvetica', 13, 'bold')
        self.secondary_font = ('Helvetica', 11, 'normal')
        self.monospace_font = ('Courier', 11, 'normal')

        # Use clam theme for better ttk widget support
        style.theme_use('clam')

        # Set root-level options for better text visibility
        self.option_add('*TButton*foreground', '#FFFFFF')
        self.option_add('*TButton*background', self.accent_blue)
        self.option_add('*TButton*highlightColor', '#FFFFFF')
        self.option_add('*TButton*activeforeground', '#FFFFFF')

        # Fix Combobox dropdown colors (white text on white background issue)
        self.option_add('*TCombobox*Listbox.background', self.bg_elevated)
        self.option_add('*TCombobox*Listbox.foreground', self.fg_primary)
        self.option_add('*TCombobox*Listbox.selectBackground', self.accent_blue)
        self.option_add('*TCombobox*Listbox.selectForeground', '#FFFFFF')
        self.option_add('*TCombobox*Listbox.font', self.default_font)

        # --- General Widget Styling ---
        style.configure('.', font=self.default_font, background=self.bg_primary, foreground=self.fg_primary)

        style.configure('TLabel', background=self.bg_card, foreground=self.fg_primary, padding=4)

        # Base Labelframe style
        style.configure('TLabelframe', background=self.bg_card, foreground=self.fg_primary,
                        borderwidth=1, relief="solid", bordercolor=self.border_subtle,
                        font=self.heading_font, padding=[24, 20, 24, 20])
        style.configure('TLabelframe.Label', background=self.bg_card, foreground=self.fg_primary,
                        font=self.heading_font, padding=[0, 0, 0, 12])

        # Card Labelframe style (with subtle border)
        style.configure('Card.TLabelframe', background=self.bg_card, foreground=self.fg_primary,
                        borderwidth=1, relief="solid", bordercolor=self.border_subtle,
                        font=self.heading_font, padding=[24, 20, 24, 20])
        style.configure('Card.TLabelframe.Label', background=self.bg_card, foreground=self.fg_primary,
                        font=self.heading_font, padding=[0, 0, 0, 12])

        # --- Buttons (macOS-style with more padding and rounded appearance) ---
        # Configure button layout to ensure text visibility
        button_layout = style.layout('TButton')

        style.configure('TButton', font=self.button_font,
                        background=self.accent_blue, foreground='white',
                        padding=[20, 12], relief="flat", borderwidth=1,
                        bordercolor=self.accent_blue, focusthickness=0,
                        lightcolor=self.accent_blue, darkcolor=self.accent_blue)
        style.map('TButton',
                  background=[('!disabled', self.accent_blue), ('active', self.accent_blue_hover), ('pressed', self.accent_blue_dark)],
                  foreground=[('!disabled', 'white'), ('active', 'white'), ('pressed', 'white'), ('selected', 'white')],
                  bordercolor=[('!disabled', self.accent_blue), ('active', self.accent_blue_hover)])

        # Ensure label element has correct foreground
        style.element_create('Button.label', 'from', 'clam')
        style.layout('TButton', [
            ('Button.border', {'sticky': 'nswe', 'children': [
                ('Button.focus', {'sticky': 'nswe', 'children': [
                    ('Button.padding', {'sticky': 'nswe', 'children': [
                        ('Button.label', {'sticky': 'nswe', 'expand': '1'})
                    ]})
                ]})
            ]})
        ])

        style.configure('Secondary.TButton', font=self.button_font,
                        background=self.bg_elevated, foreground=self.fg_primary,
                        padding=[20, 12], relief="flat", borderwidth=1,
                        bordercolor=self.border_default, focusthickness=0)
        style.map('Secondary.TButton',
                  background=[('!disabled', self.bg_elevated), ('active', self.accent_gray), ('pressed', '#3A3A3C')],
                  foreground=[('!disabled', self.fg_primary), ('active', self.fg_primary), ('pressed', self.fg_primary)],
                  bordercolor=[('!disabled', self.border_default), ('active', self.accent_gray)])

        style.configure('Danger.TButton', font=self.button_font,
                        background=self.accent_red, foreground="#FFFFFF",
                        padding=[20, 12], relief="flat", borderwidth=1,
                        bordercolor=self.accent_red, focusthickness=0)
        style.map('Danger.TButton',
                  background=[('!disabled', self.accent_red), ('active', '#FF2D20'), ('pressed', '#CC0000')],
                  foreground=[('!disabled', '#FFFFFF'), ('active', '#FFFFFF'), ('pressed', '#FFFFFF')],
                  bordercolor=[('!disabled', self.accent_red), ('active', '#FF2D20')])

        # --- Entries & Comboboxes (macOS-style input fields) ---
        style.configure('TEntry', font=self.default_font,
                        fieldbackground=self.bg_elevated, foreground=self.fg_primary,
                        borderwidth=1, relief="solid", insertcolor=self.accent_blue,
                        bordercolor=self.border_default,
                        padding=[12, 10])
        style.map('TEntry',
                  fieldbackground=[('!disabled', self.bg_elevated), ('focus', self.bg_elevated)],
                  foreground=[('!disabled', self.fg_primary)],
                  bordercolor=[('!disabled', self.border_default), ('focus', self.accent_blue)])

        style.configure('TCombobox', font=self.default_font,
                        fieldbackground=self.bg_elevated, foreground=self.fg_primary,
                        background=self.bg_elevated,
                        borderwidth=1, relief="solid", bordercolor=self.border_default,
                        arrowcolor=self.fg_secondary,
                        padding=[12, 10], arrowsize=15)
        style.map('TCombobox',
                  fieldbackground=[('!disabled', self.bg_elevated), ('readonly', self.bg_elevated), ('focus', self.bg_elevated)],
                  foreground=[('!disabled', self.fg_primary), ('readonly', self.fg_primary)],
                  background=[('!disabled', self.bg_elevated), ('readonly', self.bg_elevated)],
                  selectbackground=[('readonly', self.accent_blue)],
                  selectforeground=[('readonly', 'white')],
                  arrowcolor=[('!disabled', self.fg_secondary)],
                  bordercolor=[('!disabled', self.border_default), ('focus', self.accent_blue)])
        
        # --- Checkbuttons (macOS toggle-style) ---
        style.configure('TCheckbutton', font=self.default_font, background=self.bg_card, foreground=self.fg_primary,
                        indicatoron=True, relief='flat', borderwidth=0, padding=[12, 8])
        style.map('TCheckbutton',
                  background=[('selected', self.bg_card), ('active', self.bg_card)],
                  foreground=[('selected', self.fg_primary), ('active', self.fg_primary)])

        # --- Scales (macOS-style sliders) ---
        style.configure('TScale', background=self.bg_card, troughcolor=self.border_default,
                        sliderrelief='flat', borderwidth=0, sliderthickness=18,
                        troughrelief='flat')
        style.map('TScale',
                  background=[('active', self.bg_card)],
                  troughcolor=[('!disabled', self.border_default)],
                  sliderfill=[('active', self.accent_blue), ('!disabled', self.accent_blue)])
        
        # --- Notebook (Tabs - macOS pill-style) ---
        style.configure('TNotebook', background=self.bg_primary, borderwidth=0, tabposition='nw')
        style.configure('TNotebook.Tab',
                        background=self.bg_elevated, foreground=self.fg_secondary,
                        padding=[24, 12], font=self.button_font,
                        borderwidth=1, relief='flat',
                        bordercolor=self.border_subtle,
                        lightcolor=self.bg_elevated, darkcolor=self.bg_elevated)
        style.map('TNotebook.Tab',
                  background=[('!selected', self.bg_elevated), ('selected', self.bg_card), ('active', self.accent_gray)],
                  foreground=[('!selected', self.fg_secondary), ('selected', self.fg_primary), ('active', self.fg_primary)],
                  bordercolor=[('selected', self.border_subtle)],
                  expand=[('selected', [1, 1, 1, 0])])
        style.configure('TNotebook.Client', padding=[0, 0, 0, 0], background=self.bg_primary, borderwidth=0, relief='flat')

        style.configure('Card.TFrame', background=self.bg_card, borderwidth=0, relief='flat')

        # --- Treeview (macOS list style) ---
        style.configure('Treeview', font=self.default_font,
                        background=self.bg_card, foreground=self.fg_primary,
                        fieldbackground=self.bg_card,
                        borderwidth=1, relief='solid', bordercolor=self.border_subtle,
                        rowheight=36)
        style.configure('Treeview.Heading', font=self.button_font,
                        background=self.bg_elevated, foreground=self.fg_primary,
                        relief='flat', padding=[12, 12],
                        borderwidth=1, bordercolor=self.border_subtle)
        style.map('Treeview',
                  background=[('!selected', self.bg_card), ('selected', self.accent_blue)],
                  foreground=[('!selected', self.fg_primary), ('selected', '#FFFFFF')])

        # --- Scrollbar (macOS thin scrollbar) ---
        style.configure('TScrollbar', troughcolor=self.bg_card, background=self.fg_tertiary,
                        bordercolor=self.bg_card, arrowcolor=self.fg_primary, relief='flat',
                        width=12)
        style.map('TScrollbar', background=[('active', self.fg_secondary)])

        # --- PanedWindow ---
        style.configure('TPanedwindow', background=self.bg_primary, borderwidth=0)
        style.configure('TPanedwindow.sash', background=self.border_subtle, borderwidth=1)


    def _on_language_change_event(self, *args):
        selected_code = self.i18n.current_language_code_var.get()
        self.i18n.load_translation(selected_code, update_gui=True)
        self.save_config()

    def update_language_in_gui(self):
        self.title(_("app_title"))
        self.notebook.tab(self.control_tab, text=_("control_tab"))
        self.notebook.tab(self.library_tab, text=_("local_library_tab"))
        self.notebook.tab(self.settings_tab, text=_("settings_tab"))

        for widget in self.control_tab.winfo_children():
            widget.destroy()
        for widget in self.library_tab.winfo_children():
            widget.destroy()
        for widget in self.settings_tab.winfo_children():
            widget.destroy()
        
        self.create_control_widgets(self.control_tab)
        self.create_library_widgets(self.library_tab)
        self.create_settings_widgets(self.settings_tab)
        
        self.safe_set_status(_("status_ready"))

    def safe_set_status(self, message):
        self.after(0, lambda: self.status_var.set(message))

    def safe_populate_treeview(self, wallpapers):
        self.after(0, lambda: self.populate_treeview(wallpapers))

    def init_vars_after_lang_load(self):
        self.screens = self.detect_screens()
        self.screen_var = tk.StringVar(value=self.screens[0] if self.screens else "")
        self.background_id_var = tk.StringVar()
        self.silent_var = tk.BooleanVar()
        self.volume_var = tk.IntVar(value=15)
        self.no_automute_var = tk.BooleanVar()
        self.no_audio_processing_var = tk.BooleanVar()
        self.fps_var = tk.IntVar(value=30)
        self.scaling_var = tk.StringVar(value='default')
        self.clamp_var = tk.StringVar(value='clamp')
        self.disable_mouse_var = tk.BooleanVar()
        self.disable_parallax_var = tk.BooleanVar()
        self.no_fullscreen_pause_var = tk.BooleanVar()
        self.set_property_var = tk.StringVar()
        self.status_var = tk.StringVar(value=_("status_ready"))
        self.auto_restore_var = tk.BooleanVar(value=self.auto_restore_on_startup)
        self.stop_on_exit_var = tk.BooleanVar(value=self.stop_on_exit_setting)

    def save_config(self):
        config_data = {
            "current_language": self.i18n.current_language_code_var.get(),
            "last_wallpaper": {
                "background_id": self.background_id_var.get(),
                "screen": self.screen_var.get(),
                "silent": self.silent_var.get(),
                "volume": self.volume_var.get(),
                "no_automute": self.no_automute_var.get(),
                "no_audio_processing": self.no_audio_processing_var.get(),
                "fps": self.fps_var.get(),
                "scaling": self.scaling_var.get(),
                "clamp": self.clamp_var.get(),
                "disable_mouse": self.disable_mouse_var.get(),
                "disable_parallax": self.disable_parallax_var.get(),
                "no_fullscreen_pause": self.no_fullscreen_pause_var.get(),
                "set_property": self.set_property_var.get()
            },
            "auto_restore": getattr(self, 'auto_restore_var', tk.BooleanVar()).get(),
            "stop_on_exit": getattr(self, 'stop_on_exit_var', tk.BooleanVar()).get()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            self.safe_set_status(_("status_config_saved"))
            return True
        except IOError as e:
            self.safe_set_status(f"{_('status_error_saving_config')}: {e}")
            return False

    def load_config(self):
        self.last_wallpaper_config = None
        self.auto_restore_on_startup = False
        self.stop_on_exit_setting = False

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.current_language_code = config_data.get("current_language", "en")
                    self.last_wallpaper_config = config_data.get("last_wallpaper")
                    self.auto_restore_on_startup = config_data.get("auto_restore", False)
                    self.stop_on_exit_setting = config_data.get("stop_on_exit", False)
            except (IOError, json.JSONDecodeError) as e:
                self.status_var.set(f"{_('status_error_loading_config')}: {e}")
        self.i18n.current_language_code_var.set(self.current_language_code)

    def detect_screens(self):
        # Try X11 first (xrandr)
        try:
            result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            connected_screens = []
            primary_screen = None
            for line in lines:
                if " connected" in line:
                    parts = line.split()
                    screen_name = parts[0]
                    connected_screens.append(screen_name)
                    if "primary" in line:
                        primary_screen = screen_name

            if connected_screens:
                if primary_screen:
                    connected_screens.insert(0, connected_screens.pop(connected_screens.index(primary_screen)))
                return connected_screens
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try Wayland (wlr-randr for wlroots compositors like Sway/Hyprland)
        try:
            result = subprocess.run(['wlr-randr'], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            connected_screens = []
            for line in lines:
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    screen_name = line.split()[0]
                    if screen_name and screen_name != "":
                        connected_screens.append(screen_name)
            if connected_screens:
                return connected_screens
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Try hyprctl for Hyprland
        try:
            result = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, check=True)
            import json
            monitors = json.loads(result.stdout)
            connected_screens = [m.get('name', '') for m in monitors if m.get('name')]
            if connected_screens:
                return connected_screens
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            pass

        # Fallback to common display names
        return ["eDP-1", "HDMI-1", "DP-1"]

    def scan_local_wallpapers_thread(self):
        threading.Thread(target=self.scan_local_wallpapers, daemon=True).start()

    def find_workshop_dir(self):
        steam_paths = [
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.steam/steam")
        ]
        for path in steam_paths:
            potential_path = os.path.join(path, "steamapps/workshop/content/431960")
            if os.path.isdir(potential_path):
                return potential_path
        return None

    def scan_local_wallpapers(self):
        self.safe_set_status(_("status_searching_local"))
        workshop_dir = self.find_workshop_dir()

        if not workshop_dir:
            self.safe_set_status(_("status_no_wallpaper_dir"))
            return

        wallpapers = []
        try:
            for item_id in os.listdir(workshop_dir):
                item_path = os.path.join(workshop_dir, item_id)
                if os.path.isdir(item_path):
                    project_file = os.path.join(item_path, 'project.json')
                    if os.path.isfile(project_file):
                        with open(project_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            title = data.get('title', _("untitled"))
                            wallpapers.append({'title': title, 'id': item_id})
        except Exception as e:
            self.safe_set_status(f"{_('status_scanning_error')}: {e}")
            return
            
        if not wallpapers:
            self.safe_set_status(_("status_no_local_wallpapers"))
            return

        self.safe_populate_treeview(wallpapers)
        count_msg = _('status_local_wallpapers_found')
        try:
            self.safe_set_status(count_msg.format(count=len(wallpapers)))
        except KeyError:
            # Fallback if translation uses old format
            self.safe_set_status(f"{count_msg}: {len(wallpapers)}")

    def populate_treeview(self, wallpapers):
        self.wallpaper_tree.delete(*self.wallpaper_tree.get_children())
        for wallpaper in sorted(wallpapers, key=lambda x: x['title'].lower()):
            self.wallpaper_tree.insert('', tk.END, values=(wallpaper['title'], wallpaper['id']))

    def on_wallpaper_select(self, event):
        selected_items = self.wallpaper_tree.selection()
        if not selected_items: return
        
        selected_item = self.wallpaper_tree.item(selected_items[0])
        wallpaper_id = selected_item['values'][1]

        self.background_id_var.set(wallpaper_id)
        self.build_and_run_command()

        if Image is None or ImageTk is None:
            self.preview_label.config(text=_("preview_not_available"))
            return

        try:
            workshop_dir = self.find_workshop_dir()
            if not workshop_dir: return

            item_path = os.path.join(workshop_dir, str(wallpaper_id))
            project_file = os.path.join(item_path, 'project.json')

            if not os.path.isfile(project_file):
                self.preview_label.config(image='', text=_("project_json_not_found"))
                return

            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            preview_filename = data.get('preview')
            if not preview_filename:
                self.preview_label.config(image='', text=_("preview_not_specified"))
                return
            
            image_path = os.path.join(item_path, str(preview_filename))
            if not os.path.isfile(image_path):
                self.preview_label.config(image='', text=_("preview_file_not_found"))
                return

            img = Image.open(image_path)
            img.thumbnail((400, 225))
            
            self.preview_image_ref = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image_ref)

        except Exception as e:
            self.preview_label.config(image='', text=_("preview_loading_error").format(error=e))
            self.preview_image_ref = None

    def build_and_run_command(self, preview_mode=False):
        self.stop_wallpapers(silent=True)
        bg_id = self.background_id_var.get()
        if not bg_id:
            self.status_var.set(_("status_error_empty_id")); return

        cmd = ['linux-wallpaperengine']
        if self.silent_var.get(): cmd.append('--silent')
        else:
            if self.volume_var.get() != 15: cmd.extend(['--volume', str(self.volume_var.get())])
        if self.no_automute_var.get(): cmd.append('--noautomute')
        if self.no_audio_processing_var.get(): cmd.append('--no-audio-processing')
        if self.fps_var.get() != 30: cmd.extend(['--fps', str(self.fps_var.get())])
        if self.no_fullscreen_pause_var.get(): cmd.append('--no-fullscreen-pause')
        if self.disable_mouse_var.get(): cmd.append('--disable-mouse')
        if self.disable_parallax_var.get(): cmd.append('--disable-parallax')
        if self.set_property_var.get():
            for prop in self.set_property_var.get().split(): cmd.extend(['--set-property', prop])

        if preview_mode: cmd.append(bg_id)
        else:
            screen = self.screen_var.get()
            if not screen: self.status_var.set(_("status_error_screen_not_selected")); return
            cmd.extend(['--screen-root', screen, '--bg', bg_id])
            if self.scaling_var.get() != 'default': cmd.extend(['--scaling', self.scaling_var.get()])
            if self.clamp_var.get() != 'clamp': cmd.extend(['--clamp', self.clamp_var.get()])

        try:
            command_str = shlex.join(cmd)
            subprocess.Popen(cmd)
            self.status_var.set(f"{_('status_command_launched')}{command_str}")
            # Save config after successful wallpaper launch
            if not preview_mode:
                self.save_config()
        except (FileNotFoundError, Exception) as e: self.status_var.set(f"{_('status_error_launch_command')}{e}")

    def restore_last_wallpaper(self):
        if not self.last_wallpaper_config:
            self.safe_set_status("No saved wallpaper configuration found")
            return

        # Restore all settings from config
        self.background_id_var.set(self.last_wallpaper_config.get("background_id", ""))
        self.screen_var.set(self.last_wallpaper_config.get("screen", self.screens[0] if self.screens else ""))
        self.silent_var.set(self.last_wallpaper_config.get("silent", False))
        self.volume_var.set(self.last_wallpaper_config.get("volume", 15))
        self.no_automute_var.set(self.last_wallpaper_config.get("no_automute", False))
        self.no_audio_processing_var.set(self.last_wallpaper_config.get("no_audio_processing", False))
        self.fps_var.set(self.last_wallpaper_config.get("fps", 30))
        self.scaling_var.set(self.last_wallpaper_config.get("scaling", "default"))
        self.clamp_var.set(self.last_wallpaper_config.get("clamp", "clamp"))
        self.disable_mouse_var.set(self.last_wallpaper_config.get("disable_mouse", False))
        self.disable_parallax_var.set(self.last_wallpaper_config.get("disable_parallax", False))
        self.no_fullscreen_pause_var.set(self.last_wallpaper_config.get("no_fullscreen_pause", False))
        self.set_property_var.set(self.last_wallpaper_config.get("set_property", ""))

        # Launch the wallpaper
        self.build_and_run_command()

    def stop_wallpapers(self, silent=False):
        try:
            subprocess.run(['pkill', '-f', 'linux-wallpaperengine'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not silent: self.status_var.set(_("status_all_stopped"))
        except (subprocess.CalledProcessError, FileNotFoundError):
            if not silent: self.status_var.set(_("status_no_processes_found"))

    def _configure_combobox_colors(self, combobox):
        """Configure dropdown colors for a Combobox widget"""
        try:
            # Get the popdown listbox
            combobox.tk.eval(f'''
                ttk::combobox::PopdownWindow {combobox}
                {combobox}.popdown.f.l configure \
                    -background {self.bg_elevated} \
                    -foreground {self.fg_primary} \
                    -selectbackground {self.accent_blue} \
                    -selectforeground #FFFFFF \
                    -font {{Helvetica 12}}
            ''')
        except:
            # Fallback: try alternative method
            try:
                listbox = combobox.tk.call('ttk::combobox::PopdownWindow', combobox)
            except:
                pass

    def create_custom_button(self, parent, text, command, button_type='primary'):
        """Create a custom tk.Button styled like macOS"""
        if button_type == 'primary':
            bg = self.accent_blue
            fg = '#FFFFFF'
            active_bg = self.accent_blue_hover
        elif button_type == 'danger':
            bg = self.accent_red
            fg = '#FFFFFF'
            active_bg = '#FF2D20'
        else:  # secondary
            bg = self.bg_elevated
            fg = self.fg_primary
            active_bg = self.accent_gray

        btn = tk.Button(parent, text=text, command=command,
                       font=self.button_font, bg=bg, fg=fg,
                       activebackground=active_bg, activeforeground='#FFFFFF' if button_type != 'secondary' else self.fg_primary,
                       relief='flat', borderwidth=0,
                       padx=20, pady=12,
                       cursor='hand2',
                       highlightthickness=0)
        return btn

    def create_control_widgets(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        container.columnconfigure(0, weight=1)
        main_controls_frame = ttk.Labelframe(container, text=_("main_controls_frame"), style='Card.TLabelframe')
        audio_frame = ttk.Labelframe(container, text=_("audio_frame"), style='Card.TLabelframe')
        perf_frame = ttk.Labelframe(container, text=_("perf_frame"), style='Card.TLabelframe')
        adv_frame = ttk.Labelframe(container, text=_("adv_frame"), style='Card.TLabelframe')
        action_frame = ttk.Frame(container, padding="20", style='Card.TFrame')
        status_frame = ttk.Frame(container, padding="16", style='Card.TFrame')

        main_controls_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        audio_frame.grid(row=1, column=0, sticky="ew", padx=16, pady=12)
        perf_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=12)
        adv_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=12)
        action_frame.grid(row=4, column=0, sticky="ew", padx=16, pady=12)
        status_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=12)

        main_controls_frame.columnconfigure(1, weight=1)
        audio_frame.columnconfigure(1, weight=1)
        perf_frame.columnconfigure(1, weight=1); perf_frame.columnconfigure(3, weight=1)
        adv_frame.columnconfigure(1, weight=1)
        action_frame.columnconfigure(0, weight=1); action_frame.columnconfigure(1, weight=1); action_frame.columnconfigure(2, weight=1)
        status_frame.columnconfigure(0, weight=1)

        ttk.Label(main_controls_frame, text=_("wallpaper_id_path_label"), style='TLabel').grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(main_controls_frame, textvariable=self.background_id_var, style='TEntry').grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        ttk.Label(main_controls_frame, text=_("screen_label"), style='TLabel').grid(row=1, column=0, sticky="w", padx=8, pady=6)
        screen_combo = ttk.Combobox(main_controls_frame, textvariable=self.screen_var, values=self.screens, state='readonly', style='TCombobox')
        screen_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        self._configure_combobox_colors(screen_combo)
        
        ttk.Checkbutton(audio_frame, text=_("silent_checkbox"), variable=self.silent_var, style='TCheckbutton').grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Label(audio_frame, text=_("volume_label"), style='TLabel').grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Scale(audio_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.volume_var, style='TScale').grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        ttk.Checkbutton(audio_frame, text=_("no_automute_checkbox"), variable=self.no_automute_var, style='TCheckbutton').grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Checkbutton(audio_frame, text=_("no_audio_processing_checkbox"), variable=self.no_audio_processing_var, style='TCheckbutton').grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=6)

        ttk.Label(perf_frame, text=_("fps_label"), style='TLabel').grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Scale(perf_frame, from_=1, to=144, orient=tk.HORIZONTAL, variable=self.fps_var, style='TScale').grid(row=0, column=1, sticky="ew", padx=8, pady=6)

        ttk.Label(perf_frame, text=_("scaling_label"), style='TLabel').grid(row=1, column=0, sticky="w", padx=8, pady=6)
        scaling_combo = ttk.Combobox(perf_frame, textvariable=self.scaling_var, values=['stretch', 'fit', 'fill', 'default'], state='readonly', style='TCombobox')
        scaling_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        self._configure_combobox_colors(scaling_combo)

        ttk.Label(perf_frame, text=_("clamp_label"), style='TLabel').grid(row=1, column=2, sticky="w", padx=8, pady=6)
        clamp_combo = ttk.Combobox(perf_frame, textvariable=self.clamp_var, values=['clamp', 'border', 'repeat'], state='readonly', style='TCombobox')
        clamp_combo.grid(row=1, column=3, sticky="ew", padx=8, pady=6)
        self._configure_combobox_colors(clamp_combo)
        ttk.Checkbutton(perf_frame, text=_("disable_mouse_checkbox"), variable=self.disable_mouse_var, style='TCheckbutton').grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Checkbutton(perf_frame, text=_("disable_parallax_checkbox"), variable=self.disable_parallax_var, style='TCheckbutton').grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=6)
        ttk.Checkbutton(perf_frame, text=_("no_fullscreen_pause_checkbox"), variable=self.no_fullscreen_pause_var, style='TCheckbutton').grid(row=4, column=0, columnspan=4, sticky="w", padx=8, pady=6)

        ttk.Label(adv_frame, text=_("set_property_label"), style='TLabel').grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(adv_frame, textvariable=self.set_property_var, style='TEntry').grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        hint_label = ttk.Label(adv_frame, text=_("set_property_example"), font=self.secondary_font, foreground=self.fg_tertiary, background=self.bg_card)
        hint_label.grid(row=1, column=1, sticky="w", padx=8, pady=(0, 6))
        
        # Use custom tk.Button for better text visibility
        btn_set = self.create_custom_button(action_frame, _("set_wallpaper_button"), self.build_and_run_command, 'primary')
        btn_set.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        btn_preview = self.create_custom_button(action_frame, _("preview_in_window_button"),
                                                lambda: self.build_and_run_command(preview_mode=True), 'primary')
        btn_preview.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        btn_stop = self.create_custom_button(action_frame, _("stop_button"), self.stop_wallpapers, 'danger')
        btn_stop.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        btn_restore = self.create_custom_button(action_frame, _("restore_last_button"), self.restore_last_wallpaper, 'secondary')
        btn_restore.grid(row=1, column=0, columnspan=3, padx=6, pady=(6, 0), sticky="ew")
        
        # Status label with secondary text style
        status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=750,
                                font=self.secondary_font, foreground=self.fg_secondary,
                                background=self.bg_card)
        status_label.grid(row=0, column=0, sticky="ew", padx=8, pady=8)

    def create_library_widgets(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        container.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        paned_window = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        list_container = ttk.Frame(paned_window, padding=16, style='Card.TFrame')
        list_container.rowconfigure(1, weight=1)
        list_container.columnconfigure(0, weight=1)
        paned_window.add(list_container, weight=1)

        # Use custom button for better text visibility
        btn_scan = self.create_custom_button(list_container, _("scan_local_wallpapers_button"),
                                            self.scan_local_wallpapers_thread, 'primary')
        btn_scan.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        list_frame = ttk.Labelframe(list_container, text=_("found_wallpapers_frame"), style='Card.TLabelframe')
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.wallpaper_tree = ttk.Treeview(list_frame, columns=('Title', 'ID'), show='headings', style='Treeview')
        self.wallpaper_tree.heading('Title', text=_("treeview_title_column"))
        self.wallpaper_tree.heading('ID', text=_("treeview_id_column"))
        self.wallpaper_tree.column('ID', width=120, stretch=tk.NO, anchor='center')
        self.wallpaper_tree.column('Title', width=200, stretch=tk.YES, anchor='w')
        self.wallpaper_tree.grid(row=0, column=0, sticky="nsew")
        self.wallpaper_tree.bind('<<TreeviewSelect>>', self.on_wallpaper_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.wallpaper_tree.yview, style='TScrollbar')
        self.wallpaper_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        preview_container = ttk.Labelframe(paned_window, text=_("preview_frame"), style='Card.TLabelframe')
        paned_window.add(preview_container, weight=2)

        self.preview_label = ttk.Label(preview_container, text=_("preview_placeholder"), anchor=tk.CENTER, background=self.bg_card, foreground=self.fg_secondary, style='TLabel')
        self.preview_label.pack(expand=True, fill=tk.BOTH, padx=16, pady=16)

    def create_settings_widgets(self, container):
        for widget in container.winfo_children():
            widget.destroy()

        container.columnconfigure(1, weight=1)

        settings_frame = ttk.Labelframe(container, text=_("settings_tab"), style='Card.TLabelframe')
        settings_frame.pack(side=tk.TOP, fill=tk.X, padx=16, pady=12)
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text=_("language_label"), style='TLabel').grid(row=0, column=0, sticky="w", padx=8, pady=8)

        lang_combobox = ttk.Combobox(settings_frame, textvariable=self.i18n.current_language_display_var,
                                     values=self.i18n.lang_display_names, state='readonly', style='TCombobox')
        lang_combobox.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self._configure_combobox_colors(lang_combobox)

        def on_lang_select(event):
            selected_display_name = self.i18n.current_language_display_var.get()
            for code, name in self.i18n.available_languages.items():
                if name == selected_display_name:
                    self.i18n.current_language_code_var.set(code)
                    break

        lang_combobox.bind("<<ComboboxSelected>>", on_lang_select)

        # Auto-restore checkbox
        auto_restore_check = ttk.Checkbutton(settings_frame, text=_("auto_restore_checkbox"),
                                            variable=self.auto_restore_var, style='TCheckbutton',
                                            command=self.save_config)
        auto_restore_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=12)

        # Stop on exit checkbox
        stop_on_exit_check = ttk.Checkbutton(settings_frame, text=_("stop_on_exit_checkbox"),
                                            variable=self.stop_on_exit_var, style='TCheckbutton',
                                            command=self.save_config)
        stop_on_exit_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=12)


    def _create_tray_icon(self):
        if not pystray or not Image or not ImageDraw:
            # Fallback for when pystray or PIL components are not available
            # Use self.safe_set_status here? But _create_tray_icon is called during init
            # before the GUI is fully drawn. Best to assume it works or log.
            # self.safe_set_status(_("tray_missing_deps_error")) # This would fail too early
            return

        # Create a simple blue circle icon
        width, height = 64, 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0)) # Transparent background
        draw = ImageDraw.Draw(image)
        draw.ellipse((0, 0, width, height), fill=self.accent_blue, outline=self.accent_blue_dark, width=2)
        
        menu = (
            pystray.MenuItem(_("show_window_tray_menu"), self._show_window),
            pystray.MenuItem(_("exit_tray_menu"), self._quit_app)
        )
        self.tray_icon = pystray.Icon("wallpaper_gui", image, _("app_title"), menu)

    def _on_closing(self):
        self.withdraw()
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_window(self, icon, item):
        self.after(0, self.deiconify)
        if self.tray_icon:
            self.tray_icon.stop()

    def _quit_app(self, icon, item):
        if self.stop_on_exit_var.get():
            self.stop_wallpapers(silent=True)
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.quit)


if __name__ == "__main__":
    app = WallpaperGUI()
    app.mainloop()