import math
from enum import Enum

TEST_DATASET =  "./datasets/test_data.csv"
MARKERS = ['circle','square','triangle','diamond','inverted_triangle','hex','asterisk','circle_cross','circle_dot',
            'circle_x','circle_y','cross','dash','diamond_cross','diamond_dot','dot','hex_dot','plus','square_cross',
            'square_dot','square_pin','square_x','star','star_dot','triangle_dot','triangle_pin','x','y']

DEFAULT_PLOT_WIDTH_L = 800
DEFAULT_PLOT_HEIGHT_L = 600
DEFAULT_PLOT_WIDTH_M = 600
DEFAULT_PLOT_HEIGHT_M = 400
DEFAULT_PLOT_WIDTH_S = 350
DEFAULT_PLOT_HEIGHT_S = 250

TEXT_FILE_TEMPLATE = 'texts_{}.json'

# https://www.loc.gov/standards/iso639-2/php/code_list.php
LANGAUAGE_DICT = {
    'en': 'English',
    'de': 'German',
    'zh': '中文'
}

sin60 = math.sin(math.radians(60))
cos60 = math.cos(math.radians(60))
sin30 = math.sin(math.radians(30))
cos30 = math.cos(math.radians(30))
tan60 = math.tan(math.radians(60))

NOT_USED = 'Not used'
NOT_MAPPED = 'Not mapped'
SEPARATORS = [';',',','\t']

CTYPE_STATION = 13
CTYPE_SAMPLE = 14
CTYPE_VAL_META = 15
CTYPE_OBSERVATION = 12

STATION_IDENTIFIER_COL = 'station_identifier'
LATITUDE_COL = 'latitude'
LONGITUDE_COL = 'longitude'
STATION_ELEVATION_COL = 'station_elevation'
OTHER_STATION_COL = 'Other station column'
COLOR_COL = '_color'
PROP_SIZE_COL = '_prop_size'

SAMPLE_IDENTIFIER_COL = 'sample_identifier'
SAMPLE_DATE_COL = 'sampling_date'
SAMPLE_TIME_COL = 'sampling_time'

PARAMETER_COL = 'parameter_name'
CASNR_COL = 'case_nr'
MDL_COL = 'method_detection_limit'
VALUE_COL = 'value'
VALUE_NUM_COL = 'value_numeric'
ND_FLAG_COL = 'nd_flag'
ND_QUAL_COL = '<mdl_qualifier'
UNIT_COL = 'Unit'
METHOD_COL = 'Method'
CATEGORY_COL = 'Parameter group'
META_COLUMN_OPTIONS = []

PAR_CALCIUM = 'ca'
PAR_SODIUM = 'na'
PAR_POTASSIUM = 'k'
PAR_MAGNESIUM = 'mg'

PAR_CHLORIDE = 'cl'
PAR_SULFATE = 'so4'
PAR_ALKALINITY = 'alk'

PAR_TEMPERATURE = 'temp'
PAR_COND = 'cond_25'
PAR_PH = 'ph'

DATE_FORMAT_DB = '%Y-%m-%d'
DATE_FORMAT_LIST = ['%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%d/%m/%Y']
ENCODINGS = ['utf8', 'cp1252']
DEFAULT_GUIDELINE = 'epa_mcl'
GUIDELINE_ROOT = './guidelines/'
PROJECT_FILE = 'projects.json'

COMPARE_OPTIONS = ['>', '<', '=', '>=', '<=', '!=']
SPLASH_IMAGE = "./static/water-2630618-wide.jpg"
LOTTIE_URL = 'https://assets2.lottiefiles.com/packages/lf20_B6txqj.json'
HELP_SITE = 'https://lcalmbach.github.io/fontus-help/'
HELP_ICON = "./static/help1600.png"
MAX_LEGEND_ITEMS = 20

DEFAULT_PROJECT = 1
# Project access
PROJECT_OWNER = 3
READ = 1
WRITE = 2

SCATTER_ID = 1
TIME_SERIES_ID = 2
PIPER_ID = 3
BOXPLOT_ID = 4
MAP_ID = 5
SCHOELLER_ID = 6
HISTOGRAM_ID = 7
HEATMAP_ID = 8
EXCEEDANCE_ANALYSIS_ID = 9
TREND_ANALYSIS_ID = 10
TRANSFORM_MOLAR_WEIGHT_ID = 11
CALC_SAR_ID = 12
SATURATION_ANALYSIS_ID=13

