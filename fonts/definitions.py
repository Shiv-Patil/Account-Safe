from kivy.core.text import LabelBase
import os

def add_fonts(resource_path):
    FONTS = [
        {
            "name": "Poppins",
            "fn_regular": resource_path(os.path.join('fonts', 'Poppins', 'Poppins-Regular.ttf')),
            "fn_bold": resource_path(os.path.join('fonts', 'Poppins', 'Poppins-Bold.ttf')),
            "fn_italic": resource_path(os.path.join('fonts', 'Poppins', 'Poppins-Italic.ttf')),
            "fn_bolditalic": resource_path(os.path.join('fonts', 'Poppins', 'Poppins-BoldItalic.ttf'))
        }
    ]
    for font in FONTS:
        LabelBase.register(**font)
