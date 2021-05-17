from kivymd.uix.textfield import MDTextField
from kivy.lang import Builder
from kivy.factory import Factory


class TextField(MDTextField):
    helper_text_color = None
    def __init__(self, **kwargs):
        super(TextField, self).__init__(**kwargs)


kv = """
<TextField>

    canvas.before:
        Clear

        # Disabled line.
        Color:
            rgba:
                (self.line_color_normal \
                if self.line_color_normal else self.theme_cls.divider_color) \
                if root.mode == "line" else (0, 0, 0, 0)
        Line:
            points: self.x, self.y + dp(16), self.x + self.width, self.y + dp(16)
            width: 1
            dash_length: dp(3)
            dash_offset: 2 if self.disabled else 0

        # Active line.
        Color:
            rgba: self._current_line_color if root.mode in ("line", "fill") and root.active_line else (0, 0, 0, 0)
        Rectangle:
            size: self._line_width, dp(2)
            pos: self.center_x - (self._line_width / 2), self.y + (dp(16) if root.mode != "fill" else 0)

        # Helper text.
        Color:
            rgba: self._current_error_color if not self.helper_text_color else self.helper_text_color
        Rectangle:
            texture: self._msg_lbl.texture
            size:
                self._msg_lbl.texture_size[0] - (dp(3) if root.mode in ("fill", "rectangle") else 0), \
                self._msg_lbl.texture_size[1] - (dp(3) if root.mode in ("fill", "rectangle") else 0)
            pos: self.x + (dp(8) if root.mode == "fill" else 0), self.y + (dp(3) if root.mode in ("fill", "rectangle") else 0)

        # Texture of right Icon.
        Color:
            rgba: self.icon_right_color if self.focus else self._current_hint_text_color
        Rectangle:
            texture: self._lbl_icon_right.texture
            size: self._lbl_icon_right.texture_size if self.icon_right else (0, 0)
            pos:
                (self.width + self.x) - (self._lbl_icon_right.texture_size[1]) - dp(8), \
                self.center[1] - self._lbl_icon_right.texture_size[1] / 2 + (dp(8) if root.mode != "fill" else 0) \
                if root.mode != "rectangle" else \
                self.center[1] - self._lbl_icon_right.texture_size[1] / 2 - dp(4)

        Color:
            rgba: self._current_right_lbl_color
        Rectangle:
            texture: self._right_msg_lbl.texture
            size: self._right_msg_lbl.texture_size
            pos: self.x + self.width - self._right_msg_lbl.texture_size[0] - dp(16), self.y

        Color:
            rgba:
                (self._current_line_color if self.focus and not \
                self._cursor_blink else (0, 0, 0, 0))
        Rectangle:
            pos: (int(x) for x in self.cursor_pos)
            size: 1, -self.line_height

        # Hint text.
        Color:
            rgba: self._current_hint_text_color if not self.current_hint_text_color else self.current_hint_text_color
        Rectangle:
            texture: self._hint_lbl.texture
            size: self._hint_lbl.texture_size
            pos: self.x + (dp(8) if root.mode == "fill" else 0), self.y + self.height - self._hint_y

        Color:
            rgba:
                self.disabled_foreground_color if self.disabled else\
                (self.hint_text_color if not self.text and not\
                self.focus else self.foreground_color)

        # "rectangle" mode
        Color:
            rgba:
                (self._current_line_color if not self.text_color else self.text_color) \
                if self.focus else self._current_hint_text_color
        Line:
            width: dp(1) if root.mode == "rectangle" else dp(0.00001)
            points:
                (
                self.x + root._line_blank_space_right_point, self.top - self._hint_lbl.texture_size[1] // 2,
                self.right + dp(12), self.top - self._hint_lbl.texture_size[1] // 2,
                self.right + dp(12), self.y,
                self.x - dp(12), self.y,
                self.x - dp(12), self.top - self._hint_lbl.texture_size[1] // 2,
                self.x + root._line_blank_space_left_point, self.top - self._hint_lbl.texture_size[1] // 2
                )

    # "fill" mode.
    canvas.after:
        Color:
            rgba: root._fill_color if root.mode == "fill" else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.x, self.y
            size: self.width, self.height + dp(8)
            radius: root.radius

    font_name: "Roboto" if not root.font_name else root.font_name
    foreground_color: self.theme_cls.text_color
    bold: False
    padding:
        0 if root.mode != "fill" else "8dp", \
        "16dp" if root.mode != "fill" else "24dp", \
        0 if root.mode != "fill" and not root.icon_right else ("14dp" if not root.icon_right else self._lbl_icon_right.texture_size[1] + dp(20)), \
        "16dp" if root.mode == "fill" else "10dp"
    multiline: False
    size_hint_y: None
    height: self.minimum_height + (dp(8) if root.mode != "fill" else 0)
"""

Builder.load_string(kv)

Factory.register("TextField", TextField)
