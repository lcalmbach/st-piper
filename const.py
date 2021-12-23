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

piper_cfg = {
    'gap': 20,
    'figure_padding_left': 10,
    'figure_padding_right': 10,
    'figure_padding_top': 10,
    'figure_padding_bottom': 20,
    'marker_size': 10,
    'tick_len': 2,
    'grid_color': 'silver',
    'line_color': 'black',
    'grid_line_pattern': 'dashed',
    'tick_label_font_size': 8,
    'axis_title_font_size': 10,
    'grid_line_pattern': 'dotted',
    'legend_location': "top_right",
    'arrow_length': 5,
    'arrow_size': 5,
    'image_file_format': 'png'
}
map_cfg = {
    'extent': 7000,
    'fill_colors': ['blue', 'orange', 'green'],
    'fill_alpha': 0.8,
    'symbol_size': 10,
    'max_prop_size': 20,
    'min_prop_size': 2,
    'lin_palette': 'Magma256',
    'plot_width': DEFAULT_PLOT_WIDTH_L,
}

scatter_cfg = {
    'x_par': '',
    'y_par': '',
    'colors': ['blue', 'orange', 'green'],
    'fill_alpha': 0.8,
    'symbol_size': 10,
    'plot_width': DEFAULT_PLOT_WIDTH_L,
    'plot_height': DEFAULT_PLOT_HEIGHT_L,
}

histogram_cfg = {
    'par': '',
    'bin_width': '',
    'colors': ['#00FFAA', 'orange', 'green'],
    'fill_alpha': 0.8,
    'y_max': 0,
    'plot_height': DEFAULT_PLOT_HEIGHT_L,
    'plot_width': DEFAULT_PLOT_WIDTH_L,
    'plot_title': "",
    'x_axis_title': "",
    'y_axis_title': "Count",
    'bins': 20,
    'x_min': 0,
    'x_max': 0,
}

time_series_cfg = {
    'parameters': False,
    'parameters': ['chlorid'],
    'stations': ['F_0795'],
    'show_marker': True,
    'show_line': True,
    'show_guideline': True,
    'markers': ['circle'],
    'lines': ['blue'],
    'fill_alpha': 0.8,
    'symbol_size': 10,
    'yl_axis_title': 'Concentration in mg/L',
    'yl_unit': 'mg/L',
    'has_yr_axis': False,
    'plot_title': '',
    'plot_width': DEFAULT_PLOT_WIDTH_L,
    'plot_height': DEFAULT_PLOT_HEIGHT_M,
}

sin60 = math.sin(math.radians(60))
cos60 = math.cos(math.radians(60))
sin30 = math.sin(math.radians(30))
cos30 = math.cos(math.radians(30))
tan60 = math.tan(math.radians(60))

SAMPLE_FORMATS = ["One row per sample", "One row per value"]

NOT_USED = 'Not used'
NOT_MAPPED = 'Not mapped'
SEPARATORS = [';',',','\t']

CTYPE_STATION = 'st'
CTYPE_SAMPLE = 'sa'
CTYPE_VAL_META = 'md'
CTYPE_PARAMETER = 'pa'

STATION_IDENTIFIER_COL = 'Station identifier'
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

DATE_FORMAT_LIST = ['%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y']
ENCODINGS = ['utf8', 'cp1252']
DEFAULT_GUIDELINE = 'epa_mcl'
GUIDELINE_ROOT = './guidelines/'

COMPARE_OPTIONS = ['>', '<', '=', '>=', '<=', '!=']
SPLASH_IMAGE = "water-2630618-wide.jpg"
LOTTIE_URL = 'https://assets2.lottiefiles.com/packages/lf20_B6txqj.json'