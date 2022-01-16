import pandas as pandas

class Master_parameters():
    pass

class Parameter:
    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.column_name = kwargs['column_name']
        