from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.uix.taptargetview import MDTapTargetView
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import secrets
from kivy.core.window import Window
from cryptography.fernet import InvalidToken
from kivy.clock import Clock
from kivymd.app import MDApp
app = MDApp.get_running_app()


class Login(MDScreen):
    dialog_dismissable = False
    selection_timer = None
    selection_time = 0.6
    selected = False

    def on_enter(self):
        app.logger.info('App: SCREEN: Login')
        app.dashboard.current_user = None
        self.display_users()

    def on_leave(self):
        try:
            if self.tap_target_view.state == "open":
                self.tap_target_view.stop()
        except BaseException:
            pass

    def display_users(self):
        self.ids.rv.scroll_y = 1
        self.ids.rv.data = {}
        select_query = "SELECT * FROM users"
        self.user_list = app.db.execute_read_query(select_query)
        if not self.user_list:
            self.tap_target_view = MDTapTargetView(
                widget=self.ids.add_button_cover,
                title_text="You don't have any users",
                description_text="Click on this button to add one!",
                widget_position="right_bottom",
                stop_on_target_touch=False,
                target_circle_color=app.bg_color[:3]
            )
            if self.tap_target_view.state == "close":
                self.tap_target_view.start()
            return
        users = []
        for i in self.user_list:
            tmp = {
                "id": i[0],
                "name": i[1],
                "salt": i[2],
                "avatar": i[3],
                "key": i[4],
            }
            users.append(tmp)
        for user in users:
            self.ids.rv.data.append({
                'id': user['id'],
                'text': user['name'],
                'salt': user['salt'],
                'source': user['avatar'],
                'key': user['key']
            })

    def add_button_clicked(self):
        if len(self.user_list) >= app.MAX_USERS:
            self.dialog = MDDialog(
                title="User limit reached",
                text=f"You have reached max user limit of {app.MAX_USERS}!",
                md_bg_color=app.bg_color,
                buttons=[
                    MDFlatButton(
                        text="OK", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                    ),
                ],
                on_dismiss=self.dialog_dismissed,
            )
            self.dialog.open()
            Window.unbind(on_key_up=app.back_button)
            Window.bind(on_key_up=self.events)
            return
        try:
            if self.tap_target_view.state == "open":
                self.tap_target_view.stop()
        except BaseException:
            pass
        content = AddUserDialogContent()
        self.dialog = MDDialog(
            title="Add new user",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="ADD", text_color=app.theme_cls.primary_color, on_release=self.add_user_check
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def increase_user_limit(self, *args):
        pass

    def dialog_dismissed(self, *args):
        self.selected = False
        return True if not self.dialog_dismissable else False

    def add_user_check(self, *args):
        name = self.dialog.content_cls.ids.name
        password = self.dialog.content_cls.ids.password
        name.helper_text = ""
        password.helper_text = ""
        if len(name.text.strip()) < 1:
            name.helper_text = "Cannot be empty"
        if len(password.text) < 1:
            password.helper_text = "Cannot be empty"
        elif len(password.text) < 8:
            password.helper_text = "Minimum 8 characters required"
        if len(name.text.strip()) > 32:
            name.helper_text = "Maximum 32 characters allowed"
        if len(password.text) > 32:
            password.helper_text = "Maximum 32 characters allowed"
        check_duplicate = "SELECT EXISTS(SELECT 1 FROM users WHERE name=?)"
        is_dupli = app.db.execute_read_query(
            check_duplicate, (name.text.strip(),))
        try:
            if is_dupli[0][0] == 0:
                pass
            else:
                name.helper_text = "This user already exists."
        except BaseException:
            pass

        if name.helper_text != '' or password.helper_text != '':
            return
        self.close_dialog()
        self.add_user(name.text.strip(), password.text)

    def add_user(self, name, password):
        salt = secrets.token_bytes(32)
        encrypting_key = app.encryption.generate_key(salt, password)
        key = app.encryption.encrypt(encrypting_key, 'KrYmZiN')
        save_query = "INSERT INTO users (name, key, salt, avatar) VALUES (?, ?, ?, ?)"
        app.db.execute_query(save_query, (name, key, salt,
                                          "data/logo/kivy-icon-128.png"))
        self.display_users()

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
            self.display_users()
            return True

    def user_touch_down(self, user_list_item):
        Clock.unschedule(self.selection_timer)
        self.selected = False
        self.selection_timer = Clock.schedule_once(
            lambda dt: self.select(user_list_item), self.selection_time)

    def user_touch_move(self, user_list_item):
        Clock.unschedule(self.selection_timer)

    def user_touch_up(self, user_list_item):
        Clock.unschedule(self.selection_timer)

    def select(self, user_list_item):
        self.selected = True
        self.dialog = MDDialog(
            title=user_list_item.text,
            md_bg_color=app.bg_color,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="OPEN", text_color=app.theme_cls.primary_color, on_release=lambda x: self.login_user(user_list_item)
                ),
                MDFlatButton(
                    text="DELETE", text_color=app.theme_cls.primary_color, on_release=lambda x: self.confirm_delete_user(user_list_item)
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def user_clicked(self, user_list_item):
        if self.selected == False:
            self.login_user(user_list_item)

    def login_user(self, user_list_item):
        content = LoginUserDialogContent()
        content.name = user_list_item.text
        self.dialog = MDDialog(
            title="Login",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="LOGIN", text_color=app.theme_cls.primary_color, on_release=lambda x: self.login_user_check(user_list_item)
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def password_check(self, user_list_item):
        password = self.dialog.content_cls.ids.password
        salt = user_list_item.salt
        encrypting_key = app.encryption.generate_key(salt, password.text)
        try:
            decrypted = app.encryption.decrypt(
                encrypting_key, user_list_item.key)
            if decrypted == 'KrYmZiN':
                return True
        except InvalidToken:
            pass
        return False

    def login_user_check(self, user_list_item):
        app.start_loading()
        password = self.dialog.content_cls.ids.password
        password.helper_text = ""
        if self.password_check(user_list_item):
            user_list_item.password = password.text
            app.stop_loading()
            self.user_logged_in(user_list_item)
            return
        password.helper_text = "Invalid Password."
        app.stop_loading()

    def user_logged_in(self, user_list_item):
        self.close_dialog()
        app.dashboard.current_user = user_list_item
        app.switch_screen('dashboard')

    def confirm_delete_user(self, user_list_item):
        self.close_dialog()
        content = DeleteUserDialogContent()
        content.name = user_list_item.text
        self.dialog = MDDialog(
            title="Confirm Delete",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="DELETE", text_color=app.theme_cls.primary_color, on_release=lambda x: self.delete_user(user_list_item)
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def delete_user(self, user_list_item):
        password = self.dialog.content_cls.ids.password
        password.helper_text = ""
        if not self.password_check(user_list_item):
            password.helper_text = "Invalid Password."
            return
        self.close_dialog()
        delete_query = "DELETE FROM users WHERE id = ?"
        app.db.execute_query(delete_query, (user_list_item.id,))
        self.display_users()


class AddUserDialogContent(BoxLayout):
    pass


class LoginUserDialogContent(BoxLayout):
    pass


class DeleteUserDialogContent(BoxLayout):
    pass


Builder.load_file('login.kv')
