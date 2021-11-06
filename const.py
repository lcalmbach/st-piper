import math

TEST_DATASET =  "./datasets/test_data.csv"
MARKERS = ['circle','rect','triangle','cross']

PARAMETERS = {
    'station': {'type': 'station','name': 'Station', 'shortname': 'Station'},
    'latitude': {'type': 'station','name': 'Latitude', 'shortname': 'Latitude'},
    'longitude': {'type': 'station','name': 'Longitude', 'shortname': 'Longitude'},
    'ca': {'type': 'chem','name': 'Calcium', 'shortname': 'Ca', 'fmw': 40, 'valence': 2},
    'na': {'type': 'samchemple','name': 'Sodium', 'shortname': 'Na', 'fmw': 26, 'valence': 2},
    'mg': {'type': 'chem','name': 'Magnesium', 'shortname': 'Mg', 'fmw': 24, 'valence': 2},
    'cl': {'type': 'chem','name': 'Chloride', 'shortname': 'Cl', 'fmw': 35, 'valence': -1},
    'so4': {'type': 'samchemple','name': 'Sulfate', 'shortname': 'SO4', 'fmw': 96, 'valence': -2},
    'alk': {'type': 'chem','name': 'Alkalinity', 'shortname': 'Alk', 'fmw': 100, 'valence': -1},
    'hco3': {'type': 'chem','name': 'Bicarbonate', 'shortname': 'HCO3', 'fmw': 3*16+40+1, 'valence': -1},
    'co3': {'type': 'chem','name': 'Carbonate', 'shortname': 'CO3', 'fmw': 3*16+40, 'valence': -2},
    'no3': {'type': 'chem','name': 'Nitrate', 'shortname': 'NO3', 'fmw': 3*16+40, 'valence': -2},
    'fe': {'type': 'chem','name': 'Iron', 'shortname': 'Fe', 'fmw': 3*16+40, 'valence': 2},
}

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

SAMPLE_FORMATS = ["One row per sample", "One row per value"]