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
        self.parameters = {}
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


    def unmelt_data(self, df,parameters, sample_par_map):
        idx = [sample_par_map['station_column'], sample_par_map['sample_date_collected_column']]
        st.write(df)
        df = pd.pivot_table(df,
            values = sample_par_map['value_column'],
            index=[sample_par_map['station_column'], sample_par_map['sample_date_collected_column']], 
            columns=sample_par_map['parameter_column'],
            aggfunc=np.mean
        )
        st.write(df)
        ok = len(df)> 0
        return df, ok


    def map_parameter_with_casnr(self, df):
        df_casnr = st.session_state.parameters_metadata.reset_index()
        df_casnr = df_casnr[df_casnr.casnr.notnull()]
        df_casnr = df_casnr[['key','casnr']].set_index('casnr')
        df = pd.merge(df, df_casnr, left_on='casnr', right_on='casnr', how='left')
        df = df[['parameter','key_y']]
        df.columns=['parameter','key']
        df = df.set_index('parameter')
        st.write(df)
        return df


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
    
    def identify_station_columns(self):
        st.markdown("**Preview**")
        st.write(self.df_raw.head())
        filtered_columns = self.all_columns[(self.all_columns['type']=='st') | (self.all_columns['type'].isnull())]
        options = ['Not used', 'Station identifier', 'Geopoint', 'Latitude', 'Longitude', 'Other station parameter']
        for idx, col in filtered_columns.iterrows():
            self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
            if self.all_columns.loc[idx]['key']==options[0]:
                self.all_columns.loc[idx]['type'] = None
            else:
                self.all_columns.loc[idx]['type'] = 'st'
        st.write(self.all_columns)
        st.session_state.all_columns = self.all_columns

    def identify_sample_columns(self):
        st.markdown("**Preview**")
        st.write(self.df_raw.head())
        has_no_sample_columns = st.checkbox("Dataset has not sample columns")
        filtered_columns = self.all_columns[(self.all_columns['type']=='sa') | (self.all_columns['type'].isnull())]
        st.write(filtered_columns)
        options = ['Not used', 'Sample identifier', 'Sampling date', 'Sampling date', 'Sampling datetime','Other sample parameter']
        for idx, col in filtered_columns.iterrows():
            self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
            if self.all_columns.loc[idx]['key']==options[0]:
                self.all_columns.loc[idx]['type'] = None
            else:
                self.all_columns.loc[idx]['type'] = 'sa'
        st.write(self.all_columns)
        st.session_state.all_columns = self.all_columns


    def identify_values_meta_data_columns(self):
        st.markdown("**Preview**")
        st.write(self.df_raw.head())
        filtered_columns = self.all_columns[(self.all_columns['type']=='md') | (self.all_columns['type'].isnull())]
        st.write(filtered_columns)
        options = ['Not used', 'Parameter', 'Value', 'CAS-Nr','Detection limit']
        for idx, col in filtered_columns.iterrows():
            self.all_columns.loc[idx]['key'] = st.selectbox(idx, options=options, index=options.index(self.all_columns.loc[idx]['key']))
            if self.all_columns.loc[idx]['key']==options[0]:
                self.all_columns.loc[idx]['type'] = None
            else:
                self.all_columns.loc[idx]['type'] = 'md'
        st.write(self.all_columns)
        st.session_state.all_columns = self.all_columns
    
    def match_parameters(self):
        show_matched_only = st.sidebar.checkbox("Show matched parameters only")
        parameter_col = self.all_columns[self.all_columns['key']=='Parameter'].index 
        parameter_col = pd.DataFrame(parameter_col).iloc[0]['column_name']
        casnr_col = self.all_columns[self.all_columns['key']=='CAS-Nr'].index 
        casnr_col = pd.DataFrame(casnr_col).iloc[0]['column_name']

        parameters = pd.DataFrame(self.df_raw[[parameter_col, casnr_col]].drop_duplicates())
        parameters['key'] = cn.NOT_USED
        parameters.columns = ['parameter', 'casnr', 'key']
        parameters = parameters[parameters['parameter'].notnull()]
        parameters = self.map_parameter_with_casnr(parameters)
            
        num_pmd = st.session_state.parameters_metadata.query("type == 'chem'")
        lookup_par_list = list(num_pmd.reset_index()['key'])
        lst = [cn.NOT_USED]
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
            st.write(par['key'],type(par['key']), par['key'] != np.nan)
            if not show_matched_only or par['key'] != np.nan:
                parameters.loc[idx]['key'] = st.selectbox(idx, options=lst, index=id)
        # remove all unmapped parameters from dataframe
        parameters = parameters[parameters['key'] != 'Not used']


    def pivot_table(self, df):
        sample_par_map = {}
        mapped_parameters = self.init_all_columns(df)
        df = df[[sample_par_map['station_column'], 
            sample_par_map['sample_date_collected_column'], 
            sample_par_map['parameter_column'], 
            sample_par_map['value_column']]]
        lst_parameters = list(mapped_parameters.index)
        par_col_key = sample_par_map['parameter_column']
        df=df[ df[par_col_key].isin(lst_parameters) ]
        df = self.unmelt_data(df, lst_parameters, sample_par_map)


    def run_step(self):
        steps = ['Match Station columns', 'Match sample columns', 'Match Metadata columns', 'Match Parameters' ]
        option_item_sel = st.sidebar.selectbox('Import steps', steps)
        self.step = steps.index(option_item_sel)+1
        title = self.texts_dict[f"step{self.step}_title"]
        info = self.texts_dict[f"step{self.step}_info"]
        st.markdown(f"#### Step {self.step}: {title}")
        with st.expander("Info"):
            st.markdown(info)
        if self.step == 1:
            self.identify_station_columns()
        elif self.step == 2:
            self.identify_sample_columns()
        elif self.step == 3:
            self.identify_values_meta_data_columns()
        elif self.step == 4:
            self.match_parameters()

