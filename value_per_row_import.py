import streamlit as st
import pandas as pd
import numpy as np

import const as cn
import helper

class Value_per_row_import():
    def __init__(self, df_raw: pd.DataFrame, texts_dict):
        self.df_raw = df_raw
        if 'all_columns' in st.session_state:
            self.all_columns = st.session_state.all_columns
        else:
            self.all_columns = self.init_all_columns(df_raw)
        self.df_pivot = pd.DataFrame()
        self.station_columns = {}
        self.sample_columns = {}
        self.metadata_columns = {}
        if 'parameters' in st.session_state:
            self.parameters = st.session_state.parameters
        else:
            self.parameters = pd.DataFrame()
            st.session_state.parameters = pd.DataFrame()
        self._step = st.session_state['step']
        self.texts_dict = texts_dict

    @property
    def step(self):
         return self._step
       

    @step.setter
    def step(self, s):
         self._step = s
         st.session_state['step'] = s

    def init_all_columns(self,df):
        df_columns = pd.DataFrame(list(df.columns))
        df_columns.columns = ['column_name']
        df_columns['key'] = cn.NOT_USED
        df_columns['type'] = None
        df_columns.set_index('column_name',inplace=True)
        return df_columns


    def unmelt_data(self, df, par_col, value_col, sample_cols):
        df = pd.pivot_table(df,
            values = value_col,
            index = sample_cols, 
            columns = par_col,
            aggfunc = np.mean
        ).reset_index()
        ok = len(df)> 0
        return df, ok


    def map_parameter_with_casnr(self, df:pd.DataFrame())->pd.DataFrame():
        """use mapped casnr fields in order to identify parameters automatically using 
           the internal database table.

        Args:
            df (pd.DataFrame): [description]

        Returns:
            pd.DataFrame: column dataframe with matched parameters where valid 
            casnr is available
        """
        df_casnr = st.session_state.parameters_metadata.reset_index()
        df_casnr = df_casnr[df_casnr.casnr.notnull()]
        df = df.reset_index(inplace=True)
        df_casnr = df_casnr[['key','casnr']].set_index('casnr')
        df = pd.merge(df, df_casnr, left_on='casnr', right_on='casnr', how='left')
        df.reset_index(inplace=True)
        df = df[['parameter','casnr','key_y']]
        df.columns=['parameter','casnr','key']
        df.loc[df['key'].isnull()]['key'] = cn.NOT_USED 
        df = df.set_index('parameter')
        return df


    def get_non_matched_options(self, options: list, df:pd.DataFrame())->list:
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


    def map_parameters(self, df, file_format, step):
        """
        maps the import file columns to variables. 2 formats are possible: 
        - 1 sample per row: each row represents a sample and each column a parameter
        - 1 value per row: each row represents a measured value there must be a station, parameter and value column
            additional columns can hold either station and sample data or measurement metadata
        """
        if file_format == cn.SAMPLE_FORMATS[0]:
            cols = df.columns
            df_matched_params = pd.DataFrame(cols)
            cols['key'] = cn.NOT_USED
            cols.columns = ['Parameter','key']
            cols.set_index()
            param_lookup_lst = []
            for idx, par in cols.iterrows():
                # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
                # and an error is thrown
                cols.loc[idx]['key'] = st.selectbox(idx, options=param_lookup_lst)
        elif file_format == cn.SAMPLE_FORMATS[1]:
            lst_without_not_used = df.columns
            lst_with_not_used =  [cn.NOT_USED]
            lst_with_not_used.extend(df.columns)

            par_map = {}
            par_map['station_column'] = st.selectbox("station column", lst_without_not_used)
            par_map['sample_date_collected_column'] = st.selectbox("sample date", lst_with_not_used)
            par_map['latitude_column'] = st.selectbox("Latitude (dec°)", lst_with_not_used)
            par_map['longitude_column'] = st.selectbox("Longitude (dec°)", lst_with_not_used)
            par_map['value_column'] = st.selectbox("value column", lst_without_not_used)
            par_map['parameter_column'] = st.selectbox("parameter name column", lst_without_not_used)
            par_map['casnr_column'] = st.selectbox("CasNr column", lst_with_not_used)
            
            stations = df[par_map['station_column']].unique()
            if par_map['casnr_column'] != lst_with_not_used[0]:
                parameters = pd.DataFrame(df[[par_map['parameter_column'], par_map['casnr_column']]].drop_duplicates())
                parameters['key'] = lst_with_not_used[0]
                parameters.columns = ['parameter', 'casnr', 'key']
                parameters = parameters[parameters['parameter'].notnull()]
                parameters = self.map_parameter_with_casnr(parameters)
            else:
                parameters = pd.DataFrame(df[par_map['parameter_column']].unique())
                parameters['key'] = lst_with_not_used[0]
                parameters.columns = ['parameter', 'key']
                parameters = parameters[parameters["parameter"].notnull()]
            
            num_pmd = st.session_state.parameters_metadata.query("type == 'chem'")
            lookup_par_list = list(num_pmd.reset_index()['key'])
            lst = ['Not used']
            lst.extend(list(num_pmd['name']))
            st.markdown("#### Map parameters")

            # automatically (if casnr is present) or manually map lookup parameter to dataset-parameters 
            for idx, par in parameters.iterrows():
                # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
                # and an error is thrown
                try:
                    if not helper.isnan(parameters.loc[idx]['key']):
                        id = lookup_par_list.index(parameters.loc[idx]['key'])+1
                    else:
                        id = 0
                except:
                    id = 0
                parameters.loc[idx]['key'] = st.selectbox(idx, options=lst, index=id)
            # remove all unmapped parameters from dataframe
            parameters = parameters[parameters['key'] != 'Not used']

            return parameters, par_map
    
    def identify_station_columns(self, show_only_matched):
        st.markdown("**Preview**")
        st.write(self.df_raw.head())
        filtered_columns = self.all_columns[(self.all_columns['type']=='st') | (self.all_columns['type'].isnull())]
        options = ['Not used', 'Station identifier', 'Geopoint', 'Latitude', 'Longitude', 'Other station parameter']
        for idx, col in filtered_columns.iterrows():
            if (self.all_columns.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
                if self.all_columns.loc[idx]['key']==options[0]:
                    self.all_columns.loc[idx]['type'] = None
                else:
                    self.all_columns.loc[idx]['type'] = 'st'
        st.session_state.all_columns = self.all_columns

    def identify_sample_columns(self,show_only_matched):
        st.markdown("**Preview**")
        st.write(self.df_raw.head())
        st.session_state.has_sample_columns = st.checkbox("Dataset has not sample columns")
        if not st.session_state.has_sample_columns:
            filtered_columns = self.all_columns[(self.all_columns['type']=='sa') | (self.all_columns['type'].isnull())]
            options = ['Not used', 'Sample identifier', 'Sampling date', 'Sampling date', 'Sampling datetime','Other sample parameter']
            for idx, col in filtered_columns.iterrows():
                if (self.all_columns.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                    self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
                    if self.all_columns.loc[idx]['key']==options[0]:
                        self.all_columns.loc[idx]['type'] = None
                    else:
                        self.all_columns.loc[idx]['type'] = 'sa'
            st.session_state.all_columns = self.all_columns


    def identify_values_meta_data_columns(self,show_only_matched)->list:
        st.markdown("**Preview**")
        filtered_columns = self.all_columns[(self.all_columns['type']=='md') | (self.all_columns['type'].isnull())]
        options = ['Not used', 'Parameter', 'Value', '<DL qualifier', '<DL qualifier + value', 'Unit', 'CAS-Nr','Detection limit', 'Method', 'Comment']
        # options = self.get_non_matched_options(options, filtered_columns)
        for idx, col in filtered_columns.iterrows():
            if (self.all_columns.loc[idx]['key'] != cn.NOT_USED) or (not show_only_matched):
                self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
                if self.all_columns.loc[idx]['key']==options[0]:
                    self.all_columns.loc[idx]['type'] = None
                else:
                    self.all_columns.loc[idx]['type'] = 'md'
        st.session_state.all_columns = self.all_columns
    
    def match_parameters(self, show_only_matched)->str:
        def get_column_name(key):
            if key in list(self.all_columns['key']):
                result = self.all_columns[self.all_columns['key'] == key].index 
                result = pd.DataFrame(result).iloc[0]['column_name']
            else:
                result = None
            return 

        self.all_columns.reset_index(inplace=True)
        self.all_columns.set_index('column_name', inplace=True)
        parameter_col = get_column_name('Parameter')
        casnr_col = get_column_name('CAS-Nr') 
        if len(self.parameters) == 0:
            self.parameters = pd.DataFrame(self.df_raw[[parameter_col, casnr_col]].drop_duplicates())
            self.parameters.columns = ['parameter','casnr']
            self.parameters['key'] = cn.NOT_USED
        else:
            self.parameters = st.session_state.parameters
        st.write(self.parameters)
        #self.parameters = self.parameters[self.parameters['parameter'].notnull()]
        self.parameters = self.map_parameter_with_casnr(self.parameters)
            
        num_pmd = st.session_state.parameters_metadata.query("type == 'chem'")
        lookup_par_list = list(num_pmd.reset_index()['key'])
        lst = [cn.NOT_USED]
        lst.extend(list(num_pmd['name']))
        st.markdown("#### Map parameters")

        # automatically (if casnr is present) or manually map lookup parameter to dataset-parameters 
        for idx, par in self.parameters.iterrows():
            # if an identical parameter erroneously uses various Casnr expressions the key is not unique anymore
            # and an error is thrown

            if not (helper.isnan(par['key']) and show_only_matched):
                try:
                    if not helper.isnan(par['key']):
                        id = lookup_par_list.index(self.parameters.loc[idx]['key'])+1
                    else:
                        id = 0
                except:
                    id = 0
                if not(show_only_matched) or (par['key'] != np.nan):
                    self.parameters.loc[idx]['key'] = st.selectbox(idx, options=lst, index=id)
        # remove all unmapped parameters from dataframe
        # st.session_state.parameters = parameters[parameters['key'] != 'Not used']
        st.session_state.parameters = self.parameters


    def pivot_table(self):
        def filter_mapped_parameters(df) -> pd.DataFrame:
            used_parameters = self.parameters.dropna(subset=['key']).reset_index()
            used_parameters = self.parameters[self.parameters['key'] != cn.NOT_USED].reset_index()
            used_parameters = list(used_parameters['parameter'])
            df = df[ df[par_col].isin(used_parameters) ]
            return df, used_parameters

        def get_cols_dict() -> dict:
            mapped_parameters = st.session_state.all_columns
            mapped_parameters.reset_index(inplace=True)
            mapped_parameters.set_index('key',inplace=True)
            return mapped_parameters['column_name'].to_dict()
        
        def get_parameter_list()->list:
            mapped_parameters = st.session_state.parameters.reset_index()
            return list(mapped_parameters['parameter'])
        
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
        
        
        cols_dict = get_cols_dict()
        par_col = cols_dict['Parameter']
        value_col = cols_dict['Value']
        sample_cols = [cols_dict['Sampling date']]
        station_cols = [cols_dict['Station identifier']]
        show_settings()
        
        use_only_matched_parameters = st.checkbox("Use only matched parameters")
        if use_only_matched_parameters:
            df, used_parameters = filter_mapped_parameters(self.df_raw)
        else:
            df = self.df_raw
            used_parameters = list(self.parameters.reset_index()['parameter'])
        with st.expander("Used measured parameters"):
            st.write(used_parameters)
        if st.button("Unmelt table"):
            df, ok = self.unmelt_data(df, par_col, value_col, sample_cols)
            if ok:
                st.session_state.major_ions_complete = helper.major_ions_complete(df)
                if st.session_state.major_ions_complete:
                    df = helper.complete_columns(df)
                self.df_pivot = df
                df.to_csv('data.csv', sep=';')
                st.success("data was successfully transformed")
            st.write(self.df_pivot)


    def run_step(self):
        steps = ['Match station columns', 'Match sample columns', 'Match metadata columns', 'Match parameters', 'Pivot table' ]
        option_item_sel = st.sidebar.selectbox('Import steps', steps)
        self.step = steps.index(option_item_sel)+1
        show_only_matched = st.sidebar.checkbox("Show only matched parameters")
        
        title = self.texts_dict[f"step{self.step}_title"]
        info = self.texts_dict[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        if self.step == 1:
            self.identify_station_columns(show_only_matched)
        elif self.step == 2:
            self.identify_sample_columns(show_only_matched)
        elif self.step == 3:
            self.identify_values_meta_data_columns(show_only_matched)
        elif self.step == 4:
            self.match_parameters(show_only_matched)
        elif self.step == 5:
            self.pivot_table()
            

