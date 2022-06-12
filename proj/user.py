import streamlit as st

from query import qry
import database as db
import json
import pandas as pd

import helper
import const as cn

class User():
    def __init__(self, email):
        self.email = email
        self.set_user_info()

    def set_user_info(self):
        ok = False
        sql = qry['user_info'].format(self.email)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            ok = True
            rec = df.iloc[0]
            self.id = rec['id']
            self.first_name = rec['first_name']
            self.last_name = rec['last_name']
            self.company = rec['company']
            self.country = rec['country']
            self.language = rec['language']
            self.default_project = rec['default_project']
        else:
            self.id = -1
            self.first_name = None
            self.last_name = None
            self.company = None
            self.country = None
            self.language = 'en'
            self.default_project = cn.DEFAULT_PROJECT


    def save(self):
        sql = qry['update_user'].format(self.first_name, 
            self.last_name, 
            self.company,
            self.country,
            self.language,
            self.email) 
        ok, message = db.execute_non_query(sql, st.session_state.conn)
        message = 'Account settings have been saved successfully.' if ok else f"Account settings could not be save, the following error occurred: '{message}'"
        if ok:
            pass #st.session_state.config.language = self.language
        return ok, message


    def delete(self):
        """dummy routine for deleting a user

        Returns:
            [ok]:       boolean, result if account could be deleted
            message:    success of warning text depending on delete result
        """
        message = "Account for {self.firstname} {self.lastname} has been locked. All datasets will be deleted automatically in 7 days."
        ok = True
        return message, ok
    

    def save_password(self, pwd):
        sql = qry['update_password'].format(pwd, self.email) 
        ok, message = db.execute_non_query(sql, st.session_state.conn)
        message = 'Password was saved successfully.' if ok else f"Password could not be save, the following error occurred: '{message}'"
        return ok, message
    

    def read_config(self, an_config_id:int, setting_name: str):
        sql = qry['get_analysis_config'].format(self.id, an_config_id, setting_name) 
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        cfg = df.iloc[0]['config'] if ok else {}
        return cfg
    

    def save_config(self, an_config_id:int, setting_name: str, cfg:dict):
        # check if there is a an entry, otherwise create it
        cfg = json.dumps(cfg)
        sql = qry['update_analysis_config'].format(cfg, self.id, an_config_id, setting_name)
        ok, err_msg = db.execute_non_query(sql, st.session_state.conn)
        return ok
    
    def is_logged_in(self)->bool:
        """
        Returns true if user-id is > 1, where 1 is the default anonymous user
        """
        return (self.id > 1)

    def _get_user_project_df(self)->pd.DataFrame:
        if self.is_logged_in():
            sql = qry['user_projects'].format(self.id)
        else:
            sql = qry['public_projects']
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def get_user_projects(self)->dict:
        df = self._get_user_project_df()
        dic = dict(zip(df['id'], df['title']))
        return dic, df
