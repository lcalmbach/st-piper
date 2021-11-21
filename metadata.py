import pandas as pd

class Metdata():
    def __init__(self):
        self.metadata_df = self.get_parameters()

    def get_parameters(self):
        df = pd.read_csv('./parameters_metadata.csv', sep=";")
        df = df.set_index('key')
        return df