# File/Directory picker for android
# Source https://github.com/RobertFlatt/Android-for-Python/storage

from kivy.core.window import Window
from kivy.clock import Clock
from android import activity, mActivity
from jnius import autoclass
import traceback

Intent = autoclass('android.content.Intent')
JString = autoclass('java.lang.String')


class Picker():
    def __init__(self, **kwargs):
        self.REQUEST_CODE = 42
        self.callback = None
        activity.bind(on_activity_result=self.intent_callback)

    def __del__(self):
        activity.unbind(on_activity_result=self.intent_callback)

    def open_file(self, title="Choose a file", on_selection=None, MIME_type='*/*'):
        self.callback = on_selection
        try:
            self.file_msg = title
            self.file_intent = Intent(Intent.ACTION_GET_CONTENT)
            self.file_intent.setType(MIME_type)
            self.file_intent2 = Intent.createChooser(
                self.file_intent, JString(self.file_msg))
            mActivity.startActivityForResult(
                self.file_intent2, self.REQUEST_CODE)
            Clock.schedule_once(self.begone_you_black_screen)
        except Exception as e:
            print('ERROR Picker.open_file(): ' + str(e))
            traceback.print_exc()

    def choose_dir(self, title="Choose a directory", on_selection=None):
        self.callback = on_selection
        try:
            self.folder_msg = title
            self.folder_intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
            self.folder_intent.addCategory(Intent.CATEGORY_DEFAULT)
            self.folder_intent2 = Intent.createChooser(
                self.folder_intent, JString(self.folder_msg))
            mActivity.startActivityForResult(
                self.folder_intent2, self.REQUEST_CODE)
            Clock.schedule_once(self.begone_you_black_screen)
        except Exception as e:
            print('ERROR Picker.choose_dir(): ' + str(e))
            traceback.print_exc()

    def intent_callback(self, requestCode, resultCode, intent):
        if requestCode == self.REQUEST_CODE:
            if resultCode == 0:
                self.callback(None)
                return
            try:
                if intent:
                    self.callback(intent.getData())
            except Exception as e:
                print('ERROR Picker.intent_callback():' + str(e))
                traceback.print_exc()

    def begone_you_black_screen(self, dt):
        Window.update_viewport()
