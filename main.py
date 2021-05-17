import sys
import os
from kivy.config import Config
from kivy.utils import platform
Config.set('kivy', 'exit_on_escape', '0')
os.environ["KIVY_USE_DEFAULTCONFIG"] = "1"
os.environ["KIVY_METRICS_FONTSCALE"] = "1.0"
os.environ["KIVY_NO_ARGS"] = "1"
if platform != "android":
    Config.set('graphics', 'window_state', 'hidden')
    Config.set('input', 'mouse', 'mouse, multitouch_on_demand')
    os.environ["KIVY_METRICS_DENSITY"] = "1.0"
    Config.set('graphics', 'minimum_width', 400)
    Config.set('graphics', 'minimum_height', 400)
    Config.set('graphics', 'width', 1280)
    Config.set('graphics', 'height', 720)

from kivy.resources import resource_add_path
from kivy.properties import ColorProperty, NumericProperty, StringProperty
from kivy.logger import Logger
from fonts import definitions
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition, CardTransition, NoTransition
from kivy.uix.modalview import ModalView
from kivy.clock import mainthread
from widgets import textfield
import json
from kivymd.app import MDApp
from kivy.core.window import Window
SharedStorage, PrivateStorage = None, None
if platform == "android":
    from android.permissions import request_permissions, check_permission, Permission
    from modules import picker
    from modules.storage import SharedStorage, PrivateStorage
    from android.storage import primary_external_storage_path
    SharedStorage = SharedStorage()
    PrivateStorage = PrivateStorage()
    filechooser = picker.Picker()
else:
    from plyer import filechooser

class AccountSafe(MDApp):

    __version__ = "1.1"
    name = "Account Safe"
    title = "Account Safe"
    theme = StringProperty("Light")
    transition = StringProperty("Fade")
    text_color = ColorProperty([0, 0, 0, 1])
    bg_color = ColorProperty([0.98, 0.98, 0.98, 1])
    bg_color_2 = ColorProperty([0.92, 0.92, 0.92, 1])
    bg_color_3 = ColorProperty([0.87, 0.87, 0.87, 1])
    alt_primary_color = ColorProperty([0.57, 0.79, 0.957, 1])
    elevation = NumericProperty(10)

    SharedStorage = SharedStorage
    PrivateStorage = PrivateStorage

    MAX_USERS = NumericProperty(10)
    MAX_ACCOUNTS_PER_USER = NumericProperty(20)
    MAX_PASSWORDS_PER_ACCOUNT = NumericProperty(10)

    transitions = {
        "Fade": FadeTransition,
        "Card": CardTransition,
        "None": NoTransition,
    }

    def open_settings(self, *args):
        self.switch_screen("settings")

    def build(self):
        self.icon = self.resource_path(os.path.join('res', 'icon.png'))
        self.app_settings = os.path.join(
            getattr(self, 'user_data_dir'), 'database', 'config.json')

        from screens.login import login
        from screens.dashboard import dashboard
        from screens.accounts import accounts
        from screens.passwords import passwords
        from screens.settings import settings
        from screens.about import about
        from sqloperator import sqloperator
        from modules import encryption

        self.filechooser = filechooser
        if platform == 'android':
            self.backup_dir = os.path.join(primary_external_storage_path(), "account_safe")
        self.encryption = encryption
        self.logger = Logger
        self.loader = Loading()
        self.db = sqloperator.SqlOperator()
        self.root = ScreenManager()
        self.login = login.Login()
        self.dashboard = dashboard.Dashboard()
        self.accounts = accounts.Accounts()
        self.passwords = passwords.Passwords()
        self.settings = settings.Settings()
        self.about = about.About()
        self.screens = {
            "login": self.login,
            "dashboard": self.dashboard,
            "accounts": self.accounts,
            "passwords": self.passwords,
            "settings": self.settings,
            "about": self.about,
        }
        self.screen_history = []
        Window.bind(on_key_up=self.back_button)
        Window.bind(on_dropfile=self.on_dropfile)
        Window.softinput_mode = "below_target"
        self.root.transition = FadeTransition()
        self.get_theme()
        self.switch_screen("login")
        if platform != "android":
            Window.show()

    @mainthread
    def start_loading(self, *to_unbind):
        if to_unbind:
            if to_unbind[0]:
                for func in to_unbind:
                    Window.unbind(on_key_up=func)
        else:
            Window.unbind(on_key_up=self.back_button)
        self.loader.open()

    @mainthread
    def stop_loading(self, *to_bind):
        if to_bind:
            if to_bind[0]:
                for func in to_bind:
                    Window.bind(on_key_up=func)
        else:
            Window.bind(on_key_up=self.back_button)
        self.loader.dismiss()

    def on_dropfile(self, window, file_path):
        if self.root.current == 'login':
            self.login.close_dialog()
            self.settings.importing_backup(file_path.decode())
        else:
            return

    def switch_screen(self, screen_name):
        self.root.transition.mode = "push"
        self.root.transition.direction = "left"
        self.root.switch_to(self.screens.get(screen_name))
        self.screen_history.append(screen_name)

    def back_button(self, instance, keyboard, *args):
        if keyboard in (1001, 27):
            self.screen_history.pop()
            if self.screen_history != []:
                self.root.transition.mode = "pop"
                self.root.transition.direction = "right"
                self.root.switch_to(self.screens.get(self.screen_history[-1]))
            else:
                self.stop()
            return True

    def on_pause(self):
        self.set_theme()
        return True

    def on_resume(self):
        Window.update_viewport()

    def on_stop(self):
        self.set_theme()

    def get_theme(self):
        if os.path.exists(self.app_settings):
            try:
                with open(self.app_settings, 'r') as fp:
                    config = json.load(fp)
                    self.theme = config.get("theme", "Light")
                    self.theme_cls.primary_palette = config.get("color", "Purple")
                    self.transition = config.get("transition", "Fade")
            except BaseException as e:
                self.logger.error(e)
                self.set_theme()
                self.theme_cls.primary_palette = "Purple"
        else:
            self.set_theme()
            self.theme_cls.primary_palette = "Purple"
        self.settings.change_theme(self.theme)
        self.change_transition(self.transition)

    def set_theme(self):
        try:
            with open(self.app_settings, 'w+') as fp:
                json.dump(
                    {"theme": self.theme,
                        "color": self.theme_cls.primary_palette,
                        "transition": self.transition},
                    fp)
        except BaseException as e:
            self.logger.error(e)

    def change_transition(self, transition):
        self.transition = transition
        self.root.transition = self.transitions.get(transition, FadeTransition)()

    def has_storage_perms(self):
        if platform == "android":
            if not check_permission('android.permission.WRITE_EXTERNAL_STORAGE') or not check_permission('android.permission.READ_EXTERNAL_STORAGE'):
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
                return False
        return True

    @staticmethod
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)


loading = """
<Loading>:
    auto_dismiss: False
    background_color: 0, 0, 0, 0

    MDSpinner:
        size_hint: None, None
        size: dp(46), dp(46)
        pos_hint: {'center_x': .5, 'center_y': .5}
        active: True
"""


class Loading(ModalView):
    Builder.load_string(loading)


resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'login')))
resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'dashboard')))
resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'accounts')))
resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'passwords')))
resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'settings')))
resource_add_path(AccountSafe.resource_path(
    os.path.join('screens', 'about')))

definitions.add_fonts(AccountSafe.resource_path)

if __name__ == "__main__":
    AccountSafe().run()
