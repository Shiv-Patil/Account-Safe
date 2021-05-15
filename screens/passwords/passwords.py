from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from password_strength import PasswordStats
import secrets
import string
from kivymd.app import MDApp
app = MDApp.get_running_app()


class Passwords(MDScreen):
    dialog_dismissable = False
    selection_timer = None
    selection_time = 0.6
    selected = False
    current_account = None

    def on_pre_enter(self):
        if self.current_account:
            self.ids.account_name.text = self.current_account.name

    def on_leave(self):
        self.ids.rv.data = {}
        self.ids.rv.scroll_y = 1

    def on_enter(self):
        app.logger.info('App: SCREEN: Passwords')
        if not self.current_account:
            app.back_button(self, 27)
        self.display_passwords()

    def display_passwords(self):
        self.ids.rv.data = {}
        select_query = "SELECT * FROM passwords WHERE account = ?"
        self.password_list = app.db.execute_read_query(
            select_query, (self.current_account.id,))
        if not self.password_list:
            return
        passwords = []
        for i in self.password_list:
            tmp = {
                "id": i[0],
                "user": i[1],
                "account": i[2],
                "username": i[3],
                "password": i[4],
                "strength": i[5],
                "color": i[6]
            }
            passwords.append(tmp)
        for password in passwords:
            self.ids.rv.data.append({
                'id': password['id'],
                'user': password['user'],
                'account': password['account'],
                'username': password['username'],
                'password': password['password'],
                'strength': password['strength'],
                'strength_color': password['color']
            })

    def add_button_clicked(self):
        if len(self.password_list) >= app.MAX_PASSWORDS_PER_ACCOUNT:
            self.dialog = MDDialog(
                title="Account limit reached",
                text="You have reached max password limit of " +
                str(app.MAX_PASSWORDS_PER_ACCOUNT) + " per account!",
                md_bg_color=app.bg_color,
                buttons=[
                    MDFlatButton(
                        text="OK",
                        text_color=app.theme_cls.primary_color,
                        on_release=self.close_dialog
                    ),
                ],
                on_dismiss=self.dialog_dismissed,
            )
            self.dialog.open()
            Window.unbind(on_key_up=app.back_button)
            Window.bind(on_key_up=self.events)
            return
        content = AddPasswordDialogContent()
        self.dialog = MDDialog(
            title="Add password",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    text_color=app.theme_cls.primary_color,
                    on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="GENREATE",
                    text_color=app.theme_cls.primary_color,
                    on_release=content.generate_pass
                ),
                MDFlatButton(
                    text="ADD",
                    text_color=app.theme_cls.primary_color,
                    on_release=self.add_password_check
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def add_password_check(self, *args):
        username = self.dialog.content_cls.ids.username
        password = self.dialog.content_cls.ids.password
        username.helper_text = ""
        password.helper_text = ""
        if len(username.text.strip()) < 1:
            username.helper_text = "This field cannot be empty"
        if len(password.text) < 1:
            password.helper_text = "This field cannot be empty"
        if len(username.text.strip()) > 32:
            username.helper_text = "Name too long. Please limit it to 32 characters."
        if len(password.text) > 32:
            password.helper_text = "Password too long. Please limit it to 32 characters."
        check_duplicate = "SELECT EXISTS(SELECT 1 FROM passwords WHERE username=? AND account=?)"
        is_dupli = app.db.execute_read_query(
            check_duplicate, (username.text.strip(), self.current_account.id))
        try:
            if is_dupli[0][0] == 0:
                pass
            else:
                username.helper_text = "This username already exists."
        except BaseException:
            pass

        if username.helper_text != '' or password.helper_text != '':
            return
        self.close_dialog()
        self.add_password(username.text.strip(), password.text)

    def add_password(self, username, password):
        strength = self.dialog.content_cls.text
        color = self.dialog.content_cls.color
        salt = app.dashboard.current_user.salt
        user_password = app.dashboard.current_user.password
        encrypting_key = app.encryption.generate_key(salt, user_password)
        password_encrypted = app.encryption.encrypt(encrypting_key, password)
        save_query = "INSERT INTO passwords (user, account, username, password, strength, color) VALUES (?, ?, ?, ?, ?, ?)"
        app.db.execute_query(save_query, (app.dashboard.current_user.id,
                                          self.current_account.id, username, password_encrypted, strength, color))
        self.display_passwords()

    def password_touch_down(self, password_item):
        Clock.unschedule(self.selection_timer)
        self.selected = False
        self.selection_timer = Clock.schedule_once(
            lambda dt: self.select(password_item), self.selection_time)

    def password_touch_move(self, password_item):
        Clock.unschedule(self.selection_timer)

    def password_touch_up(self, password_item):
        Clock.unschedule(self.selection_timer)

    def select(self, password_item):
        self.selected = True
        delete_button = MDFlatButton(
            text="DELETE", text_color=app.theme_cls.primary_color)
        delete_button.bind(on_release=lambda x: self.delete_password(
            password_item, delete_button))
        self.dialog = MDDialog(
            title=password_item.username,
            md_bg_color=app.bg_color,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="OPEN", text_color=app.theme_cls.primary_color, on_release=lambda x: self.open_password(password_item)
                ),
                delete_button,
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def password_clicked(self, password_item):
        if self.selected == False:
            self.open_password(password_item)

    def open_password(self, password_item):
        self.close_dialog()
        app.start_loading()
        salt = app.dashboard.current_user.salt
        user_password = app.dashboard.current_user.password
        encrypting_key = app.encryption.generate_key(salt, user_password)
        password_decrypted = app.encryption.decrypt(
            encrypting_key, password_item.password)
        content = ShowPasswordDialogContent()
        content.username = password_item.username
        content.password = password_decrypted
        show_button = MDFlatButton(
            text="SHOW", text_color=app.theme_cls.primary_color)
        show_button.bind(on_release=lambda x: content.show_pass(show_button))
        self.dialog = MDDialog(
            title="Password",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CLOSE", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="COPY", text_color=app.theme_cls.primary_color, on_release=lambda x: Clipboard.copy(password_decrypted)
                ),
                show_button,
            ],
            on_dismiss=self.dialog_dismissed,
        )
        content.start(show_button)
        app.stop_loading()
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def delete_password(self, password_item, button):
        if not button.theme_text_color == "Custom":
            button.theme_text_color = "Custom"
            button.text_color = (1, 0, 0, 1)
            self.dialog.text = "Delete password? Please note that this action is irreversible."
            return
        self.close_dialog()
        delete_query = "DELETE FROM passwords WHERE id = ?"
        app.db.execute_query(delete_query, (password_item.id,))
        self.display_passwords()

    def dialog_dismissed(self, *args):
        self.selected = False
        return True if not self.dialog_dismissable else False

    def close_dialog(self, *args):
        self.dialog_dismissable = True
        try:
            self.dialog.dismiss()
        except AttributeError:
            pass
        self.dialog_dismissable = False
        Window.unbind(on_key_up=self.events)
        Window.bind(on_key_up=app.back_button)

    def events(self, instance, keyboard, *args):
        if keyboard in (1001, 27):
            self.close_dialog()
            return True


