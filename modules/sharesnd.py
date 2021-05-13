from kivy.core.window import Window
from kivy.clock import Clock
from jnius import autoclass, cast
from android import mActivity
JString = autoclass('java.lang.String')
Intent  = autoclass('android.content.Intent')

# Source https://github.com/RobertFlatt/Android-for-Python/share_snd

class ShareSend():
    
    def share_text(self, plain_text, app = None):
        try:
            self.plain_text = plain_text # for the gc
            self.send = Intent()
            self.send.setAction(Intent.ACTION_SEND)  
            self.send.setType("text/plain")
            self.send.putExtra(Intent.EXTRA_TEXT, JString(self.plain_text))
            if app:
                self.send.setPackage(app)
                mActivity.startActivity(self.send)
            else:
                self.send1 = Intent.createChooser(self.send,None)
                mActivity.startActivity(self.send1)
            Clock.schedule_once(self.begone_you_black_screen)
        except Exception as e:
            print('ERROR: ShareSnd().share_text()'+str(e))

    def share_uri(self, uri, app = None):
        try:
            cr =  mActivity.getContentResolver()
            self.MIME = cr.getType(uri)
            self.uri = uri
            self.parcelable = cast('android.os.Parcelable', self.uri)  
            self.send = Intent()
            self.send.setAction(Intent.ACTION_SEND)  
            self.send.setType(self.MIME)
            self.send.putExtra(Intent.EXTRA_STREAM, self.parcelable)
            self.send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            if app:
                self.send.setPackage(app)
                mActivity.startActivity(self.send)
            else:
                self.send1 = Intent.createChooser(self.send,None)
                mActivity.startActivity(self.send1)
            Clock.schedule_once(self.begone_you_black_screen)
        except Exception as e:
            print('ERROR: ShareSnd().share_uri()'+str(e))

    # On return from a share recipient which has taken the screen,
    # this Kivy app has a black screen, but its event loop is running.
    # This workaround is scheduled to occur during the app's pause sequence.
    # Thus presumably the update_viewport is de-queued when resume happens.
    # And the screen is not black.
    def begone_you_black_screen(self,dt):
        Window.update_viewport()