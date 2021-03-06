import encodings
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid
import sys
import const as cn
from const import MP
from const import Codes, Date_types
import helper

import proj.database as db
from query import qry
from .project import Project
from .fontus_import import FontusImport

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


class ValuePerRowImport(FontusImport):
    def __init__(self, prj):
        super().__init__(prj)
        self.columns_metadata_df = pd.DataFrame(['col','obj_type','par_type','unit', 'master_id'])
        self.parameter_metadata_df = pd.DataFrame(['col','par_type','unit', 'formula', 'formula_weight', 'valence'])
        self.update_mode_replace = False
        self.step_success = False # next step may only be success_step +1 not higher

    #@property
    #def step(self):
    #    return self._step
    #
    #@step.setter
    #def step(self, s):
    #    self._step = s
    #    st.session_state.step = s

    def refresh_success_step(self):
        """
        if a step has been successful, the way is open to the next step
        """
        self.success_step = self.step

    
    def load_station_data(self):
        """
        Step 0: uploads the observation from a csv file and stores it to a dataframe
        """

        self.update_mode_replace = st.checkbox('Data load mode', help="when checked, all existing data will be removed before loading the new data. If unchecked, the uploaded data will be added to the data existing in the database.")
        station_file = st.file_uploader("file holding station data (csv, 1 row per value format)")
        if station_file is not None:
            self.station_df = helper.load_data_from_file(station_file, True)

    def load_observation_data(self):
        """
        Step 1: uploads the observation from a csv file and stores it to a dataframe
        """

        observation_file = st.file_uploader("File holding observation data (csv, 1 row per value format)")
        if observation_file is not None:
            self.observation_df = helper.load_data_from_file(observation_file, True)

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


    def read_column_config():
        pass

    def read_parameters_config():
        pass

    def identify_station_columns(self, show_only_matched):
        def init_station_column_df():
            """
            creates a dataframes with 1 row for each column in the station table. each row holds: column name, label, type, map. 
            the map fields allows to map a column to a system parameter. map fields for station are: identifier, elevation, latitude, longitude
            identifiers must be string, latitude, longitude and elevation must be float type.
            """
            self.station_columns = pd.DataFrame()
            for col in self.station_df.columns:
                new_row = pd.DataFrame({'col': col, 'map': -1, 'type': Date_types.STR.value},index=[0])
                if len(self.station_columns) == 0:
                    self.station_columns = new_row
                else:
                    self.station_columns = pd.concat([self.station_columns, new_row], ignore_index = True)

        st.markdown("**Preview**")
        if len(self.station_columns) == 0:
            init_station_column_df()
        df = self.station_columns 
        with st.expander('Preview'):
            st.dataframe(self.station_df.head(100))
        
        st.markdown("**Map Station Parameters**")
        station_par_dict = df2dict(master_parameters_df('st'), 'id', 'name_en')
        types_dict = helper.get_lookup_code_dict(Codes.DATATYPE,st.session_state.language)
        with st.form('station_columns'):
            cols = st.columns(4)
            for idx, row in df.iterrows():
                #if (df.loc[idx]['map'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                with cols[0]:
                    st.text_input(label='Column',value=df.loc[idx]['col'], disabled=True, key=f'c-{idx}')
                with cols[1]:
                    index = list(station_par_dict.keys()).index(df.loc[idx, 'map'])
                    df.loc[idx, 'map'] = st.selectbox(label='Mapped Master Parameter', options=station_par_dict.keys(), 
                                            format_func=lambda x:station_par_dict[x], 
                                            index=index, 
                                            key=f'm-{idx}'
                                        )
                with cols[2]:
                    index = list(types_dict.keys()).index(df.loc[idx, 'type'])
                    df.loc[idx, 'type'] = st.selectbox(label='Data type', options=types_dict.keys(), # 
                                            format_func=lambda x:types_dict[x], 
                                            index=index, 
                                            key=f't-{idx}'
                                        )
            if st.form_submit_button("Submit"):
                pass


    def identify_sample_columns(self, show_only_matched):
        def init_sample_column_df():
            """
            creates a dataframes with 1 row for each column in the station table. each row holds: column name, label, type, map. 
            the map fields allows to map a column to a system parameter. map fields for station are: identifier, elevation, latitude, longitude
            identifiers must be string, latitude, longitude and elevation must be float type.
            """
            self.sample_columns = pd.DataFrame()
            for col in self.observation_df.columns:
                new_row = pd.DataFrame({'col': col, 'map': -1, 'type': Date_types.STR.value},index=[0])
                if len(self.sample_columns) == 0:
                    self.sample_columns = new_row
                else:
                    self.sample_columns = pd.concat([self.sample_columns, new_row], ignore_index = True)

        
        if len(self.sample_columns) == 0:
            init_sample_column_df()
        st.markdown("**Preview**")
        df = self.sample_columns 
        with st.expander('Preview'):
            st.dataframe(self.observation_df.head(100))
        
        st.markdown("**Map Sample Parameters**")
        sample_par_dict = df2dict(master_parameters_df('sa'), 'id', 'name_en')
        types_dict = helper.get_lookup_code_dict(Codes.DATATYPE,st.session_state.language)
        with st.form('sample_columns'):
            cols = st.columns(4)
            for idx, row in df.iterrows():
                #if (df.loc[idx]['map'] not in [cn.NOT_USED, cn.NOT_MAPPED]) or (not show_only_matched):
                with cols[0]:
                    st.text_input(label='Column',value=df.loc[idx]['col'], disabled=True, key=f'c-{idx}')
                with cols[1]:
                    index = list(sample_par_dict.keys()).index(df.loc[idx, 'map'])
                    df.loc[idx, 'map'] = st.selectbox(label='Mapped Master Parameter', options=sample_par_dict.keys(), 
                                            format_func=lambda x:sample_par_dict[x], 
                                            index=index, 
                                            key=f'm-{idx}'
                                        )
                with cols[2]:
                    index = list(types_dict.keys()).index(df.loc[idx, 'type'])
                    df.loc[idx, 'type'] = st.selectbox(label='Data type', options=types_dict.keys(), # 
                                            format_func=lambda x:types_dict[x], 
                                            index=index, 
                                            key=f't-{idx}'
                                        )
            if st.form_submit_button("Submit"):
                pass


    def identify_sample_columns_xx(self, show_only_matched):
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
                        st.session_state.format_date_column(df)


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
    
    def get_step_success(self):
        if self.step == 0:
            return (len(self.station_df)>0)
        elif self.step == 1:
            return (len(self.observation_df)>0)
        elif self.step == 2:
            ok = has_mandatory_columns_mapped('st', self.station_columns)

    def run_step(self):
        show_only_matched = st.sidebar.checkbox("Show only matched parameters")
        title = lang[f"step{self.step}_title"]
        info = lang[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        step_success = False
        if self.step == 0:
            self.load_station_data()
        elif self.step == 1:
            self.load_observation_data()
        elif self.step == 2:
            self.identify_station_columns(show_only_matched)
        elif self.step == 3:
            self.identify_sample_columns(show_only_matched)
        elif self.step == 4:
            self.identify_values_meta_data_columns(show_only_matched)
        elif self.step == 5:
            self.match_parameters(show_only_matched)
        self.step_success = self.get_step_success()
        
    def select_step(self):
        if lang == {}:
            set_lang()
        steps = lang['steps']
        st.sidebar.markdown(f"**Step {self.step}:**")
        st.sidebar.markdown(steps[self.step])
        
        cols = st.sidebar.columns([4,8])
        with cols[0]:
            if st.button('Previous', disabled=(self.step == 0)):
                self.step -=1
        with cols[1]:
            if st.button('Next', disabled=False): # not(self.step_success)
                self.step +=1
        self.run_step()
    
    def import_data(self):
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
            sql = qry['update_num_value_col'].format(self.key)
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
                    #try:
                    st.success('observation data was verified')
                    ok, msg = db.save_db_table(table_name=f'{self.key}_temp', df=df_observation, fields=[])
                    if ok:
                        update_station_id()
                        update_parameter_id()
                        ok, err_msg = update_num_value_col()
                        ok, err_msg = insert_observation_data()
                        
                    #except:
                    #    st.warning(f'Errors were found in observations data file: {msg}')
            

