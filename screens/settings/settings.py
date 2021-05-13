from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.dialog import BaseDialog
from kivymd.uix.behaviors import FakeRectangularElevationBehavior, SpecificBackgroundColorBehavior
from kivymd.color_definitions import colors, palette
from kivy.utils import get_color_from_hex
from kivy.properties import OptionProperty
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.button import MDIconButton
from modules import backups
from kivy.utils import platform
import traceback
import os
from kivy.metrics import dp
from kivymd.app import MDApp
app = MDApp.get_running_app()


class Settings(MDScreen):
    selected_theme = None
    dialog_dismissable = False
    color_dialog = None
    snackbar = Snackbar(
        text=" ",
        snackbar_x="10dp",
        snackbar_y="10dp",
        size_hint_x=(
            Window.width - (dp(10) * 2)
        ) / Window.width
    )

    def on_enter(self):
        app.logger.info('App: SCREEN: Settings')

    def theme_picker(self):
        content = ThemeConfirmContent()
        if app.theme == 'Dark':
            content.ids.check_dark._do_press()
        else:
            content.ids.check_light._do_press()
        self.dialog = MDDialog(
            title="Choose theme",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="OK", text_color=app.theme_cls.primary_color, on_release=self.set_theme
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        for item in self.dialog.items:
            if item.text == app.theme:
                item.set_icon()
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def color_picker(self):
        if not self.color_dialog:
            self.color_dialog = PrimaryColorPicker()
            self.color_dialog.bind(on_dismiss=self.dialog_dismissed)
        self.color_dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def set_theme(self, *args):
        self.close_dialog()
        Clock.schedule_once(lambda x: self.change_theme(self.selected_theme))

    def change_theme(self, theme):
        if theme == 'Dark':
            app.text_color = [1, 1, 1, 1]
            app.bg_color = [0.14, 0.14, 0.14, 1]
            app.bg_color_2 = [0.17, 0.17, 0.17, 1]
            app.bg_color_3 = [0.18, 0.18, 0.18, 1]
            app.elevation = 17
            app.theme_cls.theme_style = "Dark"
            app.theme = "Dark"
        else:
            app.text_color = [0, 0, 0, 1]
            app.bg_color = [0.98, 0.98, 0.98, 1]
            app.bg_color_2 = [0.92, 0.92, 0.92, 1]
            app.bg_color_3 = [0.87, 0.87, 0.87, 1]
            app.elevation = 10
            app.theme_cls.theme_style = "Light"
            app.theme = "Light"
        app.alt_primary_color = list(map(lambda x: app.bg_color[1]*0.6+0.4*x, app.theme_cls.primary_color[:3]))+[1]
        try:
            self.dialog.md_bg_color = app.bg_color
        except AttributeError:
            pass

    def import_backup(self):
        if len(app.login.user_list) >= app.MAX_USERS:
            self.snackbar.text = "Cannot add more users. User limit reached."
            self.snackbar.open()
            return
        if not app.has_storage_perms():
            return
        Window.unbind(on_key_up=app.back_button)
        app.loader.open()
        Clock.schedule_once(self.start_import, 0.7)

    def start_import(self, *args):
        def file_chosen(selection):
            if platform == "android":
                if not selection:
                    self.backup_imported((False, "Import Cancelled"))
                    return
                try:
                    file = app.SharedStorage.retrieveUri(selection)
                    if os.path.exists(file):
                        self.importing_backup(file)
                        return
                    else:
                        raise Exception("File doesn't exist")
                except Exception as e:
                    app.logger.error("App: Settings start_import(): " + str(e))
                    traceback.print_exc()
                    self.backup_imported((False, "Unknown Error Occurred"))
                    return
            if selection:
                file = selection[0]
                if type(file) == list:
                    if file:
                        file = file[0]
                    else:
                        self.backup_imported((False, "Import Cancelled"))
                        return
                self.importing_backup(file)
            else:
                self.backup_imported((False, "Import Cancelled"))
        app.filechooser.open_file(title="Import backup", on_selection=file_chosen)

    @mainthread
    def importing_backup(self, file):
        if len(app.login.user_list) >= app.MAX_USERS:
            self.snackbar.text = "Cannot add more users. User limit reached."
            self.snackbar.open()
            return
        self.backup_imported(backups.load_backup(file))

    @mainthread
    def backup_imported(self, result):
        if not result[0]:
            self.snackbar.text = result[1]
            app.loader.dismiss()
            self.snackbar.open()
            return
        try:
            user = result[1].get('user')
            org_name = user[0]
            select_query = "SELECT id FROM users WHERE name = ?"
            for i in range(1, app.MAX_USERS):
                if app.db.execute_read_query(select_query, (user[0],)):
                    user[0] = org_name+str(i)
                else:
                    break
            save_query = "INSERT INTO users (name, key, salt, avatar) VALUES (?, ?, ?, ?)"
            app.db.execute_query(save_query, (user[0], user[1], user[2], user[3]))
            user_id = app.db.execute_read_query(select_query, (user[0],))[0][0]
            select_query = "SELECT id FROM accounts WHERE name = ?"
            for account in result[1].get('accounts'):
                save_query = "INSERT INTO accounts (user, name, pinned) VALUES (?, ?, ?)"
                app.db.execute_query(save_query, (user_id, account.get('name'), account.get('pinned')))
                acc_id = app.db.execute_read_query(select_query, (account.get('name'),))[0][0]
                for password in account.get('passwords'):
                    save_query = "INSERT INTO passwords (user, account, username, password, strength, color) VALUES (?, ?, ?, ?, ?, ?)"
                    app.db.execute_query(save_query, (user_id, acc_id, password.get('username'), password.get('password'), password.get('strength'), password.get('color')))
            self.snackbar.text = f"Successfully imported backup as {user[0]}"
            app.login.display_users()
        except BaseException as e:
            app.logger.error('App: Import Backup: ' + str(e))
            self.snackbar.text = "Something went wrong"
            traceback.print_exc()
        Window.bind(on_key_up=app.back_button)
        app.loader.dismiss()
        self.snackbar.open()

    def dialog_dismissed(self, *args):
        return True if not self.dialog_dismissable else False

    def close_dialog(self, *args):
        self.dialog_dismissable = True
        try:
            self.dialog.dismiss()
            self.color_dialog.dismiss()
        except AttributeError:
            try:
                self.color_dialog.dismiss()
            except AttributeError:
                pass
        self.dialog_dismissable = False
        Window.unbind(on_key_up=self.events)
        Window.bind(on_key_up=app.back_button)

    def events(self, instance, keyboard, *args):
        if keyboard in (1001, 27):
            self.close_dialog()
            return True


class ThemeConfirmContent(BoxLayout):
    divider = None

    def set_icon(self):
        self.ids.check.active = True
        check_list =  self.ids.check.get_widgets(self.ids.check.group)
        for check in check_list:
            if check != self.ids.check:
                check.active = False
        app.settings.selected_theme = self.text


class PrimaryColorSelector(MDIconButton):
    color_name = OptionProperty("Indigo", options=palette)

    def rgb_hex(self, col):
        return get_color_from_hex(colors[col][app.theme_cls.accent_hue])


class PrimaryColorPicker(BaseDialog, SpecificBackgroundColorBehavior, FakeRectangularElevationBehavior):
    pass


Builder.load_file('settings.kv')
