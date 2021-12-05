import pandas as pd

    
class Metadata():
    """
    This class holds all information on the parameters metadata
    the columns must be: 
    key;type;name;casnr;short_name;formula;fmw;valence;unit_cat;unit;is_mandatory

    Returns:
        [type]: [description]
    """
    def __init__(self):
        self.metadata_df = self.get_parameters()

    def get_parameters(self):
        df = pd.read_csv('./parameters_metadata.csv', sep=";")
        df = df.set_index('key')
        return df
    
    def key2par(self):
        result = zip(list(self.metadata_df.index), list(self.metadata_df['name']))
        return dict(result)