import encodings
import streamlit as st
import pandas as pd
from pathlib import Path
from st_aggrid import AgGrid

import const as cn
from const import MP
from const import Codes, Date_types
from metadata import Metadata
import helper

import database as db
from query import qry

lang = {}
def set_lang():
    global lang
    lang = helper.get_language(__name__, st.session_state.language)
    
SAMPLE_FORMATS = ['one value per row', 'one sample per row']

def truncate_table(table_name):
    sql = qry['truncate_table'].format(table_name )
    ok, err_msg = db.execute_non_query(sql, st.session_state.conn)
    return ok, err_msg

@st.experimental_memo
def master_parameters_df(type: str=''):
    sql = qry['master_columns']
    df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
    if type > '':
        df = df[df['type']==type]
    return df

def has_mandatory_columns_mapped(type:str, df):
    ok, msg = True, ''
    sql = qry['mandatory_parameters'].format(lang, type)
    df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
    for idx, row in df.iterrows():
        if not row['id'] in list(df['id']):
            ok = False
            msg = f"The mandatory parameter {row['name']} has not been mapped"
    return ok, msg


def load_import_config():
    uploaded_column_definition = st.file_uploader("Columns mapping file, csv")
    if uploaded_column_definition:
        st.session_state.column_map_df = pd.read_csv(uploaded_column_definition,
                                                            sep=st.session_state.separator)
        with st.expander('Preview columns list'):
            AgGrid(st.session_state.column_map_df)
    uploaded_parameters_definition = st.file_uploader("Parameters mapping file, csv")

    if uploaded_parameters_definition:
        st.session_state.parameter_map_df = pd.read_csv(uploaded_parameters_definition,
                                                                sep=st.session_state.separator)
        sample_cols = st.session_state.sample_cols()
        station_cols = st.session_state.station_cols()
        df, ok = self.unmelt_data(st.session_state.row_value_df,
            st.session_state.parameter_col(), 
            st.session_state.value_col(), 
            sample_cols + station_cols)
        with st.expander('Preview parameter list'):
            AgGrid(st.session_state.parameter_map_df)


