from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.core.window import Window
from kivy.clock import Clock
from kivymd import color_definitions
import random
from kivymd.app import MDApp
app = MDApp.get_running_app()


class Accounts(MDScreen):
    dialog_dismissable = False
    selection_timer = None
    selection_time = 0.6
    selected = False

    def on_leave(self):
        self.ids.rv.data = {}
        self.ids.rv.scroll_y = 1

    def on_enter(self):
        app.logger.info('App: SCREEN: Accounts')
        self.display_accounts()

    def display_accounts(self):
        self.ids.rv.data = {}
        self.ids.rv.data.append({
            'id': '-',
            'name': "Add account",
            'letter': "+",
            'color_tint': app.theme_cls.primary_color,
            'pinned': False
        })
        select_query = "SELECT * FROM accounts WHERE user = ?"
        self.account_list = app.db.execute_read_query(
            select_query, (app.dashboard.current_user.id,))
        if not self.account_list:
            return
        accounts = []
        for i in self.account_list:
            tmp = {
                "id": i[0],
                "user": i[1],
                "name": i[2],
                "pinned": i[3]
            }
            accounts.append(tmp)
        accounts_pinned, accounts_not_pinned = [], []
        for account in accounts:
            accounts_pinned.append(account) if account.get(
                "pinned") else accounts_not_pinned.append(account)
        accounts_pinned.sort(key=lambda x: x.get('name'))
        accounts_not_pinned.sort(key=lambda x: x.get('name'))
        for account in accounts_pinned+accounts_not_pinned:
            self.ids.rv.data.append({
                'id': account['id'],
                'user': account['user'],
                'name': account['name'],
                'letter': account['name'][0].upper(),
                'color_tint': get_color_from_hex(color_definitions.colors[random.choice(color_definitions.palette)]['500']),
                'pinned': account['pinned'],
            })

    def account_touch_down(self, account_item):
        if account_item.letter == '+' and account_item.id == '-':
            return
        Clock.unschedule(self.selection_timer)
        self.selected = False
        self.selection_timer = Clock.schedule_once(
            lambda dt: self.select(account_item), self.selection_time)

    def account_touch_move(self, account_item):
        Clock.unschedule(self.selection_timer)

    def account_touch_up(self, account_item):
        Clock.unschedule(self.selection_timer)

    def select(self, account_item):
        self.selected = True
        delete_button = MDFlatButton(
            text="DELETE", text_color=app.theme_cls.primary_color)
        delete_button.bind(on_release=lambda x: self.delete_account(
            account_item, delete_button))
        self.dialog = MDDialog(
            title=account_item.name,
            md_bg_color=app.bg_color,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="UNPIN" if account_item.pinned else "PIN", text_color=app.theme_cls.primary_color, on_release=lambda x: self.pin_account(account_item)
                ),
                delete_button,
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

    def account_clicked(self, account_item):
        if self.selected == False:
            if account_item.letter == '+' and account_item.id == '-':
                self.add_button_clicked()
                return
            self.open_account(account_item)

    def open_account(self, account_item):
        app.passwords.current_account = account_item
        app.switch_screen('passwords')

    def pin_account(self, account_item):
        update_query = "UPDATE accounts SET pinned = ? WHERE id = ?"
        app.db.execute_query(
            update_query, (not(account_item.pinned), account_item.id))
        self.close_dialog()
        self.display_accounts()

    def add_button_clicked(self):
        if len(self.account_list) >= app.MAX_ACCOUNTS_PER_USER:
            self.dialog = MDDialog(
                title="Account limit reached",
                text=f"You have reached max account limit of {app.MAX_ACCOUNTS_PER_USER} per user!",
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
        content = AddAccountDialogContent()
        self.dialog = MDDialog(
            title="Add new account",
            md_bg_color=app.bg_color,
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="CANCEL", text_color=app.theme_cls.primary_color, on_release=self.close_dialog
                ),
                MDFlatButton(
                    text="ADD", text_color=app.theme_cls.primary_color, on_release=self.add_account_check
                ),
            ],
            on_dismiss=self.dialog_dismissed,
        )
        self.dialog.open()
        Window.unbind(on_key_up=app.back_button)
        Window.bind(on_key_up=self.events)

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

    def add_account_check(self, *args):
        name = self.dialog.content_cls.ids.name
        name.helper_text = ""
        if len(name.text.strip()) < 1:
            name.helper_text = "This field cannot be empty"
        if len(name.text.strip()) > 16:
            name.helper_text = "Maximum 16 characters allowed"
        check_duplicate = "SELECT EXISTS(SELECT 1 FROM accounts WHERE name=? AND user=?)"
        is_dupli = app.db.execute_read_query(
            check_duplicate, (name.text.strip(), app.dashboard.current_user.id))
        try:
            if is_dupli[0][0] == 0:
                pass
            else:
                name.helper_text = "Account already exists."
        except BaseException:
            pass

        if name.helper_text != '':
            return
        self.close_dialog()
        self.add_account(name.text.strip())

    def add_account(self, name):
        save_query = "INSERT INTO accounts (user, name, pinned) VALUES (?, ?, ?)"
        app.db.execute_query(
            save_query, (app.dashboard.current_user.id, name, False))
        self.display_accounts()

    def delete_account(self, account_item, button):
        if not button.theme_text_color == "Custom":
            button.theme_text_color = "Custom"
            button.text_color = (1, 0, 0, 1)
            self.dialog.text = "Delete account? Please note that this action is irreversible."
            return
        self.close_dialog()
        delete_query = "DELETE FROM accounts WHERE id = ?"
        app.db.execute_query(delete_query, (account_item.id,))
        self.display_accounts()


class AddAccountDialogContent(BoxLayout):
    pass


Builder.load_file('accounts.kv')
