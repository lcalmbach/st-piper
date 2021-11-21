# Use Cases
## Info
### No Menu options
User sees general inforamtion on app and the dataset that is currently loaded
1. System displays an introduction, the current dataset and parameters: both shown in expander
## Data
### Load New Dataset
- samples per row: dataset is imported as current_dataset and current_dataset_melted is generated.
- value per row: current_dataset_melted is imported and current_dataset is generated
for the dataframe *current_dataset* meq/L and meq/L% for major ions are calculated
#### import file to dataframe
prerequisits: file has been loaded
1. user selects data format and separator
1. system presents upload widget
1. user uploads file
1. system checks if file is valid: dbd!
1. user presses *Import Data* button
1. system displays imported data

#### format 1 row per value
**match station parameters**
1. system presents all columns
1. user selects at the minimum the station identifier column
1. system sets *stations_params_valid* flag and allows sample parameters to be mapped
1. if the geopoint parameter is mapped, the geopoint is split into the latitude, longitude columns and these columns are mapped automatically
1. if the lat/long parameters are mapped, the flag *lat_long_valid* is set to true: maps menu is only shown if this flag is set.
**match sample parameters**
1. Sample parameters are not mandatory: measurements can be linked to stations only, if the user selects the no sample columns, the *sample_params_valid* flag is set to true. Otherwise, it is set to true, if at least one sample parameter has been selected, e.g. the sample date or a sample identifier.
1. If the sample date parameter is mapped, the *sample_date_valid* flag is set to true.
match metadata columns parameters
**match parameters**

**Load configuration**

**Save configuration**

