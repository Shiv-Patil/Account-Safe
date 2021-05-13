from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.app import MDApp
import os
from kivy.core.window import Window
from modules import backups
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from kivy.clock import Clock, mainthread
from kivy.utils import platform
share = None
app = MDApp.get_running_app()
if platform == 'android':
    from modules.sharesnd import ShareSend
    from jnius import autoclass
    import shutil
    Uri = autoclass('android.net.Uri')
    File = autoclass('java.io.File')
    Context = autoclass("android.content.Context")
    FileProvider = autoclass('androidx.core.content.FileProvider')
    share = ShareSend()


class Dashboard(MDScreen):
    current_user = None
    loader = None
    share = share

    snackbar = Snackbar(
        text="Backup saved successfully",
        snackbar_x="10dp",
        snackbar_y="10dp",
        size_hint_x=(
            Window.width - (dp(10) * 2)
        ) / Window.width
    )

    def on_pre_enter(self):
        self.ids.user_card.ids.user_name.text = self.current_user.text
        self.ids.user_card.ids.user_avatar.source = self.current_user.source
        select_query = "SELECT * FROM accounts WHERE user = ?"
        account_list = app.db.execute_read_query(
            select_query, (self.current_user.id,))
        self.ids.account_count.text = str(len(account_list))
        select_query = "SELECT * FROM passwords WHERE user = ?"
        password_list = app.db.execute_read_query(
            select_query, (self.current_user.id,))
        self.ids.password_count.text = str(len(password_list))

    def on_enter(self):
        app.logger.info('App: SCREEN: Dashboard')
        if not self.current_user:
            app.back_button(self, 27)
        if platform == 'android':
            shutil.rmtree(app.backup_dir, ignore_errors=True)

    def create_backup(self):
        if not app.has_storage_perms():
            return
        Window.unbind(on_key_up=app.back_button)
        app.loader.open()
        Clock.schedule_once(self.creating_backup, 0.7)

    def creating_backup(self, *args):
        if platform == "android":
            self.filename = self.current_user.text+".accountsafebackup"
            self.filepath = os.path.join(app.backup_dir, self.filename)
            if backups.save_backup(self.filepath):
                uri = FileProvider.getUriForFile(Context.getApplicationContext(
                ), Context.getApplicationContext().getPackageName() + ".fileprovider", File(self.filepath))
                if uri:
                    self.share.share_uri(uri)
            Window.bind(on_key_up=app.back_button)
            app.loader.dismiss()
            return

        def folder_chosen(selection):
            if selection:
                folder = selection[0]
                if type(folder) == list:
                    if folder:
                        folder = folder[0]
                    else:
                        self.backup_created(False)
                        return
                backup_path = os.path.join(
                    folder, 'krk', self.current_user.text+".accountsafebackup")
                self.backup_created(backups.save_backup(backup_path))
            else:
                self.backup_created(False)
        app.filechooser.choose_dir(
            title="Save backup", on_selection=folder_chosen)

    @mainthread
    def backup_created(self, result):
        Window.bind(on_key_up=app.back_button)
        app.loader.dismiss()
        if not result:
            self.snackbar.text = "Operation Cancelled"
            self.snackbar.open()
            return
        self.snackbar.text = "Backup saved successfully"
        self.snackbar.open()


Builder.load_file('dashboard.kv')
