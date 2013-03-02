class Option(object):
    def __init__(self, name, help_text,
            check=None, converter=None, choices=None):
        self.name = name
        self.help_text = help_text
        self.check = check
        self.converter = converter or str
        self.choices = choices
