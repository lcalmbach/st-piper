import math

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

CTYPE_STATION = 'st'
CTYPE_SAMPLE = 'sa'
CTYPE_VAL_META = 'md'
CTYPE_PARAMETER = 'pa'

STATION_IDENTIFIER_COL = 'station_key'
GEOPOINT_COL = 'Geopoint'
LATITUDE_COL = 'Latitude'
LONGITUDE_COL = 'Longitude'
SAMPLING_DEPTH_COL = 'Depth'
OTHER_STATION_COL = 'Other station column'
COLOR_COL = '_color'
PROP_SIZE_COL = '_prop_size'
STATION_COLUMNS_OPTIONS = [STATION_IDENTIFIER_COL, GEOPOINT_COL, LATITUDE_COL,
    LONGITUDE_COL, SAMPLING_DEPTH_COL, OTHER_STATION_COL, NOT_USED]

SAMPLE_IDENTIFIER_COL = 'Sample identifier'
SAMPLE_DATE_COL = 'Sampling date'
SAMPLE_TIME_COL = 'Sampling time'
OTHER_SAMPLE_COL = 'Other sample column' 
SAMPLE_COLUMN_OPTIONS = [SAMPLE_IDENTIFIER_COL,SAMPLE_DATE_COL,SAMPLE_TIME_COL,OTHER_SAMPLE_COL, NOT_USED]

PARAMETER_COL = 'Parameter'
CASNR_COL = 'CAS-Nr'
DL_COL = 'Detection limit'
VALUE_NUM_COL = 'Numeric value'

ND_FLAG_COL = '_nd_flag'
ND_QUAL_COL = '<DL qualifier'
ND_QUAL_VALUE_COL = '<DL qualifier + numeric value'
UNIT_COL = 'Unit'
METHOD_COL = 'Method'
COMMENT_COL = 'Comment'
CATEGORY_COL = 'Parameter group'
META_COLUMN_OPTIONS = [NOT_USED, PARAMETER_COL, CASNR_COL,
                       DL_COL, VALUE_NUM_COL, ND_QUAL_COL,
                       ND_QUAL_VALUE_COL, UNIT_COL, METHOD_COL,
                       COMMENT_COL, CATEGORY_COL]

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
SAMPLING_DATE_ID = 24
LONGITUDE_ID = 3
LATITUDE_ID = 2
STATION_IDENTIFIER_ID = 1
COND_25_ID = 17
WATER_TEMP_ID = 19
SAMPLE_IDENTIFIER_ID = 25
NUMERIC_VALUE_ID = 26

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

DEFAULT_PROJECT_ID = 1
DEFAULT_USER_ID = 1
DEFAULT_DATE_FORMAT = 'mm/dd/yyyy'