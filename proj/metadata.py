import pandas as pd
from pathlib import Path
from query import qry
import proj.database as db
from streamlit import session_state
import const as cn
    
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
        self.map_parameter2id = dict(zip(list(self.metadata_df['key']), list(self.metadata_df['id'])))
        self.map_id2parameter = dict(zip(list(self.metadata_df['id']), list(self.metadata_df['key'])))

    def get_parameters(self):
        sql = qry['sys_parameters']
        df, ok, err_msg = db.execute_query(sql, session_state.conn)
        return df
    
    def key2par(self):
        result = zip(list(self.metadata_df.index), list(self.metadata_df['name']))
        return dict(result)