class Project():
    def __init__(self, id: int):
        ok = self.set_project_info(id)
        self.has_config_settings = False
        if self.row_is=="one value per row":
            st.session_state.imp = Value_per_row_import(self)
        else:
            st.session_state.imp = Sample_per_row_import(self)
        self._station_fields = None
        self._sample_fields = None
        self._observation_fields = None

    def master_parameter_2_col_name(self, master_parameter_id: int, col_type: int):
        """translates a master parameter name to a column name 

        Args:
            master_parameter_key (str): master parameter name expression, e.g. 'PARAMETER'
            col_type (int): column type: observation, station, sample or metadata
        """
        result = 0
        df = self.columns_df.query("type_id == @col_type and master_parameter_id == @master_parameter_id")
        if len(df)>0:
            result = df.iloc[0]['column_name']
        return result

        
    def set_project_info(self, id:int):
        def get_parameters():
            sql = qry['project_parameters'].format(self.key)
            df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
            df = df.set_index('id')
            return df
        
        def get_columns():
            sql = qry['project_columns'].format(self.key)
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
            self.has_separate_station_file = df.iloc[0]['has_separate_station_file']
            self.parameters_df = get_parameters()
            self.columns_df = get_columns()
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
    def db_date_format(self):
        result = self.date_format.replace('%','')
        result = result.replace('d','dd')
        result = result.replace('m','mm')
        result = result.replace('Y','yyyy')
        return result
        
    #property 
    def stations_columns_df(self):
        return self.columns_df[self.columns_df['type_id']==cn.CTYPE_STATION]
    
    def observation_columns_df(self):
        return self.columns_df[self.columns_df['type_id'].isin([cn.CTYPE_SAMPLE, cn.CTYPE_VAL_META])]
    
    def station_columns_df(self):
        return self.columns_df[self.columns_df['type_id']==cn.CTYPE_STATION]

    @property
    def date_column(self):
         df = self.columns_df[self.columns_df['master_parameter_id']==MP.SAMPLING_DATE.value]
         return df.iloc[0]['column_name']

    @property
    def station_fields(self):
        def get_station_fields():
            fields = list(self.columns_df.query(f'type_id == {cn.CTYPE_STATION}')['field_name'])
            result = '"id","' +  '","'.join(fields) + '"'
            return result

        if self._station_fields == None:
            self._station_fields = get_station_fields()
        return self._station_fields
    
    @property
    def sample_fields(self):
        def get_sample_fields():
            fields = list(self.columns_df.query(f'(type_id == {cn.CTYPE_SAMPLE}) and (not field_name.isnull())')['field_name'])
            result = '"' + '","'.join(fields) + '"'
            return result

        if self._sample_fields == None:
            self._sample_fields = get_sample_fields()
        return self._sample_fields
    
    @property
    def observation_fields(self):
        def get_observation_fields():
            fields = list(self.columns_df.query(f'(type_id == {cn.CTYPE_VAL_META}) and (not field_name.isnull())')['field_name'])
            result = '"' + '","'.join(fields) + '"'
            return result

        if self._observation_fields == None:
            self._observation_fields = get_observation_fields()
        return self._observation_fields
       

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

    def import_data(self):
        st.write(self.row_is)
        if self.row_is=="one value per row":
            self.import_value_per_row_import()
        else:
            self.import_value_per_row_import()
    
    def import_value_per_row_import(self):
        def verify_file_columns(df_config, df_data)->bool:
            ok, msg = True, []
            # verify if each predefined column name is included in the import file
            for col in list(df_config['column_name']):
                if not(col in list(df_data.columns)):
                    msg.append(f"column '{col}' could not be found")
                    ok=False
            return ok, msg

        def  update_station_id():
            """
            updates the station_id column in the observation table based on the station_name column in the
            project station table which mast match the station column in the observation table.
            """
            source_key = self.master_parameter_2_col_name(MP.STATION_IDENTIFIER.value, cn.CTYPE_SAMPLE)
            sql = qry['update_station_id'].format(self.key, cn.STATION_IDENTIFIER_COL, source_key)
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)
        
        def  update_parameter_id():
            source_key = self.master_parameter_2_col_name(MP.PARAMETER.value, cn.CTYPE_VAL_META)
            sql = qry['update_parameter_id'].format(self.key, cn.PARAMETER_COL, source_key)
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)

        def insert_observation_data():
            df_cols = self.observation_columns_df()
            df_cols = df_cols.query(f"( type_id != {cn.CTYPE_STATION} ) and ( field_name.notnull() )")
            source_fields = '"' + '","'.join(list(df_cols['column_name'])) + '","station_id", "parameter_id"'
            target_fields = '"' + '","'.join(list(df_cols['field_name'])) + '","station_id", "parameter_id"'
            cmd = f"insert into {self.key}_observation ({target_fields}) select {source_fields} from {self.key}_temp"
            ok, err_msg = db.execute_non_query(cmd,st.session_state.conn)
            return ok, err_msg
        
        def insert_station_data():
            df_cols = self.station_columns_df()
            df_cols = df_cols.query(f"( type_id == {cn.CTYPE_STATION} ) and ( field_name.notnull() )")
            source_fields = '"' + '","'.join(list(df_cols['column_name'])) + '"'
            target_fields = '"' + '","'.join(list(df_cols['field_name'])) + '"'
            cmd = f"insert into {self.key}_station ({target_fields}) select {source_fields} from {self.key}_temp"
            ok, err_msg = db.execute_non_query(cmd,st.session_state.conn)
            return ok, err_msg

        def update_num_value_col():
            """
            This function fills the numeric value column: for numeric values in the value column, this value is reported
            <X (non detects) are replaced by half of the value. e.g. <1.0 becomes 0.5
            """
            
            num_value_col = self.master_parameter_2_col_name(MP.NUMERIC_VALUE.value, cn.CTYPE_VAL_META)
            value_col = self.master_parameter_2_col_name(MP.VALUE.value, cn.CTYPE_VAL_META)
            sql = qry['update_num_value_col'].format(self.key, num_value_col, value_col)
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)
            return ok, err_msg

        station_file = st.file_uploader(label="Station data", type='csv', help='Station file must be added during the first upload and whenever there were changes in station data')
        observation_file = st.file_uploader(label="Observation data, csv", type='csv', help='csv file with the oberved values')
        import_mode_options = ['Keep existing records', 'Delete existing records prior to import']
        import_mode = st.radio(label="Data append mode",
            options=import_mode_options,
            help="All data from the import file will be appended. If some records already exist in the database you should select the option: 'Delete existing records prior to the import'")
        if st.button('upload data', disabled=(observation_file == None and station_file == None)):  
            if station_file:
                with st.spinner(text='Loading station data'):
                    if import_mode == import_mode_options[1]:
                        ok, err_msg = truncate_table(f"{self.key}_station")
                    df_station = helper.load_data_from_file(station_file, preview=True)
                    st.success('station data was loaded')
                    try:    
                        ok, msg = verify_file_columns(df_config=self.station_columns_df(), df_data=df_station)
                        if not ok:
                            raise ValueError(f'The following columns could not be found or contain invalid data: {msg}')
                        else:
                            st.success('Station data was verified')
                        db.save_db_table(table_name=f'{self.key}_temp', df=df_station, fields=[])
                        ok, err_msg = insert_station_data()
                        if not ok:
                            raise ValueError(f'Station could not be inserted into table: {err_msg}')
                        else:
                            st.success('Station data was inserted in data table')
                    except ValueError as e:
                        st.warning(e)
                    except:
                        st.warning('An error occurred while reading the station data')

            if observation_file:
                with st.spinner(text='Loading observation data'):
                    if import_mode == import_mode_options[1]:
                        ok, err_msg = truncate_table(f"{self.key}_observation")
                    df_observation = helper.load_data_from_file(observation_file, preview=True)
                    df_observation['parameter_id'] = 0
                    df_observation['station_id'] = 0
                    col = self.date_column
                    df_observation[col] = pd.to_datetime(df_observation[col])
                    st.success('observation data was loaded')
                    ok, msg = verify_file_columns(df_config=self.observation_columns_df(), df_data=df_observation)
                    try:
                        st.success('observation data was verified')
                        db.save_db_table(table_name=f'{self.key}_temp', df=df_observation, fields=[])
                        update_station_id()
                        update_parameter_id()
                        ok, err_msg = update_num_value_col()
                        ok, err_msg = insert_observation_data()
                        
                    except:
                        st.warning(f'Errors were found in observations data file: {msg}')
            

    def import_sample_per_row_import(self):
        pass

    def station_data(self):
        sql = qry['station_data'].format(self.station_fields, self.key, self.db_date_format)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def station_samples(self, station_id):
        sql = qry['station_samples'].format(self.sample_fields, self.key, station_id)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_data(self):
        sql = qry['parameter_data'].format(self.key)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

    def sample_observations(self, station_id, sample_date):
        fields = f"{self.observation_fields},{self.sample_fields}"
        sql = qry['sample_observations'].format(fields, self.key, station_id, sample_date)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df
    
    def parameter_observations(self, parameter_id:int, filter: str):
        filter = " AND " + filter if filter > '' else ''
        sql = qry['parameter_observations'].format(self.key, parameter_id, filter)
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
        sql = qry['observations'].format(self.key, filter)
        df, ok, err_msg = db.execute_query(sql, st.session_state.conn)
        return df

