import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
from datetime import datetime

import const as cn
from const import MP, Codes, Date_types
from .metadata import Metadata
import helper
import proj.database as db
from query import qry
from .fontus_import import FontusImport

DATA_ROW_FORMATS = ['one value per row', 'one sample per row']

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)

class Project():
    def __init__(self, id: int):
        ok = self.set_project_info(id)
        self.has_config_settings = False
        self.has_separate_station_file = False

        self._station_fields = []
        self._sample_fields = []
        self._observation_fields = []
        self._parameter_metadata_fields = []
        self._parameter_group1 = []
        self._parameter_group2 = []
        self.source_date_format = '%d/%m/%Y'
        self.display_date_format = '%d/%m/%Y'
        self.stations_df, ok, err_msg  = self.get_stations()

    def get_stations(self):
        sql = qry['project_stations'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        df = df.set_index('id')
        return df, ok, err_msg 


    def master_parameter_2_col_name(self, master_parameter_id: int, col_type: int):
        """Translates a master parameter name to a column name 

        Args:
            master_parameter_key (str): master parameter name expression, e.g. 'PARAMETER'
            col_type (int): column type: observation, station, sample or metadata
        """
        result = 0
        df = self.columns_df.query("type_id == @col_type and master_parameter_id == @master_parameter_id")
        if len(df) > 0:
            result = df.iloc[0]['column_name']
        return result

        
    def set_project_info(self, id:int)->bool:
        """retrieves the project info from the database and fills the project instance

        Args:
            id (int): project-id

        Returns:
            bool: success of outcome
        """        
        ok = True

        def get_parameters():
            sql = qry['project_parameters'].format(self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            df = df.set_index('id')
            return df, ok, err_msg
        
        def get_columns():
            sql = qry['project_columns'].format(self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            df = df.set_index('id')
            return df, ok, err_msg 
        
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
            self.has_separate_station_file = df.iloc[0]['has_separate_station_file']
            self.parameters_df, ok, err_msg = get_parameters()
            self.columns_df, ok, err_msg = get_columns()
            if self.row_is == cn.DATA_FORMAT.ValuePerRow.value:
                from .value_per_row_import import ValuePerRowImport
                self.imp = ValuePerRowImport(self)
            else:
                from .sample_per_row_import import SamplePerRowImport
                self.imp = SamplePerRowImport(self)
            self.phreeqc_database =  df.iloc[0]['phreeqc_thermdb']
            return True
        else:
            self.id = -1
            self.title = 'Enter a title'
            self.description= 'Enter a description'
            self.row_is = cn.DATA_FORMAT.SamplePerRow.value
            self.date_format = '%Y/%m/%d'
            self.separator = ';'
            self.encoding = 'utf8'
            self.url_source = ''
            self.is_public = False
            self.owner_id = 0
            self.language = 'en'

            return ok
    
    # properties -----------------------------------------------------------
    @property
    def db_date_format(self):
        result = self.date_format.replace('%','')
        result = result.replace('d','dd')
        result = result.replace('m','mm')
        result = result.replace('Y','yyyy')
        return result
    
    @property
    def date_column(self):
         df = self.columns_df[self.columns_df['master_parameter_id']==MP.SAMPLING_DATE.value]
         return df.iloc[0]['column_name']

    @property
    def station_fields(self):
        if self._station_fields == []:
            self._station_fields = ["id"] +  list(self.columns_df.query(f'type_id == {cn.CTYPE_STATION}')['field_name'])
        return self._station_fields
    
    @property
    def sample_fields(self):
        if self._sample_fields == []:
            self._sample_fields = list(self.columns_df.query(f'(type_id == {cn.CTYPE_SAMPLE}) and (not field_name.isnull())')['field_name'])
        return self._sample_fields
    
    @property
    def observation_fields(self):
        if self._observation_fields == []:
            self._observation_fields = list(self.columns_df.query(f'(type_id  == {cn.CTYPE_OBSERVATION}) and (not field_name.isnull())')['field_name'])
        return self._observation_fields
    
    @property
    def parameter_metadata_fields(self):
        if self._parameter_metadata_fields == []:
            self._parameter_metadata_fields = list(self.columns_df.query(f'(type_id == {cn.CTYPE_VAL_META}) and (not field_name.isnull())')['field_name'])
        return self._parameter_metadata_fields
    
    @property
    def parameter_group1(self):
        if self._parameter_group1 == []:
            sql = qry['parameter_group_list'].format(1, self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            self._parameter_group1 = list(df['group1'])
        return self._parameter_group1
    
    @property
    def parameter_group2(self):
        if self._parameter_group2 == []:
            sql = qry['parameter_group_list'].format(2, self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            self._parameter_group2 = list(df['group2'])
        return self._parameter_group2
       

    # functions ------------------------------------------------------------

    def get_parameter_list(self, type_id: int, attribute:str='column_name')->list:
        columns = self.parameters_df.query('parameter_type_id == @type_id')
        columns = list(columns[attribute])
        return columns


    def get_column_names_csv_list(self, type_id: int, sep:str=',', quotes:bool=True, prefix:str='')->str:
        columns = self.parameters_df.query('parameter_type_id == @type_id')
        columns = list(columns['column_name'])
        if quotes:
            columns = [f'{x}' for x in columns]
        if prefix:
            columns = [f'{prefix}.{x}' for x in columns]
        columns = sep.join(columns)
        return columns

    def get_sample_number(self, date:datetime, station_id:int)->str:
        sql = qry['sample_number_from_station_date'].format(self.key, station_id, date.strftime(cn.DATE_FORMAT_DB))
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df.iloc[0]['sample_number']

    def station_columns_df(self)->list:
        df = self.parameters_df.query('parameter_type_id == @cn.CTYPE_STATION')
        return 

    def observation_display_order_expression(self, prefix:str)->str:
        result = ''
        if 'group2' in self.parameter_metadata_fields:
            result = f'order by {prefix}.group2, {prefix}.group1, {prefix}.parameter_name'
        elif 'group1' in self.parameter_metadata_fields:
            result = f'order by {prefix}.group1, {prefix}.parameter_name'
        else:
            result = f'order by {prefix}.parameter_name'
        return result

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
        result = self.parameters_df[self.parameters_df['master_parameter_id'] == master_par_id]
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
        result = self.parameters_df[self.parameters_df['master_parameter_id'] == master_par_id]
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
            par_id = self.parameters_df[self.parameters_df['master_parameter_id']==sys_par_id]
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
                ,self.has_separate_station_file
                ,self.id) 
            ok, message = db.execute_non_query(sql, st.session_state.conn)
            
            message = 'Account settings have been saved successfully.' if ok else f"Account settings could not be saved, the following error occurred: '{message}'"
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
                ,st.session_state.user.id) #ownerid
            ok, message = db.execute_non_query(sql, st.session_state.conn)
            message = 'Project hase been created successfully.' if ok else f"Project could not be created, the following error occurred: '{message}'"
            if ok:
                sql = qry['max_project_id'].format(st.session_state.user.id)
                id = db.get_value(sql, st.session_state.conn)
                self.project = Project(id)
                #add to user_project table
                sql = qry['insert_user_project'].format(st.session_state.user.id, id, cn.PROJECT_OWNER)
                ok, err_msg = db.execute_query(sql, st.session_state.conn)

        return ok, message


    def station_data(self):
        fields = helper.list_to_csv_string(self.station_fields, add_quotes=True)
        sql = qry['station_data'].format(fields, self.key, self.db_date_format)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def station_samples(self, station_id):
        fields = helper.list_to_csv_string(self.sample_fields, add_quotes=True)
        sql = qry['station_samples'].format(fields, self.key, station_id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_data(self):
        sql = qry['parameter_data'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df


    def stations_samples(self, filter: str)->pd.DataFrame:
        """Returns a list of sample fields based on a user defined filter

        Args:
            filter (str): filter expression including 'WHERE'

        Returns:
            pd.DataFrame: Samples and number of observations
        """
        filter = f' where {filter}' if filter > '' else filter
        sql = qry['station_samples'].format(self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def phreeqc_samples(self, filter: str)->pd.DataFrame:
        sql = qry['sample_list'].format(self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def phreeqc_observations(self, samples_number:str)->pd.DataFrame:
        sql = qry['phreeqc_observations'].format(self.key, samples_number)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def sample_observations(self, sample_number:str):
        of_list = self.get_column_names_csv_list(type_id=cn.ParTypes.VAL_META.value, quotes=True, prefix='t1')
        pf_list = self.get_column_names_csv_list(type_id=cn.ParTypes.PARAMETER.value, quotes=True, prefix='t2')
        sql = qry['sample_observations'].format(f"{pf_list},{of_list}", self.key, sample_number)
        sql += ' ' + self.observation_display_order_expression('t2')
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_observations(self, parameter_id:int, filter: str):
        observation_list = helper.list_to_csv_string(value_list=self.observation_fields, prefix='t1', add_quotes=False)
        sample_list =  helper.list_to_csv_string(value_list=self.sample_fields, prefix='t1', add_quotes=False)
        station_list = helper.list_to_csv_string(value_list=self.station_fields, prefix='t2', add_quotes=False)
        parameter_list = helper.list_to_csv_string(value_list=self.parameter_metadata_fields, prefix='t3', add_quotes=False)
        filter = " AND " + filter if filter > '' else ''
        sql = qry['parameter_observations'].format(f"{station_list}, {sample_list}, {observation_list}, {parameter_list}", self.key, parameter_id, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        df['sampling_date'] = pd.to_datetime(df['sampling_date'])
        return df
    
    def time_series(self,parameter_id: int, stations: list):
        stations = [str(x) for x in stations]
        stations_csv = ','.join(stations)
        sql = qry['proj_time_series'].format(self.key, parameter_id, stations_csv)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def get_station_list(self, allow_none: bool=False):
        # station_key = self.key2col()[cn.STATION_IDENTIFIER_COL]
        sql = qry['station_list'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        result = dict(zip(df['id'], df['station_identifier']))
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
        csv_parameters = ",".join(map(str, filter_parameters)) if len(filter_parameters) > 0 else ''
        csv_stations = ",".join(map(str, filter_stations)) if len(filter_stations) > 0 else ''
        filter = ''
        if csv_parameters > '':
            filter = f" AND parameter_id in ({csv_parameters})"
        if len(csv_stations)>0:
            filter += f" AND station_id in ({csv_stations})"
        fields = f"t1.sampling_date, t1.value_numeric, t1.detection_limit, t1.station_id, t1.parameter_id, t3.parameter_name, t2.station_identifier"
        sql = qry['observations'].format(fields, self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def get_user_permission(self, user_id: int)->cn.PERMISSION:
        """Evaluates the permission for this project of a specified user and returns the permission result (read, write, noPermission)

        Args:
            user_id (int): user id of user requesting access

        Returns:
            cn.Permission: permission
        """
        permission = cn.PERMISSION.NoPermission.value
        if self.owner_id == user_id:
            permission = cn.PERMISSION.Write.value
        elif self.is_public:
            permission = cn.PERMISSION.Read.value
        return permission

    def import_data(self):
        self.imp.import_data()