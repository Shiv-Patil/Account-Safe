from kivymd.uix.screen import MDScreen
from kivy.lang import Builder
from kivymd.app import MDApp
app = MDApp.get_running_app()


class About(MDScreen):
    def on_enter(self):
        app.logger.info('App: SCREEN: About')


Builder.load_file('about.kv')
