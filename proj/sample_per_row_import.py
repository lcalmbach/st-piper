import streamlit as st
import pandas as pd
from pathlib import Path
from st_aggrid import AgGrid

import const as cn
from const import MP
from const import Codes, Date_types
import helper

import proj.database as db
from query import qry
from .fontus_import import FontusImport
from .project import Project

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)
    
SAMPLE_FORMATS = ['one value per row', 'one sample per row']


class SamplePerRowImport(FontusImport):
    def __init__(self, prj: Project):
        super().__init__(prj)
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}
        self.settings={}

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
    
    def import_data(self):
        def verify_file_columns(df_config, df_data)->bool:
            ok, msg = True, []
            # verify if each predefined column name is included in the import file
            for col in list(df_config['source_column_name']):
                if not(col in list(df_data.columns)):
                    msg.append(f"column '{col}' could not be found")
                    ok=False
            return ok, msg

        def update_station_id():
            """
            updates the station_id column in the observation table based on the station_name column in the
            project station table which mast match the station column in the observation table.
            """
            source_key = self.get_column_name(MP.STATION_IDENTIFIER.value)
            sql = qry['update_station_id'].format(self.project.key, cn.STATION_IDENTIFIER_COL, source_key)
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)
            return ok, err_msg
        
        def  update_parameter_id():
            sql = qry['update_parameter_id'].format(self.project.key, 'source_column_name', 'variable')
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)
            return ok, err_msg

        def insert_observation_data():
            sample_cols = self.get_column_df([cn.ParTypes.SAMPLE.value])
            source_cols = list(sample_cols['source_column_name']) + ["detection_limit","value","unit","station_id","parameter_id","value_numeric","is_non_detect"]
            target_cols = list(sample_cols['field_name']) + ["detection_limit","value","unit","station_id","parameter_id","value_numeric","is_non_detect"]
            source_fields = '"' + '","'.join(source_cols) + '"'
            target_fields = '"' + '","'.join(target_cols) + '"'
            cmd = f"insert into {self.project.key}_observation ({target_fields}) select {source_fields} from {self.project.key}_temp"
            ok, err_msg = db.execute_non_query(cmd,st.session_state.conn)
            return ok, err_msg
        
        def insert_station_data():
            source_cols = ["SAMPLE_FIELD_ID","detection_limit","value","unit","station_id","sampling_date","parameter_id","value_numeric","is_non_detect"]
            target_cols = ["sample_number","detection_limit","value","unit","station_id","sampling_date","parameter_id","value_numeric","is_non_detect"]
            source_fields = '"' + '","'.join(source_cols) + '"'
            target_fields = '"' + '","'.join(target_cols) + '"'
            cmd = f"insert into {self.project.key}_station ({target_fields}) select {source_fields} from {self.project.key}_temp"
            ok, err_msg = db.execute_non_query(cmd,st.session_state.conn)
            return ok, err_msg

        def update_num_value_col():
            """
            This function fills the numeric value column: for numeric values in the value column, this value is reported
            <X (non detects) are replaced by half of the value. e.g. <1.0 becomes 0.5
            """
            
            num_value_col = 'value_numeric'
            value_col = 'value'
            sql = qry['update_num_value_col'].format(self.project.key, num_value_col, value_col)
            ok, err_msg = db.execute_non_query(sql,st.session_state.conn)
            return ok, err_msg
        
        def import_station_file():
            with st.spinner(text='Loading station data'):
                if import_mode == import_mode_options[1]:
                    ok, err_msg = truncate_table(f"{self.project.key}_station")
                df_station = helper.load_data_from_file(station_file, preview=True)
                st.success('station data was loaded')
                try:    
                    ok, msg = verify_file_columns(df_config=self.station_columns_df(), df_data=df_station)
                    if not ok:
                        raise ValueError(f'The following columns could not be found or contain invalid data: {msg}')
                    else:
                        st.success('Station data was verified')
                    db.save_db_table(table_name=f'{self.project.key}_temp', df=df_station, fields=[])
                    ok, err_msg = insert_station_data()
                    if not ok:
                        raise ValueError(f'Station could not be inserted into table: {err_msg}')
                    else:
                        st.success('Station data was inserted in data table')
                except ValueError as e:
                    st.warning(e)
                except:
                    st.warning('An error occurred while reading the station data')

        def import_observation_file():
             with st.spinner(text='Loading observation data'):
                if self.settings['append_mode'] == import_mode_options[1]:
                    ok, err_msg = db.truncate_table(f"{self.project.key}_observation")
                df_observation = helper.load_data_from_file(self.settings['observation_file'], preview=True)
                
                dt_col = self.get_column_name(MP.SAMPLING_DATE.value)
                df_observation[dt_col] = pd.to_datetime(df_observation[dt_col], format=self.project.source_date_format)
                
                ok, msg = verify_file_columns(df_config=self.columns_df, df_data=df_observation)
                if ok:
                    st.success('observation data was verified')
                id_vars = self.get_column_list(cn.ParTypes.STATION.value) + self.get_column_list(cn.ParTypes.SAMPLE.value)
                value_vars = self.get_column_list(cn.ParTypes.OBSERVATION.value)
                df_observation = pd.melt(df_observation, id_vars=id_vars, value_vars=value_vars,
                    var_name=None, value_name='value', col_level=None)
                df_observation['station_id'] = 0
                df_observation['parameter_id'] = 0
                df_observation['value_numeric'] = 0.0
                df_observation['detection_limit'] = 0.0
                df_observation['is_non_detect'] = False
                df_observation['unit'] = ''

                ok, msg = db.save_db_table(table_name=f'{self.project.key}_temp', df=df_observation, fields=[])
                if ok:
                    st.success('observation data was loaded')
                    ok, msg = update_station_id()
                
                if ok:
                    st.success('Station id was updated')
                    ok, msg = update_parameter_id()
                if ok:
                    st.success('Parameter id was updated')
                    ok, msg = update_num_value_col()
                if ok:
                    st.success('non detect fields were updated')
                    ok, msg = insert_observation_data()
                if ok:
                    st.success(f'data was successfully converted and saved to database')
                else:
                    st.warning(f'Errors were found in observations data file: {msg}')

        #-----------------------------------------------------------------------------
        # Begin
        #-----------------------------------------------------------------------------
        
        self.settings['station_file'] = None
        if self.project.has_separate_station_file:
            self.settings['station_file'] = st.file_uploader(label="Stationvv data", type='csv', help='Station file must be added during the first upload and whenever there were changes in station data')

        self.settings['observation_file'] = st.file_uploader(label="Observation data, csv", type='csv', help='csv file with the oberved values')
        import_mode_options = ['Keep existing records', 'Delete existing records prior to import']
        append_mode = st.radio(label="Data append mode",
            options=import_mode_options,
            help="All data from the import file will be appended. If some records already exist in the database you should select the option: 'Delete existing records prior to the import'")
        self.settings['append_mode'] = import_mode_options.index(append_mode)
        if st.button('upload data', disabled=(self.settings['observation_file'] == None and self.settings['station_file'] == None)):  
            if self.project.has_separate_station_file and self.settings['station_file']:
                import_station_file() 
            if self.settings['observation_file']:
                import_observation_file()
               