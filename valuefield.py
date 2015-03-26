import re
from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty
class ValueField(TextInput):
    
    def __init__(self, *args, **kwargs):
        self.next = kwargs.pop('next', None)
        self.multiline = False
        super(ValueField, self).__init__(*args, **kwargs)

    def set_next(self, next):
        self.next = next

    def _keyboard_on_key_down(self, window, keycode, text, modifiers):
        key, key_str = keycode
        if key in (9, 13) and self.next is not None:
            self.next.focus = True
            self.next.select_all()
            self.dispatch('on_text_validate')
        else:
            super(ValueField, self)._keyboard_on_key_down(window, keycode, text, modifiers)
            

class TextValueField(ValueField):
    max_len = NumericProperty(100)
    
    def insert_text(self, substring, from_undo=False):
        if len(self.text) < self.max_len:
            super(TextValueField, self).insert_text(substring, from_undo=from_undo)    
    
class NumericValueField(ValueField):
    min_value = NumericProperty(None, allownone=True)
    max_value = NumericProperty(None, allownone=True)

    def __init__(self, *args, **kwargs):
        super(NumericValueField, self).__init__(*args, **kwargs)
        self.bind(on_text_validate=self.validate_minmax)
    
    def validate_minmax(self, *args):
        try:
            value = int(self.text)
            if self.min_value is not None and value < self.min_value:
                self.text = str(self.min_value)
            if self.max_value is not None and value > self.max_value:
                self.text = str(self.max_value)
        except:
            pass        

class IntegerValueField(NumericValueField):
    pat = re.compile('[^0-9]')
        
    def insert_text(self, substring, from_undo=False):
        if '-'  in substring and not '-' in self.text:
            return super(IntegerValueField, self).insert_text(substring, from_undo=from_undo)
        
        s = re.sub(self.pat, '', substring)
        super(IntegerValueField, self).insert_text(s, from_undo=from_undo)
        
    
class FloatValueField(NumericValueField):
    pat = re.compile('[^0-9]')
    
    def insert_text(self, substring, from_undo=False):
        if '-' in substring and not '-' in self.text:
            return super(FloatValueField, self).insert_text(substring, from_undo=from_undo)
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        super(FloatValueField, self).insert_text(s, from_undo=from_undo)
            
