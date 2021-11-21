import const as cn
import helper
import pandas as pd
import uuid

from metadata import Metadata

class Config():
    def __init__(self):
        self.raw_data = pd.DataFrame()
        self.row_sample_df = pd.DataFrame()
        self.row_value_df = pd.DataFrame()
        self.col2key = {}
        self.key2col = {}
        self.file_format = ''
        self.stations_params_valid = False
        self.sample_params_valid = False
        self.meta_params_valid = False
        self.params_params_valid = False
        self.sessionid = uuid.uuid1() # or uuid.uuid4()
        self.parameters_metadata = Metadata()
        # self.current_dataset = get_data()
        self.piper_config = cn.cfg
        self.step = 0
    def stations_params_valid(self):
        result = cn.STATION_IDENTIFIER_COL in self.key2col.keys
    
    def sample_params_valid(self):
        result = cn.SAMPLE_IDENTIFIER_COL in self.key2col.keys or cn.SAMPLE_DATE_COL in self.key2col.keys

    def meta_params_valid(self):
        result = cn.VALUE_COL in self.key2col.keys or cn.DESC_VALUE_COL in self.key2col.keys
        result = result and cn.PARAMETER_COL in self.key2col.keys

    def has_casnr(self):
        result = cn.CASNR_COL in self.key2col.keys
        result = result and cn.PARAMETER_COL in self.key2col.keys
        




