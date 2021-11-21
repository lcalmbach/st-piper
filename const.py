import math

TEST_DATASET =  "./datasets/test_data.csv"
MARKERS = ['circle','rect','triangle','cross']

cfg = {
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

sin60 = math.sin(math.radians(60))
cos60 = math.cos(math.radians(60))
sin30 = math.sin(math.radians(30))
cos30 = math.cos(math.radians(30))
tan60 = math.tan(math.radians(60))

SAMPLE_FORMATS = ["<specify format>", "One row per sample", "One row per value"]

NOT_USED = 'Not used'
NOT_USED = 'Not mapped'
SEPARATORS = [';',',','\t']

STATION_IDENTIFIER_COL = 'Station identifier'
SAMPLE_IDENTIFIER_COL = 'Sample identifier'
SAMPLE_DATE_COL = 'Sampling date'
SAMPLE_TIME_COL = 'Sampling time'
GEOPOINT_COL = 'Geopoint'
LATITUDE_COL = 'Latitude'
OTHER_STATION_COL = 'Other station column'