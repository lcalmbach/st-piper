import pandas as pd
from pathlib import Path
from query import qry
import database as db
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

    def unit_conversion(self, par_id, unit_in, unit_out):
        def calc_concentration_conversion(par):
            fact = {'g/L': 1e3, 'μg/l)': 1e-3, 'ng/l':1e-6, 
                    'mol/l': par['fmw'] * 1e3, 'mmol/l': par['fmw'],'μmol/l': par['fmw'] * 1e-3, 'nmol/L': par['fmw'] * 1e-6,
                    'meq/l': par['fmw'] * par['valence'], 'μeq/l': par['fmw'] * par['valence'] * 1e-3
            }
            result = fact[unit_in] / fact[unit_out]
            return result
        
        def calc_length_conversion():
            fact = {'km': 1e3, 'cm': 1e-2, 'mm':1e-3, 'μm':1e-4
            }
            result = fact[unit_in] / fact[unit_out]
            return result

        print(unit_in, unit_out)
        par = self.metadata_df[self.metadata_df['id']==par_id].iloc[0]
        print(par)
        unit_in = par['unit'] if unit_in == None else unit_in

        if par['unit_cat'] in (cn.MOL_CONCENTRATION_CAT,cn.SIMPLE_CONCENTRATION_CAT):
            result = calc_concentration_conversion(par)
        elif par['unit_cat'] == cn.LENGTH_CAT:
            result = calc_length_conversion()
        else:
            result = 1
        return result