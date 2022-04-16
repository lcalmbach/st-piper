import encodings
import streamlit as st
import pandas as pd
from pathlib import Path

import const as cn
from metadata import Metadata
import helper

import database as db
from query import qry

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.config.language)


class Project():
    def __init__(self, id: int):
        ok = self.set_project_info(id)
        self.longitude_col = 'longitude'
        self.latitude_col = 'latitude'
        self._station_fields = None
        self.db_date_format = cn.DEFAULT_DATE_FORMAT

    def set_project_info(self, id:int):
        def get_parameters():
            sql = qry['project_parameters'].format(self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            df = df.set_index('id')
            return df

        sql = qry['project'].format(id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            ok = True
            self.id = df.iloc[0]['id']
            self.key = f"p{str(self.id).zfill(4)}"
            self.title = df.iloc[0]['title']
            self.short_name = df.iloc[0]['short_name']
            self.description= df.iloc[0]['description']
            self.row_is = df.iloc[0]['row_is']
            self.date_format = df.iloc[0]['date_format']
            self.separator = df.iloc[0]['separator']
            self.encoding = df.iloc[0]['encoding']
            self.is_public = df.iloc[0]['is_public']
            self.url_source = df.iloc[0]['url_source']
            self.owner_id = df.iloc[0]['owner_id']
            self.parameters_df = get_parameters()
            return True
        else:
            self.id = -1
            self.title = 'Enter a title'
            self.description= 'Enter a description'
            self.row_is = 'one value per row'
            self.date_format = '%Y/%m/%d'
            self.separator = ';'
            self.encoding = 'utf8'
            self.url_source = ''
            self.is_public = False
            self.owner_id = 0
            self.language = 'en'

            return True
    
    # properties -----------------------------------------------------------
    
    @property
    def station_fields(self):
        def get_station_fields():
            sql = qry['station_fields_ordered'].format(self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            result = '"id","' + '","'.join(list(df['parameter_name'])) + '"'
            return result
            
        if self._station_fields == None:
            self._station_fields = get_station_fields()
        return self._station_fields
       

    # functions ------------------------------------------------------------


    def get_station_df(self, station_id: int):
        sql = qry['station'].format(self.key, station_id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df


    def par_id(self, master_par_id: int) -> int:
        """
        returns the parameter id for a parameter in the current project given a master parameter id.

        Args:
            master_par_id (int): _description_

        Returns:
            int: project parameterid
        """
        result = self.parameters_df[self.parameters_df['sys_par_id'] == master_par_id]
        if len(result) > 0:
            return int(result.index.values[0])
        else:
            return None
    
    def par_name(self, master_par_id:int, field:str='parameter_name') -> int:
        """
        returns the parameter name for a parameter in the current project given a master parameter id.

        Args:
            master_par_id (int): _description_

        Returns:
            int: project parameterid
        """
        result = self.parameters_df[self.parameters_df['sys_par_id'] == master_par_id]
        if len(result) > 0:
            return int(result.iloc[0][field])
        else:
            return None

    def unit_conversion(self, par_id, unit_in, unit_out):
        def calc_concentration_conversion(par):
            fact = {'g/L': 1e3, 'mg/L': 1, 'μg/L)': 1e-3, 'ng/L':1e-6, 
                    'mol/L': par['fmw'] * 1e3, 'mMol/L': par['fmw'],'μMol/L': par['fmw'] * 1e-3, 'nMol/L': par['fmw'] * 1e-6,
                    'meq/L': par['fmw'] / abs(par['valence']), 'μeq/L': par['fmw'] / abs(par['valence']) * 1e-3
            }
            result = fact[unit_in] / fact[unit_out]
            return result
        
        def calc_length_conversion():
            fact = {'km': 1e3, 'cm': 1e-2, 'mm':1e-3, 'μm':1e-4
            }
            result = fact[unit_in] / fact[unit_out]
            return result

        par = self.parameters_df.loc[par_id]
        unit_in = par['unit'] if unit_in == None else unit_in
        if par['unit_cat'] in (cn.MOL_CONCENTRATION_CAT,cn.SIMPLE_CONCENTRATION_CAT):
            result = calc_concentration_conversion(par)
        elif par['unit_cat'] == cn.LENGTH_CAT:
            result = calc_length_conversion()
        else:
            result = 1
        return result


    def get_parameter_name_list(self, list_of_par_id:list, fieldname:str):
        """converts a list of master parameter ids to corresponsding field names: eg. formula, shortname, name

        Args:
            list_of_par_id (list): master parameter ids
            fieldname (str): name of field in master parameter table

        Returns:
            _type_: list of requested field
        """
        result = []
        for par_id in list_of_par_id:
            result.append(self.parameters_df.loc[par_id][fieldname])
        return result

    
    def master_par_id_2_par_id(self,par_list: list):
        """converts a list of system parameter id (metadata table) to the mapped parameter id of the current project

        Args:
            par_list (list): list of master parameter ids

        Returns:
            result: list of project parameter ids
            unmatched: list of master parameters not matched in the project parameter list
        """
        result=[]
        unmatched=[]
        for sys_par_id in par_list:
            par_id = self.parameters_df[self.parameters_df['sys_par_id']==sys_par_id]
            # if the parameter has been mapped
            if len(par_id) > 0:
                result.append(int(par_id.index.values[0]))
            # if parameter is not mapped
            else:
                unmatched.append(sys_par_id)
        return result, unmatched

    def save(self):
        if self.id > 0:
            sql = qry['update_project'].format(
                self.title.replace("'","''")
                ,self.description.replace("'","''")
                ,self.row_is 
                ,self.date_format
                ,self.separator
                ,self.encoding
                ,self.url_source
                ,self.is_public
                ,self.id) 
            ok, message = db.execute_non_query(sql, st.session_state.conn)
            message = 'Account settings have been saved successfully.' if ok else f"Account settings could not be save, the following error occurred: '{message}'"
        else:
            sql = qry['insert_project'].format(
                self.title 
                ,self.description
                ,self.row_is 
                ,self.date_format
                ,self.separator
                ,self.encoding
                ,self.url_source
                ,self.is_public
                ,st.session_state.config.user.id) #ownerid
            ok, message = db.execute_non_query(sql, st.session_state.conn)
            message = 'Project hase been created successfully.' if ok else f"Project could not be created, the following error occurred: '{message}'"
            if ok:
                sql = qry['max_project_id'].format(st.session_state.config.user.id)
                id = db.get_value(sql, st.session_state.conn)
                self.project = Project(id)
                #add to user_project table
                sql = qry['insert_user_project'].format(st.session_state.config.user.id, id, cn.PROJECT_OWNER)
                ok, err_msg = db.execute_query(sql, st.session_state.conn)

        return ok, message

    def configure_import(self):
        if self.row_is=="one value per row":
            imp = Value_per_row_import(self)
        else:
            imp = Sample_per_row_import(self)
        imp.run_step()

    def station_data(self):
        sql = qry['station_data'].format(self.station_fields, self.key, self.db_date_format )
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def station_samples(self, station_id):
        sql = qry['station_samples'].format(self.key, station_id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_data(self):
        sql = qry['parameter_data'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def sample_observations(self, station_id, sample_date):
        sql = qry['sample_observations'].format(self.key, station_id, sample_date)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_observations(self, parameter_id:int, filter: str):
        filter = " AND " + filter if filter >'' else ''
        sql = qry['parameter_observations'].format(self.key, parameter_id, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def get_station_list(self, allow_none: bool=False):
        # station_key = self.key2col()[cn.STATION_IDENTIFIER_COL]
        sql = qry['station_list'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        result = dict(zip(df['id'], df['identifier']))
        if allow_none:
            result = {-1:'Select stations', **result}
        return result
    
    def get_date_list(self, station_id: int, allow_none: bool=False):
        # station_key = self.key2col()[cn.STATION_IDENTIFIER_COL]
        sql = qry['date_list4station'].format(self.key, station_id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        result = dict(zip(df['date'], df['fmt_date']))
        if allow_none:
            result = {-1:'Select stations', **result}
        return result
    
    def get_parameter_dict(self, allow_none: bool=False, filter:str='')->dict:
        sql = qry['parameter_list'].format(self.key,filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if ok:
            result = dict(zip(df['id'], df['parameter_name']))
            #if allow_none:
            #    result = {-1:'Select parameter', **result}
        else:
            result = {}
        return result
    
    def min_max_date(self):
        sql = qry['min_max_sampling_date'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df.iloc[0]['min_date'], df.iloc[0]['max_date']
    
    def get_observations(self, filter_parameters:list, filter_stations:list):
        csv_parameters = ",".join(map(str, filter_parameters)) if len(filter_parameters)>0 else ''
        csv_stations = ",".join(map(str, filter_stations)) if len(filter_stations)>0 else ''
        filter = ''
        if csv_parameters > '':
            filter = f" AND parameter_id in ({csv_parameters})"
        if len(csv_stations)>0:
            filter += f" AND station_id in ({csv_stations})"
        sql = qry['observations'].format(self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