SIMPLE_CONCENTRATION_CAT = 6
MOL_CONCENTRATION_CAT = 7
LENGTH_CAT = 8
SURFACE_CAT = 9
WEIGHT_CAT = 10
TEMPERATURE_CAT = 11

CALCIUM_ID = 4
MAGNESIUM_ID = 7
SODIUM_ID = 5
POTASSIUM_ID = 6
SULFATE_ID = 9
CHLORID_ID = 8
ALKALINITY_ID = 10
BICARBONATE_ID = 11
CARBONATE_ID = 12

PARKEY2ID_DICT = {
    'SAMPLE_IDENTIFIER_ID': 1,
    'SAMPLE_DATE_ID': 24,
    'SAMPLE_TIME_ID': 'sampling_time',

    'LONGITUDE_ID': 3,
    'LATITUDE_ID': 2,
    'STATION_IDENTIFIER_ID': 1,
    
    'NUMERIC_VALUE_ID': 26,
    'VALUE_ID': 39,
    'UNIT': 40,
    'MDL': 41,
    'PARAMETER':21,

    'COND_25_ID': 17,
    'WATER_TEMP_ID': 19,
    'SAMPLE_IDENTIFIER_ID': 25
    }

MAJOR_IONS = [
    CALCIUM_ID ,
    MAGNESIUM_ID,
    SODIUM_ID, 
    POTASSIUM_ID, 
    SULFATE_ID, 
    CHLORID_ID, 
    ALKALINITY_ID, 
    BICARBONATE_ID, 
    CARBONATE_ID,
]

MAJOR_ANIONS = [
    SULFATE_ID, 
    CHLORID_ID, 
    ALKALINITY_ID, 
    BICARBONATE_ID, 
    CARBONATE_ID,
]

MAJOR_CATIONS = [
    CALCIUM_ID ,
    MAGNESIUM_ID,
    SODIUM_ID, 
    POTASSIUM_ID, 
]

#observation fields
PARAMETER_ID = 'parameter_id'
STATION_ID = 'station_id'
DEFAULT_DATE_FORMAT = 'mm/dd/yyyy'
DEFAULT_USER_ID = 1
DEFAULT_PROJECT_ID = 1

class Codes(Enum):
    USER_PROJECT_PERMISSION = 1
    ROW_FORMAT = 2
    UNIT_CATEGORY = 3
    PARAMETER_TYPE = 4
    DATATYPE = 5

class ParTypes(Enum):
    OBSERVATION = 12
    STATION = 13
    VAL_META = 15
    PARAMETER = 44

class Date_types(Enum):
    STR = 16
    INT = 17
    FLOAT = 18
    BOOL=19
    DATETIME=20
    LOOKUP_LIST=21

# master parameters
class MP(Enum):
    SAMPLE_NR = 25
    NUMERIC_VALUE = 26
    GENERAL_STATION_PARAMETER = 27
    GENERAL_SAMPLE_PARAMETER = 28
    TOP_OF_CASING = 32
    YEAR_OF_CONSTRUCTION = 33
    YEAR_OF_DECOMMISSION = 34
    CAS_NUMBER = 36
    PARAMETER_GROUP = 37
    GENERAL_METADATA = 38
    VALUE = 39
    UNIT = 40
    PARAMETER = 21
    PH = 20
    SAMPLING_DATE = 24
    STATION_IDENTIFIER =  1
    LATITUDE = 2
    LONGITUDE= 3
    GENERAL_OBSERVATION_PARAMETER = 29
    METHOD_DETECTION_LIMIT = 23
    CONDUCTIVITY_25C = 17
    TDS = 18
    CALCIUM = 4
    SODIUM = 5
    POTASSIUM =  6
    MAGNESIUM =  7
    ALKALINITY = 10
    CHLORIDE= 8
    SULFATE = 9
    BICARBONATE = 11
    CARBONATE = 12
    NITRATE = 13
    IRON = 14
    MANGANESE = 15
    ARSENIC = 16
    TEMPERATURE = 19
    WELL_DEPTH = 30
    GROUND_ELEVATION = 31

AGG_GRID_COL_HEIGHT = 30

class ENUMS(Enum):
    user_permission=1
    import_row_format = 2
    unit_category = 3
    parameter_type = 4
    data_type = 5

class PERMISSION(Enum):
    Read = 1
    Write = 2
    Full = 3
    NoPermission = 25

class DATA_FORMAT(Enum):
    ValuePerRow = 4
    SamplePerRow = 5