class Sample_per_row_import():
    def __init__(self, prj: Project):
        self.project = prj
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}

        self.step = 0
        self.file_format = SAMPLE_FORMATS[1]

    def load_new_dataset(self):
        def load_data():
            df = pd.read_csv(uploaded_file, 
                sep=st.session_state.project.separator, 
                encoding=st.session_state.project.encoding)
            st.success(f"File was loaded: {len(df)} rows, {len(list(df.columns))} columns.")
            with st.expander('Preview'):
                AgGrid(df.head())
            st.session_state.row_value_df = df
        
        def load_config():
            uploaded_column_definition = st.file_uploader("Columns mapping file, csv")
            if uploaded_column_definition:
                st.session_state.column_map_df = pd.read_csv(uploaded_column_definition,
                                                                    sep=st.session_state.separator)
                with st.expander('Preview columns list'):
                    AgGrid(st.session_state.column_map_df)
            uploaded_parameters_definition = st.file_uploader("Parameters mapping file, csv")

            if uploaded_parameters_definition:
                st.session_state.parameter_map_df = pd.read_csv(uploaded_parameters_definition,
                                                                       sep=st.session_state.separator)
                sample_cols = st.session_state.sample_cols()
                station_cols = st.session_state.station_cols()
                df, ok = self.unmelt_data(st.session_state.row_value_df,
                    st.session_state.parameter_col(), 
                    st.session_state.value_col(), 
                    sample_cols + station_cols)
                with st.expander('Preview parameter list'):
                    AgGrid(st.session_state.parameter_map_df)

        st.title = st.text_input('Dataset title', 'New dataset')
        cols = st.columns(3)
        with cols[0]:
            id = cn.SEPARATORS.index(st.session_state.separator)
            st.session_state.separator = st.selectbox('Separator character', options=cn.SEPARATORS, index=id)
            value=0
            abc = st.checkbox('Has separate data source file for station data', value=value)
            gl_list = st.session_state.guideline_list()
            id = 0
            st.session_state.guidelines[0]['name'] = st.selectbox('Standard/Guideline', options=gl_list, index=id)
        with cols[1]:
            id = cn.ENCODINGS.index(st.session_state.encoding)
            st.session_state.encoding = st.selectbox('File encoding', options=cn.ENCODINGS, index=id)
        with cols[2]:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.date_format)
            st.session_state.date_format = st.selectbox('Date field format', options=cn.DATE_FORMAT_LIST, index=id)
        st.session_state.imp.update_mode_replace = st.checkbox('Data load mode', help="when checked, all existing data will be removed before loading the new data. If unchecked, the uploaded data will be added to the data existing in the database.")
        uploaded_file = st.file_uploader("Data file (csv, 1 row per value format)")
        if uploaded_file is not None:
            load_data()
        
        if st.session_state.data_is_loaded():
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
        df = st.session_state.column_map_df
        with st.expander('Preview'):
            st.dataframe(st.session_state.row_value_df.head(100))
        filtered_columns = df[(df['type'] == cn.CTYPE_STATION) | (df['type'].isna())]
        for idx, row in filtered_columns.iterrows():
            if (df.loc[idx]['key'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                id = cn.STATION_COLUMNS_OPTIONS.index(df.loc[idx]['key'])
                df.loc[idx]['key'] = st.selectbox(idx, options=cn.STATION_COLUMNS_OPTIONS, index=id)
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_STATION
                                
                if (df.loc[idx]['key'] == cn.GEOPOINT_COL) and (not st.session_state.col_is_mapped(cn.LONGITUDE_COL)):
                    st.session_state.geopoint_to_lat_long()


    def identify_sample_columns(self, show_only_matched):
        with st.expander("Preview"):
            st.dataframe(st.session_state.row_value_df.head())
        st.session_state.has_sample_columns = st.checkbox("Dataset has no sample columns", False)
        df = st.session_state.column_map_df
        if not st.session_state.has_sample_columns:
            id = cn.DATE_FORMAT_LIST.index(st.session_state.date_format)
            st.session_state.date_format = st.selectbox("Sampling date format", options=cn.DATE_FORMAT_LIST, index=id)
            filtered_columns = df[(df['type'] == cn.CTYPE_SAMPLE) | (df['type'].isnull())]
            for idx, col in filtered_columns.iterrows():
                if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                    df.loc[idx]['key'] = st.selectbox(idx, options=cn.SAMPLE_COLUMN_OPTIONS, index=cn.SAMPLE_COLUMN_OPTIONS.index(df.loc[idx]['key']))
                    if df.loc[idx]['key'] == cn.NOT_USED:
                        df.loc[idx]['type'] = None
                    else:
                        df.loc[idx]['type'] = cn.CTYPE_SAMPLE
                    
                    if df.loc[idx]['key'] == cn.SAMPLE_DATE_COL and not st.session_state.date_is_formatted:
                        st.session_state.format_date_column()

                    
    def identify_values_meta_data_columns(self, show_only_matched)->list:
        st.markdown("**Preview**")
        df = st.session_state.column_map_df
        filtered_columns = df[(df['type'] == cn.CTYPE_VAL_META) | (df['type'].isnull())]
        options = cn.META_COLUMN_OPTIONS
        for idx, col in filtered_columns.iterrows():
            if (df.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                df.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(df.loc[idx]['key']))
                
                if df.loc[idx]['key'] == cn.NOT_USED:
                    df.loc[idx]['type'] = None
                else:
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META
                
                if df.loc[idx]['key'] == cn.ND_QUAL_VALUE_COL and not st.session_state.value_col_is_filled:
                    ok = st.session_state.split_qual_val_column()
                    df.loc[idx]['type'] = cn.CTYPE_VAL_META


    def match_parameters(self, show_only_matched)->str:
        ok, err_msg = True, ''
        casnr_col = st.session_state.key2col()[cn.CASNR_COL]
        df_pars = st.session_state.parameter_map_df
        if len(df_pars) == 0: 
            st.session_state.init_user_parameters()
            st.markdown('parameters were initialized because none were found')
        
        if casnr_col != None:
            if st.button("Map using CasNR"):
                ok, err_msg = st.session_state.map_parameter_with_casnr()

        options = st.session_state.lookup_parameters.key2par()
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
            df = st.session_state.parameter_map_df
            df = df.dropna(subset=['key'])
            df = df[df['key'] != cn.NOT_USED]
            lst_parameters = list(df.index)
            
            df_data = st.session_state.row_value_df.copy()
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
        
        cols_dict = st.session_state.key2col()
        par_col = st.session_state.parameter_col()
        value_col = st.session_state.value_col()
        sample_cols = st.session_state.sample_cols()
        station_cols = st.session_state.station_cols()
        sample_cols = sample_cols + station_cols
        show_settings()
        
        use_only_matched_parameters = st.checkbox("Use only matched parameters")
        if use_only_matched_parameters:
            df, used_parameters = filter_mapped_parameters()
        else:
            df = st.session_state.row_value_df
            used_parameters = list(st.session_state.parameter_map_df.index)
        with st.expander("Used measured parameters"):
            st.dataframe(used_parameters)
        if st.button("Unmelt table"):
            df, ok = self.unmelt_data(df, par_col, value_col, sample_cols)
            if ok:
                parameter_master_data = st.session_state.lookup_parameters.metadata_df
                df = helper.complete_columns(df, st.session_state.key2par(), parameter_master_data)
                df.to_csv('data.csv', sep=st.session_state.separator)
                st.success("data was successfully transformed")
                AgGrid(df.head(100))
            st.session_state.row_sample_df = df

            st.session_state.column_map_df.to_csv('columns.csv', sep=st.session_state.separator)
            st.session_state.parameter_map_df.to_csv('parameters.csv', sep=st.session_state.separator)


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
            
