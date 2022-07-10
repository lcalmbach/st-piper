import streamlit as st

import proj.database as db
from .parameter import Parameter
from query import qry
import helper



class Guideline():
    def __init__(self, id):
        self.set_guideline_info(id)

    def set_guideline_info(self, id):
        sql = qry['guideline_detail'].format(id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            self.id = df.iloc[0]['id']
            self.title = df.iloc[0]['title']
            self.title_short = df.iloc[0]['title_short']
            self.description = df.iloc[0]['description']

            sql = qry['guideline_items'].format(id)
            self.items_df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            self.items_df.set_index('id')
        else:
            self.id = -1
            self.title = None
            self.title_short = None
            self.description = None
        
    def find_match(self, par: Parameter):
        if par.sys_par_id != None:
            result = self.items_df[self.items_df['sys_par_id']==par.sys_par_id]
            result = dict(result.iloc[0]) if len(result)>0 else None
        elif par.casnr != None:
            result = self.items_df[self.items_df['casnr']==par.casnr]
            result = dict(result.iloc[0]) if len(result)>0 else None
            result = Standard(guideline=self, parameter=Parameter(id), max_value=result['max_value'], unit=result['unit'])
        else:
            result = None
        return result
    
    def get_parameter_dict(self, allow_none: bool=True):

        sql = qry['standard_parameter_list'].format(self.id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if ok:
            result = dict(zip(df['id'], df['parameter']))
            if allow_none:
                result = {-1:'Select parameter', **result}
        else:
            result = {}
        return result

    def get_standard(self,id:int):
        result = self.items_df.loc[id]
        result =  dict(result)
        standard = Standard(guideline=self, parameter=Parameter(id), max_value=result['max_value'], unit=result['unit'])
        return standard
    
    def __str__(self):
        return f'Guideline({self.title}, {len(self.items_df)} standards)'

class Standard():
    def __init__(self, guideline:Guideline, parameter: Parameter, unit: str = '', max_value: float=0, min_value: float=0):
        self.guideline = guideline
        self.parameter = parameter
        self.max_value = max_value
        self.min_value = min_value
        self.unit = unit
    
    def __str__(self):
        return f'Standard({self.guideline.title},{self.parameter.name},{self.max_value})'
