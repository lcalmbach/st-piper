import encodings
from sys import settrace
import streamlit as st
import pandas as pd
import numpy as np
import uuid
import json
from pathlib import Path
import random

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

            return True
    
    # properties -----------------------------------------------------------


    # functions ------------------------------------------------------------
    def get_parameter_name_list(self, list_of_par_id:list, fieldname:str):
        """converts a list of master parameter ids to corresponsding field names: eg. formula, shortname, name

        Args:
            list_of_par_id (list): master parameter ids
            fieldname (str): name of field in master parameter table

        Returns:
            _type_: list of requested field
        """
        _df = self.parameters_df.reset_index()
        _df = _df[_df['id'].isin(list_of_par_id)]
        dic = dict(zip(list(_df['id']), list(_df[fieldname])))
        result = [dic[item] for item in list_of_par_id]
        return result
    
    def master_par_id_2_par_id(self,par_list: list):
        """converts a list of system parameter id (metadata table) to the mapped parameter id of the current project

        Args:
            par_list (list): list of master parameter ids

        Returns:
            _type_: list of project parameter ids
        """
        result=[]
        for sys_par_id in par_list:
            par_id = self.parameters_df[self.parameters_df['sys_par_id']==sys_par_id]
            # if the parameter has been mapped
            if len(par_id) > 0:
                result.append(par_id.iloc[0]['id'])
            # if parameter is not mapped
            else:
                result.append(None)
        return result

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
        sql = qry['station_data'].format(self.key)
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
        if csv_parameters>'':
            filter = f" AND parameter_id in ({csv_parameters})"
        if len(csv_stations)>0:
            filter = f" AND station_id in ({csv_stations})"
        sql = qry['observations'].format(self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df


class User():
    def __init__(self, email):
        self.email = email
        self.set_user_info()

    def set_user_info(self):
        global lang

        ok = False
        sql = qry['user_info'].format(self.email)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            ok = True
            self.id = df.iloc[0]['id']
            self.first_name = df.iloc[0]['first_name']
            self.last_name = df.iloc[0]['last_name']
            self.company = df.iloc[0]['company']
            self.country = df.iloc[0]['country']
            self.language = df.iloc[0]['language']
            self.default_project = df.iloc[0]['default_project']
        else:
            self.id = -1
            self.first_name = None
            self.last_name = None
            self.company = None
            self.country = None
            self.language = 'en'
            self.default_project = cn.DEFAULT_PROJECT
        lang = helper.get_language(__name__, 'en')

    
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
            st.session_state.config.language = self.language
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


class Parameter():
    def __init__(self, id):

        self.set_parameter_info(id)

    def set_parameter_info(self,id):
        global lang

        ok = False
        sql = qry['parameter_detail'].format(st.session_state.config.project.key, id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        if len(df)>0:
            self.id = df.iloc[0]['id']
            self.name = df.iloc[0]['parameter_name']
            self.casnr = df.iloc[0]['casnr']
            self.group1 = df.iloc[0]['group1']
            self.group2 = df.iloc[0]['group1']
            self.sys_par_id = df.iloc[0]['sys_par_id']
        else:
            self.id = -1
            self.title = None
            self.title_short = None
            self.description = None


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
        result = None
        if par.sys_par_id != None:
            result = self.items_df[self.items_df['sys_par_id']==par.sys_par_id]
            result = dict(result.iloc[0]) if len(result)>0 else None
        elif par.casnr != None:
            result = self.items_df[self.items_df['casnr']==par.casnr]
            result = dict(result.iloc[0]) if len(result)>0 else None
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
        return dict(result)


class Config():
    def __init__(self):
        self.language = 'en'
        lang = helper.get_language(__name__, self.language)
        self.session_key = uuid.uuid1()
        self.logged_in_user = None
        self.pwd = None
        self.title = ''
        self.encoding = cn.ENCODINGS[0]
        self.separator = cn.SEPARATORS[0]
        self.date_format = cn.DATE_FORMAT_LIST[0]
        self._row_sample_df = pd.DataFrame()
        self._row_value_df = pd.DataFrame()
        self._column_map_df = pd.DataFrame({'column_name': [], 'key': []})
        self._parameter_map_df = pd.DataFrame({'parameter': [], 'casnr': [], 'key': []})
        self.load_config_from_file_flag = False
        self.file_format = ''
        self.date_is_formatted = False
        self.params_params_valid = False
        self.lookup_parameters = Metadata() # metadata for a wide selection of parameters 
        self.time_stations_config = {}
        self.time_parameters_config = {}
        self.map_parameters_config = {}
        self.projects_df = self.get_projects()
        self.unit_row = 1

        self._project = {}
        self.user = User('x')
        
        self.step = 0
        # true if either the value column is mapped or if the qual-value col is mapped and 
        # the value and detection-flag column is generated
        self.value_col_is_filled: bool = False 
        # true if either the qual-value column is mapped or if the value and qual cols are mapped and 
        # the qual-value is generated

# properties---------------------------------------------------------------------------------------
    @property
    def project_dict(self)->dict:
        df = pd.DataFrame(self.projects_df)
        dic = dict(zip(df['id'], df['title']))
        return dic

    @property
    def project(self):
        return self._project
       
    @project.setter
    def project(self, prj:Project):
        self._project = prj

    @property
    def row_sample_df(self):
        return self._row_sample_df
       
    @row_sample_df.setter
    def row_sample_df(self, df):
        self._row_sample_df = df
        if self.major_ions_complete:
            df = helper.complete_columns(df, self.key2par(), self.lookup_parameters.metadata_df)

    @property
    def row_value_df(self):
        return self._row_value_df
       
    @row_value_df.setter
    def row_value_df(self, df):
        self._row_value_df = df
        self.init_column_map()

    @property
    def column_map_df(self):
        return self._column_map_df
       
    @column_map_df.setter
    def column_map_df(self, column_map):
        self._column_map_df = column_map
        self._column_map_df.set_index('column_name', inplace=True)
        self.check_columns()
        
    @property
    def parameter_map_df(self):
        return self._parameter_map_df
       
    @parameter_map_df.setter
    def parameter_map_df(self, parameter_map):
        self._parameter_map_df = parameter_map
        self._parameter_map_df.set_index('parameter', inplace=True)

    @property
    def longitude_col(self) -> str:
        return self.key2col()[cn.LONGITUDE_COL]

    @property
    def latitude_col(self) -> str:
        return self.key2col()[cn.LATITUDE_COL]

    @property
    def station_col(self) -> str:
        return self.key2col()[cn.STATION_IDENTIFIER_COL]

    @property
    def parameter_col(self) -> str:
        return self.key2col()[cn.PARAMETER_COL]

    @property
    def value_col(self) -> str:
        return self.key2col()[cn.VALUE_NUM_COL]

    @property
    def sample_cols(self) -> list:
        return list(self.coltype2dict(cn.CTYPE_SAMPLE).keys())
    
    @property
    def station_cols(self) -> list:
        return list(self.coltype2dict(cn.CTYPE_STATION).keys())
    
    @property
    def sample_station_cols(self) -> list:
        """
        returns the list of all station and sample related parameters. Often, these are used to for grouping
        """
        fields = self.sample_cols
        fields += self.station_cols
        return fields

    @property
    def parameter_list(self) -> list:
        return list(self.parameter_map_df.index)

    @property
    def date_col(self) -> str:
        return self.key2col()[cn.SAMPLE_DATE_COL]

    @property
    def sample_identifier_col(self) -> str:
        if self.col_is_mapped(cn.SAMPLE_IDENTIFIER_COL):
            return self.key2col()[cn.SAMPLE_IDENTIFIER_COL]
        elif self.col_is_mapped(cn.DATE_IDENTIFIER_COL):
            return self.key2col()[cn.DATE_IDENTIFIER_COL]
        else:
            return None
    @property
    def major_ions_complete(self):
        ok = (self.par_is_mapped(cn.PAR_CALCIUM)
                and self.par_is_mapped(cn.PAR_MAGNESIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_SODIUM)
                and self.par_is_mapped(cn.PAR_ALKALINITY)
                and self.par_is_mapped(cn.PAR_SULFATE)
                and self.par_is_mapped(cn.PAR_CHLORIDE))
        return ok
    
    @property
    def logged_in_user_name(self):
        return 'please login'if self.logged_in_user == None else self.logged_in_user


# functions----------------------------------------------------------------------------------------
    def get_guideline_dict(self)->pd.DataFrame:
        sql = qry['guidelines']
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        result = dict(zip(df['id'], df['title']))
        return result
    

    def get_projects(self)->pd.DataFrame:
        if self.is_logged_in():
            sql = qry['user_projects'].format(self.user.id)
        else:
            sql = qry['public_projects']
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
        
    def check_columns(self):
        """
        sets the format of matched columns such as date column. This is only possible if the sample_row df 
        exists. todo: call this for each dataframe : values as row and sample. then the columns are fixed when they are present
        """
        if len(self._row_value_df) > 0:
            if self.col_is_mapped(cn.SAMPLE_DATE_COL):
                self.format_date_column(self._row_value_df)
            if self.col_is_mapped(cn.GEOPOINT_COL):
                self.geopoint_to_lat_long(self._row_value_df)
            if self.col_is_mapped(cn.ND_QUAL_VALUE_COL):
                self.split_qual_val_column()
            if self.col_is_mapped(cn.LATITUDE_COL):
                self._row_value_df[self.latitude_col] = self._row_value_df[self.latitude_col].astype(float)
                self._row_value_df[self.longitude_col] = self._row_value_df[self.longitude_col].astype(float)
        
        # same for row as sample format datafram
        if len(self._row_sample_df) > 0:
            if self.col_is_mapped(cn.SAMPLE_DATE_COL):
                self.format_date_column(self._row_sample_df)
                if not 'year' in self._row_sample_df.columns:
                    self._row_sample_df['year'] = self._row_sample_df[self.date_col].dt.year
            if self.col_is_mapped(cn.LATITUDE_COL):
                self._row_sample_df[self.latitude_col] = self._row_sample_df[self.latitude_col].astype(float)
                self._row_sample_df[self.longitude_col] = self._row_sample_df[self.longitude_col].astype(float)
    
    def load_data(self, ds):
        def data_file():
            """
            required format: 000001_data.csv
            """
            result = str(self.project.id).rjust(6,'0') +'_data.csv'
            return result
        
        def parameter_map_file():
            result = str(self.project.id).rjust(6,'0') +'_parameters.csv'
            return result
        
        def column_map_file():
            result = str(self.project.id).rjust(6,'0') +'_columns.csv'
            return result

        def import_row_value():
            def pivot_data():
                sample_cols = self.sample_cols
                station_cols = self.station_cols
                group_cols = sample_cols + station_cols
                self.row_sample_df = pd.pivot_table(self.row_value_df,
                    values=self.value_col,
                    index=group_cols,
                    columns=self.parameter_col,
                    aggfunc=np.mean
                ).reset_index()

            # read the data
            folder = Path("data/")
            self.date_format = self.project.date_format
            self.row_value_df = pd.read_csv(folder / data_file(), 
                                            sep=self.project.separator, 
                                            encoding=self.project.encoding)
            # read column mapping
            self.column_map_df = pd.read_csv(folder / column_map_file(), sep=';')

            # read parameter mapping
            self.parameter_map_df = pd.read_csv(folder / parameter_map_file(), sep=';')
            pivot_data()

        def import_row_sample():
            """
            data in the format 1 row per sample are melted to the format 1 row per value: the values are grouped by station 
            and sample fields. the additional parameter rows each build a new row per row.
            """

            def melt_data():
                df = pd.melt(frame=self.row_sample_df,
                                             id_vars=self.sample_station_cols, 
                                             value_vars = self.parameter_list,
                                             var_name = 'parameter',
                                             value_name = 'value'
                )
                df['unit'] = ''
                df['detection_limit'] = 0
                return df


            # read the data
            folder = Path("data/")
            self.date_format = self.project.date_format
            self.row_sample_df = pd.read_csv(folder / data_file(), 
                                            sep=self.project.separator, 
                                            encoding=self.project.encoding)
            # read column mapping
            self.column_map_df = pd.read_csv(folder / column_map_file(), sep=';')
            df = self.column_map_df
            df = df[df['type'].isin(['sa', 'st'])]
            df.loc['parameter'] = [cn.PARAMETER_COL, cn.CTYPE_VAL_META, None]
            df.loc['value'] = [cn.ND_QUAL_VALUE_COL, cn.CTYPE_VAL_META, None]
            df.loc['num_value'] = [cn.VALUE_NUM_COL, cn.CTYPE_VAL_META, None]
            df.loc['unit'] = [cn.UNIT_COL, cn.CTYPE_VAL_META, None]
            df.loc['detection_limit'] = [cn.DL_COL, cn.CTYPE_VAL_META, None]
            self.column_map_df = df.reset_index()
            
            # read parameter mapping
            self.parameter_map_df = pd.read_csv(folder / parameter_map_file(), sep=';')
            self._row_value_df = melt_data()
            # trigger set column map, since only now all information is available. this triggers the formatting of essential 
            # columns such as date
            self.check_columns()
            

        def init_data():
            self._row_value_df = pd.DataFrame()
            self._row_sample_df = pd.DataFrame()
            self._column_map_df = pd.DataFrame()
            self._parameter_map_df = pd.DataFrame()

        init_data()
        if self.project.row_is == "one value per row":
            import_row_value()
        else:
            import_row_sample()

    def read_all_guidelines(self):
        with open(f"{cn.GUIDELINE_ROOT}guidelines.json") as f:
            guidelines_df = pd.DataFrame(json.load(f))
        return guidelines_df

    def read_guideline_data(self):
        data = pd.DataFrame()
        for index, row in self.guidelines_df.iterrows():
            filename = f"{cn.GUIDELINE_ROOT}{row['filename']}"
            df =  pd.read_csv(filename, sep='\t')
            df['key'] = row['key']
            data = data.append(df, ignore_index=True)
        return data

    def init_column_map(self):
        ok, err_msg = True, ''
        try:
            df = pd.DataFrame({'column_name': list(self.row_value_df)})
            df['key'] = cn.NOT_USED
            df['type'] = None
            self.column_map_df = df
        except:
            ok = False
            err_msg = 'Column map could not be initialized'
        return ok
    
    def get_plots_options(self):
        result = []
        result.append("Scatter")
        result.append("Histogram")
        result.append("Boxplot")
        if self.col_is_mapped(cn.SAMPLE_DATE_COL):
            result.append("Time series")
        if self.col_is_mapped(cn.LATITUDE_COL):
            result.append("Map")
        if self.major_ions_complete:
            result.append("Piper")
            result.append("Schoeller")

        return result

    def par_is_mapped(self, key_name):
        ok = key_name in list(self.parameter_map_df['key']) if len(self.parameter_map_df) > 0 else False
        return ok

    def col_is_mapped(self, key_name):
        ok = key_name in list(self.column_map_df['key']) if len(self.column_map_df) > 0 else False
        return ok

    def coltype2dict(self, col_type):
        df = self.column_map_df[self.column_map_df['type'] == col_type]
        result = zip(list(df.index), list(df.key))
        return dict(result)

    def col2key(self) -> dict:
        result = zip(list(self.column_map_df.index), list(self.column_map_df.key))
        return dict(result)


    def key2col(self) -> dict:
        df = self.column_map_df[self.column_map_df['key'] != cn.NOT_USED]
        result = zip(list(df['key']), list(df.index))
        return dict(result)

    def par2casnr(self) -> dict:
        result = zip(list(self.parameter_map_df.index), list(self.parameter_map_df.casnr))
        return dict(result)

    def par2key(self) -> dict:
        result = zip(list(self.parameter_map_df.index), list(self.parameter_map_df.key))
        return dict(result)


    def key2par(self)->dict:
        df = self.parameter_map_df[self.parameter_map_df['key'] != cn.NOT_USED]
        result = zip(list(df['key']), list(df.index))
        return dict(result)


    def merge_qual_val_column(self):
        """if value and qualifier are mapped in seperate columns, these 2 columns are additionall merged in
        a common column e.g. | < | 0.05 | becomes <0.05

        Returns:
            [type]: [description]
        """
        ok = False
        val_col = self.key2col()[cn.VALUE_NUM_COL]
        qual_col = self.key2col()[cn.ND_QUAL_COL]
        if qual_col != None:
            val_qual_col = '_qual_value'
            self.row_value_df[val_qual_col] = ''  
            self.row_value_df.loc[self.row_value_df[qual_col]=='<',val_qual_col] = self.row_value_df[qual_col] + self.row_value_df[val_col]
        
        self.value_col_is_filled = True
        ok = True
        return ok

    def split_qual_val_column(self):
        ok = False
        qual_val_col = self.key2col()[cn.ND_QUAL_VALUE_COL]
        nd_flag_col = cn.ND_FLAG_COL
        df = self.row_value_df

        df[qual_val_col] = df[qual_val_col].astype(str)
        df[nd_flag_col] = False
        df.loc[df[qual_val_col].str.startswith('<') == True, nd_flag_col] = True
        df.loc[df[nd_flag_col] == True, cn.VALUE_NUM_COL] = df[qual_val_col].str.replace('<', '')
        df.loc[(df[nd_flag_col] == False), cn.VALUE_NUM_COL] = pd.to_numeric(df[qual_val_col],errors='coerce') 
        df[cn.VALUE_NUM_COL] = df[cn.VALUE_NUM_COL].astype('float') 
        df.loc[(df[nd_flag_col] == True) & (df[cn.VALUE_NUM_COL] != 0), cn.VALUE_NUM_COL] = df[cn.VALUE_NUM_COL] / 2
        self.column_map_df.loc[cn.VALUE_NUM_COL] = [cn.VALUE_NUM_COL, cn.CTYPE_VAL_META, None]
        self.qual_value_col_is_filled = True
        ok = True
        return ok


    def format_date_column(self, df):
        ok = False
        try:
            df[self.date_col] = pd.to_datetime(df[self.date_col], format=self.date_format, errors='ignore')
            print('date column was formatted')
            ok = True
        except:
            print('date column could not be formatted')
        return ok


    def stations_params_valid(self):
        result = cn.STATION_IDENTIFIER_COL in list(self.column_map_df['key'])
        return result
    
    def sample_params_valid(self):
        result = cn.SAMPLE_IDENTIFIER_COL in list(self.column_map_df['key']) 
        result = result or cn.SAMPLE_DATE_COL in list(self.column_map_df['key'])
        return result

    def meta_params_valid(self):
        result = cn.VALUE_COL in list(self.column_map_df['key'])
        result = result or cn.DESC_VALUE_COL in list(self.column_map_df['key'])
        result = result and cn.PARAMETER_COL in list(self.column_map_df['key'])

    def has_casnr(self):
        """
        Returns true if casnr and parameter key has been mapped.

        Returns:
            [type]: [description]
        """
        result = cn.CASNR_COL in list(self.column_map_df['key'])
        result = result and cn.PARAMETER_COL in list(self.column_map_df['key'])
        return result

    def geopoint_to_lat_long(self, df):
        ok,err_msg = True,''
        col_name = self.key2col()[cn.GEOPOINT_COL]
        df[[cn.LATITUDE_COL, cn.LONGITUDE_COL]] = df[col_name].str.split(',', expand=True)
        df = self.column_map_df
        df.loc[cn.LATITUDE_COL] = [cn.LATITUDE_COL, cn.CTYPE_STATION, None]
        df.loc[cn.LONGITUDE_COL] = [cn.LONGITUDE_COL, cn.CTYPE_STATION, None]
        return ok, err_msg

    def get_parameter_detail_form_columns(self):
        """Returns a list of columns used to display a single sample depending on what columns have been
        mapped. 

        Returns:
            [type]: [description]
        """
        lst_cols = [self.key2col()[cn.PARAMETER_COL]]
        if self.col_is_mapped(cn.UNIT_COL):
            lst_cols.append(self.key2col()[cn.UNIT_COL])
        if self.col_is_mapped(cn.CASNR_COL):
            lst_cols.append(self.key2col()[cn.CASNR_COL])
        if self.col_is_mapped(cn.ND_QUAL_VALUE_COL):
            lst_cols.append(self.key2col()[cn.ND_QUAL_VALUE_COL])
            lst_cols.append(self.key2col()[cn.VALUE_NUM_COL])
        if self.col_is_mapped(cn.DL_COL):
            lst_cols.append(self.key2col()[cn.DL_COL])
            lst_cols.append(self.key2col()[cn.VALUE_NUM_COL])
        if self.col_is_mapped(cn.CATEGORY_COL):
            lst_cols.append(self.key2col()[cn.CATEGORY_COL])
        if self.col_is_mapped(cn.COMMENT_COL):
            lst_cols.append(self.key2col()[cn.COMMENT_COL])
        return lst_cols

    def init_user_parameters(self):

        casnr_col = self.key2col()[cn.CASNR_COL]

        if casnr_col != None:
            df_pars = pd.DataFrame(self.row_value_df[[self.parameter_col, casnr_col]].drop_duplicates())
            df_pars.columns = ['parameter', 'casnr']
            df_pars['key'] = cn.NOT_USED
            self.parameter_map_df = df_pars
        elif casnr_col == None:
            df_pars = pd.DataFrame(self.row_value_df[[self.parameter_col]].drop_duplicates())
            df_pars.columns = ['parameter']
            df_pars['key'] = cn.NOT_USED
            self.parameter_map_df = df_pars  
    
    def map_parameter_with_casnr(self)->pd.DataFrame():
        """use mapped casnr fields in order to identify parameters automatically using 
           the internal database table.

        Args:
            df (pd.DataFrame): [description]

        Returns:
            pd.DataFrame: column dataframe with matched parameters where valid 
            casnr is available
        """

        ok, err_msg = True, ''
        result_df = self.parameter_map_df.copy().reset_index()
        df_casnr = self.lookup_parameters.metadata_df.reset_index()
        df_casnr = df_casnr[df_casnr.casnr.notnull()]
        df_casnr = df_casnr[['key','casnr']]
        result_df = pd.merge(result_df, df_casnr, left_on='casnr', right_on='casnr', how='left')
        result_df = result_df[['parameter', 'casnr', 'key_y']]
        result_df.columns = ['parameter', 'casnr', 'key']
        # set all rows where key = null to string 'not used'
        result_df = result_df.fillna(value={'key': cn.NOT_USED})
        self.parameter_map_df = result_df
        return ok, err_msg



    def data_is_loaded(self) -> bool:
        return (len(self.row_sample_df)>0) | (len(self.row_value_df)> 0)

    def columns_are_mapped(self) -> bool:
        return self.col_is_mapped(cn.STATION_IDENTIFIER_COL)
    
    def parameters_are_mapped(self) -> bool:
        df = self.parameter_map_df
        return len(df[df['key'] != cn.NOT_USED]) > 0

    def parameter_categories(self):
        if self.col_is_mapped(cn.CATEGORY_COL):
            pc_col_name = self.key2col()[cn.CATEGORY_COL]
            return list(self.row_value_df[pc_col_name].unique())
        else:
            return []
    
    def get_standards(self, parameter)->list:
        casnr = self.parameter_map_df.loc[parameter]['casnr']
        result = []
        for guideline in self.guidelines:
            try:
                df = guideline['data']
                value = df.query('casnr == @casnr')
                if len(value) > 0:
                    result.append({'name': guideline['name'],
                                'value': value.iloc[0]['value'],
                                'unit': value.iloc[0]['unit']
                    })
            except:
                print('error occurred when retriebving the guideline list')
        return result

    def is_logged_in(self):
        return self.logged_in_user != None


class Sample_per_row_import():
    def __init__(self, prj: Project):
        self.project = prj
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}

        self._step = st.session_state.config.step
        self.file_format = cn.SAMPLE_FORMATS[1]

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, s):
        self._step = s
        st.session_state.config.step = s

    def load_new_dataset(self):
        def load_data():
            df = pd.read_csv(uploaded_file, 
                sep=st.session_state.config.separator, 
                encoding=st.session_state.config.encoding)
            st.success(f"File was loaded: {len(df)} rows, {len(list(df.columns))} columns.")
            with st.expander('Preview'):
                st.write(df.head())
            st.session_state.config.row_value_df = df
        
        def load_config():
            uploaded_column_definition = st.file_uploader("Columns mapping file, csv")
            if uploaded_column_definition:
                st.session_state.config.column_map_df = pd.read_csv(uploaded_column_definition,
                                                                    sep=st.session_state.config.separator)
                with st.expander('Preview columns list'):
                    AgGrid(st.session_state.config.column_map_df)
            uploaded_parameters_definition = st.file_uploader("Parameters mapping file, csv")

            if uploaded_parameters_definition:
                st.session_state.config.parameter_map_df = pd.read_csv(uploaded_parameters_definition,
                                                                       sep=st.session_state.config.separator)
                sample_cols = st.session_state.config.sample_cols()
                station_cols = st.session_state.config.station_cols()
                df, ok = self.unmelt_data(st.session_state.config.row_value_df,
                    st.session_state.config.parameter_col(), 
                    st.session_state.config.value_col(), 
                    sample_cols + station_cols)
                with st.expander('Preview parameter list'):
                    AgGrid(st.session_state.config.parameter_map_df)

        st.title = st.text_input('Dataset title', 'New dataset')
        cols = st.columns(3)
        with cols[0]:
            id = cn.SEPARATORS.index(st.session_state.config.separator)
            st.session_state.config.separator = st.selectbox('Separator character', options=cn.SEPARATORS, index=id)
            gl_list = st.session_state.config.guideline_list()
            id = 0
            st.session_state.config.guidelines[0]['name'] = st.selectbox('Standard/Guideline', options=gl_list, index=id)
        with cols[1]:
            id = cn.ENCODINGS.index(st.session_state.config.encoding)
            st.session_state.config.encoding = st.selectbox('File encoding', options=cn.ENCODINGS, index=id)
        with cols[2]:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox('Date field format', options=cn.DATE_FORMAT_LIST, index=id)
        uploaded_file = st.file_uploader("Data file (csv, 1 row per value format)")
        if uploaded_file is not None:
            load_data()
        
        if st.session_state.config.data_is_loaded():
            load_config_from_file_flag = st.checkbox('Load config from file')

            if load_config_from_file_flag:
                load_config()


    def unmelt_data(self, df, par_col, value_col, group_cols):
        df = pd.pivot_table(df,
            values=value_col,
            index=group_cols,
            columns=par_col,
            aggfunc=np.mean
        ).reset_index()
        ok = len(df) > 0
        return df, ok


    def get_non_matched_options(self, options: list, df: pd.DataFrame()) -> list:
        """Removes the options from the options list, that have already been assigned previously

        Args:
            options (list): list with all options
            df (pd.DataFrame): grid with columns, having a key collumn

        Returns:
            list: list if options that have not been assigned yet
        """
        for idx, col in df.iterrows():
            if (df.loc[idx]['key'] == idx):
                options.remove(idx)
        return options


    def identify_station_columns(self, show_only_matched):
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        with st.expander('Preview'):
            st.dataframe(st.session_state.config.row_value_df.head(100))
        filtered_columns = df[(df['type'] == cn.CTYPE_STATION) | (df['type'].isna())]
        for idx, row in filtered_columns.iterrows():
            if (df.loc[idx]['key'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                id = cn.STATION_COLUMNS_OPTIONS.index(df.loc[idx]['key'])
                df.loc[idx]['key'] = st.selectbox(idx, options=cn.STATION_COLUMNS_OPTIONS, index=id)
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_STATION
                                
                if (df.loc[idx]['key'] == cn.GEOPOINT_COL) and (not st.session_state.config.col_is_mapped(cn.LONGITUDE_COL)):
                    st.session_state.config.geopoint_to_lat_long()


    def identify_sample_columns(self, show_only_matched):
        with st.expander("Preview"):
            st.dataframe(st.session_state.config.row_value_df.head())
        st.session_state.config.has_sample_columns = st.checkbox("Dataset has no sample columns", False)
        df = st.session_state.config.column_map_df
        if not st.session_state.config.has_sample_columns:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox("Sampling date format", options=cn.DATE_FORMAT_LIST, index=id)
            filtered_columns = df[(df['type'] == cn.CTYPE_SAMPLE) | (df['type'].isnull())]
            for idx, col in filtered_columns.iterrows():
                if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                    df.loc[idx]['key'] = st.selectbox(idx, options=cn.SAMPLE_COLUMN_OPTIONS, index=cn.SAMPLE_COLUMN_OPTIONS.index(df.loc[idx]['key']))
                    if df.loc[idx]['key'] == cn.NOT_USED:
                        df.loc[idx]['type'] = None
                    else:
                        df.loc[idx]['type'] = cn.CTYPE_SAMPLE
                    
                    if df.loc[idx]['key'] == cn.SAMPLE_DATE_COL and not st.session_state.config.date_is_formatted:
                        st.session_state.config.format_date_column()

                    
    def identify_values_meta_data_columns(self, show_only_matched)->list:
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        filtered_columns = df[(df['type'] == cn.CTYPE_VAL_META) | (df['type'].isnull())]
        options = cn.META_COLUMN_OPTIONS
        for idx, col in filtered_columns.iterrows():
            if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                df.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(df.loc[idx]['key']))
                
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META
                
                if df.loc[idx]['key'] == cn.ND_QUAL_VALUE_COL and not st.session_state.config.value_col_is_filled:
                    ok = st.session_state.config.split_qual_val_column()
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META


    def match_parameters(self, show_only_matched)->str:
        ok, err_msg = True, ''
        casnr_col = st.session_state.config.key2col()[cn.CASNR_COL]
        df_pars = st.session_state.config.parameter_map_df
        if len(df_pars) == 0: 
            st.session_state.config.init_user_parameters()
            st.write('parameters were initialized because none were found')
        
        if casnr_col != None:
            if st.button("Map using CasNR"):
                ok, err_msg = st.session_state.config.map_parameter_with_casnr()

        options = st.session_state.config.lookup_parameters.key2par()
        options = helper.add_not_used2dict(options)
        st.markdown("#### Map parameters")

        for idx, par in df_pars.iterrows():
            # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
            # and an error is thrown

            if not (helper.isnan(par['key']) and show_only_matched):                
                try:
                    id = list(options.keys()).index(par['key'])
                except:
                    id = 0
                if not(show_only_matched) or (par['key'] != cn.NOT_USED):
                    df_pars.loc[idx]['key'] = st.selectbox(idx, options=list(options.keys()), 
                        format_func=lambda x:options[x], 
                        index=id)


    def pivot_table(self):
        def filter_mapped_parameters() -> pd.DataFrame:
            par_col = cols_dict[cn.PARAMETER_COL]
            df = st.session_state.config.parameter_map_df
            df = df.dropna(subset=['key'])
            df = df[df['key'] != cn.NOT_USED]
            lst_parameters = list(df.index)
            
            df_data = st.session_state.config.row_value_df.copy()
            df_data = df_data[df_data[par_col].isin(lst_parameters)]
            return df_data, lst_parameters
        
        def show_settings():
            cols = st.columns([1,4])
            with cols[0]:
                st.markdown('Parameter column:')
                st.markdown('Value column:')
                st.markdown('Sample columns:')
                st.markdown('Station columns:')
            with cols[1]:
                st.markdown(f"{par_col}")
                st.markdown(f"{value_col}")
                st.markdown(f"{','.join(sample_cols)}")
                st.markdown(f"{','.join(station_cols)}")
        
        cols_dict = st.session_state.config.key2col()
        par_col = st.session_state.config.parameter_col()
        value_col = st.session_state.config.value_col()
        sample_cols = st.session_state.config.sample_cols()
        station_cols = st.session_state.config.station_cols()
        sample_cols = sample_cols + station_cols
        show_settings()
        
        use_only_matched_parameters = st.checkbox("Use only matched parameters")
        if use_only_matched_parameters:
            df, used_parameters = filter_mapped_parameters()
        else:
            df = st.session_state.config.row_value_df
            used_parameters = list(st.session_state.config.parameter_map_df.index)
        with st.expander("Used measured parameters"):
            st.dataframe(used_parameters)
        if st.button("Unmelt table"):
            df, ok = self.unmelt_data(df, par_col, value_col, sample_cols)
            if ok:
                parameter_master_data = st.session_state.config.lookup_parameters.metadata_df
                df = helper.complete_columns(df, st.session_state.config.key2par(), parameter_master_data)
                df.to_csv('data.csv', sep=st.session_state.config.separator)
                st.success("data was successfully transformed")
                AgGrid(df.head(100))
            st.session_state.config.row_sample_df = df

            st.session_state.config.column_map_df.to_csv('columns.csv', sep=st.session_state.config.separator)
            st.session_state.config.parameter_map_df.to_csv('parameters.csv', sep=st.session_state.config.separator)


    def run_step(self):
        steps = lang['steps']
        option_item_sel = st.sidebar.selectbox('Import steps', steps)
        self.step = steps.index(option_item_sel)
        show_only_matched = st.sidebar.checkbox("Show only matched parameters")
        
        title = lang[f"step{self.step}_title"]
        info = lang[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        if self.step == 0:
            self.load_new_dataset()
        elif self.step == 1:
            self.identify_station_columns(show_only_matched)
        elif self.step == 2:
            self.identify_sample_columns(show_only_matched)
        elif self.step == 3:
            self.identify_values_meta_data_columns(show_only_matched)
        elif self.step == 4:
            self.match_parameters(show_only_matched)
        elif self.step == 5:
            self.pivot_table()
            

class Value_per_row_import():
    def __init__(self, texts_dict):
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}

        self._step = st.session_state.config.step
        lang = texts_dict
        self.file_format = 'one value per row'

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, s):
        self._step = s
        st.session_state.config.step = s

    def load_new_dataset(self):
        def load_data():
            df = pd.read_csv(uploaded_file, 
                sep=st.session_state.config.separator, 
                encoding=st.session_state.config.encoding)
            st.success(f"File was loaded: {len(df)} rows, {len(list(df.columns))} columns.")
            with st.expander('Preview'):
                st.write(df.head())
            st.session_state.config.row_value_df = df
        
        def load_config():
            uploaded_column_definition = st.file_uploader("Columns mapping file, csv")
            if uploaded_column_definition:
                st.session_state.config.column_map_df = pd.read_csv(uploaded_column_definition,
                                                                    sep=st.session_state.config.separator)
                with st.expander('Preview columns list'):
                    AgGrid(st.session_state.config.column_map_df)
            uploaded_parameters_definition = st.file_uploader("Parameters mapping file, csv")

            if uploaded_parameters_definition:
                st.session_state.config.parameter_map_df = pd.read_csv(uploaded_parameters_definition,
                                                                       sep=st.session_state.config.separator)
                sample_cols = st.session_state.config.sample_cols()
                station_cols = st.session_state.config.station_cols()
                df, ok = self.unmelt_data(st.session_state.config.row_value_df,
                    st.session_state.config.parameter_col(), 
                    st.session_state.config.value_col(), 
                    sample_cols + station_cols)
                with st.expander('Preview parameter list'):
                    AgGrid(st.session_state.config.parameter_map_df)

        st.title = st.text_input('Dataset title', 'New dataset')
        cols = st.columns(3)
        with cols[0]:
            id = cn.SEPARATORS.index(st.session_state.config.separator)
            st.session_state.config.separator = st.selectbox('Separator character', options=cn.SEPARATORS, index=id)
            # gl_list = st.session_state.config.guideline_list()
            # id = 0
            # st.session_state.config.guidelines[0]['name'] = st.selectbox('Standard/Guideline', options=gl_list, index=id)
        with cols[1]:
            id = cn.ENCODINGS.index(st.session_state.config.encoding)
            st.session_state.config.encoding = st.selectbox('File encoding', options=cn.ENCODINGS, index=id)
        with cols[2]:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox('Date field format', options=cn.DATE_FORMAT_LIST, index=id)
        uploaded_file = st.file_uploader("Data file (csv, 1 row per value format)")
        if uploaded_file is not None:
            load_data()
        
        if st.session_state.config.data_is_loaded():
            load_config_from_file_flag = st.checkbox('Load config from file')

            if load_config_from_file_flag:
                load_config()


    def unmelt_data(self, df, par_col, value_col, group_cols):
        df = pd.pivot_table(df,
            values=value_col,
            index=group_cols,
            columns=par_col,
            aggfunc=np.mean
        ).reset_index()
        ok = len(df) > 0
        return df, ok


    def get_non_matched_options(self, options: list, df: pd.DataFrame()) -> list:
        """Removes the options from the options list, that have already been assigned previously

        Args:
            options (list): list with all options
            df (pd.DataFrame): grid with columns, having a key collumn

        Returns:
            list: list if options that have not been assigned yet
        """
        for idx, col in df.iterrows():
            if (df.loc[idx]['key'] == idx):
                options.remove(idx)
        return options


    def identify_station_columns(self, show_only_matched):
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        with st.expander('Preview'):
            st.dataframe(st.session_state.config.row_value_df.head(100))
        filtered_columns = df[(df['type'] == cn.CTYPE_STATION) | (df['type'].isna())]
        for idx, row in filtered_columns.iterrows():
            if (df.loc[idx]['key'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                id = cn.STATION_COLUMNS_OPTIONS.index(df.loc[idx]['key'])
                df.loc[idx]['key'] = st.selectbox(idx, options=cn.STATION_COLUMNS_OPTIONS, index=id)
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_STATION
                                
                if (df.loc[idx]['key'] == cn.GEOPOINT_COL) and (not st.session_state.config.col_is_mapped(cn.LONGITUDE_COL)):
                    st.session_state.config.geopoint_to_lat_long()


    def identify_sample_columns(self, show_only_matched):
        with st.expander("Preview"):
            st.dataframe(st.session_state.config.row_value_df.head())
        st.session_state.config.has_sample_columns = st.checkbox("Dataset has no sample columns", False)
        df = st.session_state.config.column_map_df
        if not st.session_state.config.has_sample_columns:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.config.date_format)
            st.session_state.config.date_format = st.selectbox("Sampling date format", options=cn.DATE_FORMAT_LIST, index=id)
            filtered_columns = df[(df['type'] == cn.CTYPE_SAMPLE) | (df['type'].isnull())]
            for idx, col in filtered_columns.iterrows():
                if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                    df.loc[idx]['key'] = st.selectbox(idx, options=cn.SAMPLE_COLUMN_OPTIONS, index=cn.SAMPLE_COLUMN_OPTIONS.index(df.loc[idx]['key']))
                    if df.loc[idx]['key'] == cn.NOT_USED:
                        df.loc[idx]['type'] = None
                    else:
                        df.loc[idx]['type'] = cn.CTYPE_SAMPLE
                    
                    if df.loc[idx]['key'] == cn.SAMPLE_DATE_COL and not st.session_state.config.date_is_formatted:
                        st.session_state.config.format_date_column(df)

                    
    def identify_values_meta_data_columns(self, show_only_matched)->list:
        st.markdown("**Preview**")
        df = st.session_state.config.column_map_df
        filtered_columns = df[(df['type'] == cn.CTYPE_VAL_META) | (df['type'].isnull())]
        options = cn.META_COLUMN_OPTIONS
        for idx, col in filtered_columns.iterrows():
            if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                df.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(df.loc[idx]['key']))
                
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META
                
                if df.loc[idx]['key'] == cn.ND_QUAL_VALUE_COL and not st.session_state.config.value_col_is_filled:
                    ok = st.session_state.config.split_qual_val_column()
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META


    def match_parameters(self, show_only_matched)->str:
        ok, err_msg = True, ''
        casnr_col = st.session_state.config.key2col()[cn.CASNR_COL]
        df_pars = st.session_state.config.parameter_map_df
        if len(df_pars) == 0: 
            st.session_state.config.init_user_parameters()
            st.write('parameters were initialized because none were found')
        
        if casnr_col != None:
            if st.button("Map using CasNR"):
                ok, err_msg = st.session_state.config.map_parameter_with_casnr()

        options = st.session_state.config.lookup_parameters.key2par()
        options = helper.add_not_used2dict(options)
        st.markdown("#### Map parameters")

        for idx, par in df_pars.iterrows():
            # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
            # and an error is thrown

            if not (helper.isnan(par['key']) and show_only_matched):                
                try:
                    id = list(options.keys()).index(par['key'])
                except:
                    id = 0
                if not(show_only_matched) or (par['key'] != cn.NOT_USED):
                    df_pars.loc[idx]['key'] = st.selectbox(idx, options=list(options.keys()), 
                        format_func=lambda x:options[x], 
                        index=id)


    def pivot_table(self):
        def filter_mapped_parameters() -> pd.DataFrame:
            par_col = cols_dict[cn.PARAMETER_COL]
            df = st.session_state.config.parameter_map_df
            df = df.dropna(subset=['key'])
            df = df[df['key'] != cn.NOT_USED]
            lst_parameters = list(df.index)
            
            df_data = st.session_state.config.row_value_df.copy()
            df_data = df_data[df_data[par_col].isin(lst_parameters)]
            return df_data, lst_parameters
        
        def show_settings():
            cols = st.columns([1,4])
            with cols[0]:
                st.markdown('Parameter column:')
                st.markdown('Value column:')
                st.markdown('Sample columns:')
                st.markdown('Station columns:')
            with cols[1]:
                st.markdown(f"{par_col}")
                st.markdown(f"{value_col}")
                st.markdown(f"{','.join(sample_cols)}")
                st.markdown(f"{','.join(station_cols)}")
        
        cols_dict = st.session_state.config.key2col()
        par_col = st.session_state.config.parameter_col()
        value_col = st.session_state.config.value_col()
        sample_cols = st.session_state.config.sample_cols()
        station_cols = st.session_state.config.station_cols()
        sample_cols = sample_cols + station_cols
        show_settings()
        
        use_only_matched_parameters = st.checkbox("Use only matched parameters")
        if use_only_matched_parameters:
            df, used_parameters = filter_mapped_parameters()
        else:
            df = st.session_state.config.row_value_df
            used_parameters = list(st.session_state.config.parameter_map_df.index)
        with st.expander("Used measured parameters"):
            st.dataframe(used_parameters)
        if st.button("Unmelt table"):
            df, ok = self.unmelt_data(df, par_col, value_col, sample_cols)
            if ok:
                parameter_master_data = st.session_state.config.lookup_parameters.metadata_df
                df = helper.complete_columns(df, st.session_state.config.key2par(), parameter_master_data)
                df.to_csv('data.csv', sep=st.session_state.config.separator)
                st.success("data was successfully transformed")
                AgGrid(df.head(100))
            st.session_state.config.row_sample_df = df

            st.session_state.config.column_map_df.to_csv('columns.csv', sep=st.session_state.config.separator)
            st.session_state.config.parameter_map_df.to_csv('parameters.csv', sep=st.session_state.config.separator)


    def run_step(self):
        set_lang()
        steps = lang['steps']
        option_item_sel = st.sidebar.selectbox('Import steps', steps)
        self.step = steps.index(option_item_sel)
        show_only_matched = st.sidebar.checkbox("Show only matched parameters")
        
        title = lang[f"step{self.step}_title"]
        info = lang[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        if self.step == 0:
            self.load_new_dataset()
        elif self.step == 1:
            self.identify_station_columns(show_only_matched)
        elif self.step == 2:
            self.identify_sample_columns(show_only_matched)
        elif self.step == 3:
            self.identify_values_meta_data_columns(show_only_matched)
        elif self.step == 4:
            self.match_parameters(show_only_matched)
        elif self.step == 5:
            self.pivot_table()