class AddPasswordDialogContent(BoxLayout):
    color = '#00b200ff'
    text = None

    def update_strength(self, content, password):
        progress_bar = content.ids.password_strength
        label = content.ids.strength_label
        if password == "":
            progress_bar.color = (0, 0, 0, 0)
            label.text = self.text = " "
            return
        strength = PasswordStats(password).strength()
        progress_bar.value = max(strength, 0.05)
        if strength < 0.32:
            label.text = self.text = "WEAK"
            progress_bar.color = label.color = (.7, .07, .07, 1)
            self.color = '#b21111ff'
        elif strength < 0.66:
            label.text = self.text = "OK"
            progress_bar.color = label.color = (.7, .65, .07, 1)
            self.color = '#b2a511ff'
        else:
            label.text = self.text = "STRONG"
            progress_bar.color = label.color = (0, .7, 0, 1)
            self.color = '#00b200ff'

    def generate_pass(self, *args):
        chars = string.ascii_lowercase + string.ascii_uppercase + \
            string.digits + string.punctuation
        self.ids.password.text = ''.join(
            secrets.choice(chars) for i in range(32))


class ShowPasswordDialogContent(BoxLayout):
    def start(self, button):
        app.passwords.dialog.update_height()
        Clock.schedule_once(lambda x: self.show_pass(button))

    def show_pass(self, button):
        if self.show:
            self.show = False
            button.text = "SHOW"
        else:
            self.show = True
            button.text = "  HIDE "


Builder.load_file('passwords.kv')
