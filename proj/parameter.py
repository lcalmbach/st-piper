import streamlit as st

import database as db
from query import qry

class Parameter():
    def __init__(self, id):

        self.set_parameter_info(id)

    def set_parameter_info(self,id):
        global lang

        ok = False
        sql = qry['parameter_detail'].format(st.session_state.project.key, id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            self.id = df.iloc[0]['id']
            self.name = df.iloc[0]['parameter_name']
            self.casnr = df.iloc[0]['casnr']
            self.group1 = df.iloc[0]['group1']
            self.group2 = df.iloc[0]['group1']
            self.sys_par_id = df.iloc[0]['master_parameter_id']
        else:
            self.id = -1
            self.title = None
            self.title_short = None
            self.description = None