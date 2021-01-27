###############################################################################################
###############################################################################################

# Name:             Identify_Fallow_Fields.py
# Author:           Kelly Meehan, USBR
# Created:          20200501
# Updated:          20210127 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool calculates the following for each agricultural field: 1) NDVI for each image, 2) delta NDVI between each image, 3) most recent harvest date, and 4) fallow status. There is an assumption imagery is a composited ERDAS IMAGINE raster.

################################################################################################
################################################################################################

# This script will:
# 0. Set up
# 1. Calculate NDVI
# 2. Calculate delta NDVI for time periods (excluding first date)
# 3. Identify most recent harvest date
# 4. Identify fallow fields
# 5. Join pandas dataframe to Ground Truth Feature Class

#----------------------------------------------------------------------------------------------

# 0. Set up 

# 0.0 Import necessary packages
import arcpy, os, glob, pandas, numpy, fnmatch
from datetime import datetime, timedelta

#--------------------------------------------

# 0.1 Read in tool parameters

# User sepecifies imagery directory
imagery_directory = arcpy.GetParameterAsText(0)

# User specifies feature class of agricultural fields containing the following fields: 1) FIELD_ID as unique identifier and 2) Crop_Type of last season's ground truth data
ground_truth_feature_class = arcpy.GetParameterAsText(1)

# User specifies name of region as name without spaces
region = arcpy.GetParameterAsText(2)

# User specifies file geodatabase
geodatabase = arcpy.GetParameterAsText(3)

# User specifies threshold number of days fields should be below NDVI threshold in order to be labeled fallow
days_required_fallow = arcpy.GetParameterAsText(4)

# User sets NDVI threshold value (float between 0 and 1.0) below which fallow fields should fall 
ndvi_fallow_threshold = arcpy.GetParameterAsText(5)

# User sets delta NDVI threshold value (float between -1 and 0) below which harvested fields should fall
harvest_value_threshold = arcpy.GetParameterAsText(6)

# User selects Red Band
red_band = arcpy.GetParameterAsText(7)

# User selects NIR Band
nir_band = arcpy.GetParameterAsText(8)

#--------------------------------------------

# 0.2 Set environment settings

# Set overwrite permissions to true in case user reruns tool (and redraws aoi)
arcpy.env.overwriteOuptut = True

# Change working directory to output directory
os.chdir(imagery_directory)

# Set workspace to output directory
arcpy.env.workspace = imagery_directory

#--------------------------------------------

# 0.3 Check out spatial analyst extension
arcpy.CheckOutExtension('Spatial')

#--------------------------------------------------------------------------

# 1. Calculate NDVI

# Create list of all files in Imagery Directory
file_list = os.listdir()

# Assign variable to empty list (to which .img files to be iterated through will be added)
imagery_list = []

# Create list of composite rasters
imagery_list = glob.glob('*.img')

# Function to calculate zonal mean NDVI per agricultural field

def calculate_ndvi():

    # Create empty lists to which dates will later be added
    date_list = []
    
    for i in imagery_list:
        
        # Extract date from image file name
        image_name = os.path.basename(i) 
        image_name_chunks = image_name.split('_')
        image_date = image_name_chunks[2]
        
        # Clip image by subset area of interest      
        outExtractByMask = arcpy.sa.ExtractByMask(in_raster = i, in_mask_data = ground_truth_feature_class)
        
        # Assign variable to clipped image
        output = r'in_memory\subset_raster_' + image_date
        
        # Check for pre-existing raster and delete
        if arcpy.Exists(output):
            arcpy.Delete_management(in_data = output)
        
        # Save extracted image to memory        
        outExtractByMask.save(output)
       
        # Read in NIR and Red bands
        nir_raster = arcpy.Raster(output + '\\Band_' + str(nir_band))
        red_raster = arcpy.Raster(output + '\\Band_' + str(red_band))
        
        # Generate two new rasters, the first as the top of the ndvi calculation, the second the bottom
        # NOTE: arcpy.sa.Raster function required to read in layer as a raster object and Float function is used to avoid integer outputs
        numerator = arcpy.sa.Float(nir_raster - red_raster)
        denominator = arcpy.sa.Float(nir_raster + red_raster)
        
        # Generate a third raster (in memory) of ndvi (numerator divided by denominator)
        ndvi_output = arcpy.sa.Divide(numerator, denominator)
        
        # Extract date from file name and append to list
        date_list.append(image_date)
        
        # Assign variable to zonal statistics table
        majority_table = r'in_memory/' + region + '_ndvi_' + image_date
    
        # Check for pre-existing table and delete
        if arcpy.Exists(majority_table):
            arcpy.Delete_management(in_data = majority_table)
        
        # Generat zonal statistics (mean) table
        arcpy.sa.ZonalStatisticsAsTable(in_zone_data = ground_truth_feature_class, zone_field = 'FIELD_ID', in_value_raster = ndvi_output, out_table = majority_table, statistics_type = 'MEAN')

        # Check for pre-existing attribute table field and delete        
        if 'ndvi_' + image_date in [field.name for field in arcpy.ListFields(ground_truth_feature_class)]:
            arcpy.DeleteField_management(in_table = ground_truth_feature_class, drop_field = 'ndvi_' + image_date)
            
        # Join table to area of interest subset
        arcpy.JoinField_management(in_data = ground_truth_feature_class, in_field = 'FIELD_ID', join_table = majority_table, join_field  = 'FIELD_ID', fields = 'MEAN')
        
        # Change name of joined attribute table field 
        arcpy.AlterField_management(in_table = ground_truth_feature_class, field = 'MEAN', new_field_name = 'ndvi_' + image_date, new_field_alias = 'ndvi_' + image_date)
        
        # Check for lingering MEAN attribute table field and delete
        if 'MEAN' in [field.name for field in arcpy.ListFields(ground_truth_feature_class)]:
            arcpy.DeleteField_management(in_table = ground_truth_feature_class, drop_field = 'MEAN')
    
calculate_ndvi()

#--------------------------------------------------------------------------

# 2. Calculate delta NDVI for time periods (excluding first date)

# Create list of attribute table fields to include in numpy array (ndvi, FIELD_ID, Crop_Type)
include_fields = [field.name for field in arcpy.ListFields(dataset = ground_truth_feature_class, wild_card = 'ndvi*')]

include_fields.insert(0, 'FIELD_ID')

include_fields.append('Crop_Type')

# Create numpy array from Training Label Signame Geodatabase Table
array_ndvi = arcpy.da.TableToNumPyArray(in_table = ground_truth_feature_class, field_names = include_fields)

# Create pandas data frame from numpy array
df_ndvi = pandas.DataFrame(data = array_ndvi)

# Set FIELD_ID column as index
df_ndvi.set_index('FIELD_ID', inplace = True)

# Create copy of NDVI dataframe without Crop_Type
df_ndvi_no_crop = df_ndvi.loc[:,df_ndvi.columns != 'Crop_Type']

# Calculate delta NDVI 
df_delta_ndvi = df_ndvi_no_crop.diff(axis = 1)

# Change column names to indicate delta NDVI
df_delta_ndvi.columns = [col.replace('ndvi', 'delta') for col in df_delta_ndvi.columns]

# Delete first delta NDVI column with no data
df_delta_ndvi.dropna(axis = 1, how = 'all', inplace = True)

#--------------------------------------------------------------------------

# 3. Identify most recent harvest date

# Function to identify most recent harvest date, using -9999 in lieu NA   
def get_recent_harvest(v):
    s = pandas.Series(v < float(harvest_value_threshold))
    array = s.where(s == True).last_valid_index()
    return '-9999' if array is None else array[6:]

df_delta_ndvi['Harvest_Date'] = df_delta_ndvi.apply(lambda x: get_recent_harvest(x), axis = 1)

# Join delta NDVI dataframe
df_ndvi = df_ndvi.join(df_delta_ndvi, how = 'outer')

#--------------------------------------------------------------------------

# 4. Identify fallow fields

# Create list of all dataframe column names
columns_all = list(df_ndvi.columns.values)

# Create list of delta NDVI column names
columns_ndvi = fnmatch.filter(columns_all, 'ndvi*')

# Set variable for most recent NDVI column name
ultima_ndvi = columns_ndvi[-1]

# Create list of delta NDVI column names
columns_delta = fnmatch.filter(columns_all, 'delta_*')

# Create list of NDVI dates as integers
dates = [d.replace('ndvi_', '') for d in columns_ndvi]
dates_as_integers = [int(d) for d in dates]

# Find beginning of fallow date threshold (date prior to last image by the number of days fields evaluated for fallow status)
day_required_fallow = datetime.strptime(str(dates_as_integers[-1]), "%Y%m%d") - timedelta(int(days_required_fallow))

# Assign variable to integer value (as YYYYYMMFF) of fallow date threshold beginning
date_required_fallow = int(day_required_fallow.strftime("%Y%m%d"))

# Extract dates within fallow analysis timeframe
dates_recent = [r for r in dates_as_integers if r >= date_required_fallow]

# Identify columns with NDVI dates within fallow analysis timeframe
columns_ndvi_recent = ['ndvi_' + str(n) for n in dates_recent]

# Identify columns with delta NDVI dates within fallow analysis timeframe
columns_delta_recent = ['delta_' + str(c) for c in dates_recent]

# Label fields as fallow if NDVI was less than user defined NDVI fallow threshold for the entirety of the fallow analysis timeframe

df_ndvi['Fallow_Status'] = numpy.where((df_ndvi[columns_ndvi_recent] < float(ndvi_fallow_threshold)).all(axis = 1), 'Fallow', 'Not_Fallow')

# Create column with sum values of delta NDVI values within required fallow analysis time range
df_ndvi['recent_delta_sum'] = df_ndvi[columns_delta_recent].sum(axis=1)

# Override fallow label for those fields: 1) whose sum delta NDVI over the required fallow time range was >= 0.01 and the most recent NDVI was >= 0.10 or 2) that had a recent harvest (within the fallow analysis timeframe) which was not previously captured (i.e. crop type is fallow)

for index, row in df_ndvi.iterrows():
    if df_ndvi.loc[index, 'recent_delta_sum'] >= 0.01 and df_ndvi.loc[index, ultima_ndvi] >= 0.10:
        df_ndvi.loc[index, 'Fallow_Status'] = 'Not_Fallow'
    if df_ndvi.loc[index, 'Harvest_Date'] != '-9999' and int(df_ndvi.loc[index, 'Harvest_Date']) <= date_required_fallow and df_ndvi.loc[index, 'Crop_Type'] == 1403:
        df_ndvi.loc[index, 'Fallow_Status'] = 'Not_Fallow'   

# Delete column Crop_Type to avoid issues with upcoming merge 
del df_ndvi['Crop_Type']

#--------------------------------------------------------------------------

# 5. Join pandas dataframe to Ground Truth feature class

# Create list of all pandas dataframe columns
columns_all = list(df_ndvi.columns.values)

# Create list of column to join (i.e. exclude NDVI columns as already pre-existing in feature class)
columns_non_ndvi = [c for c in columns_all if c not in columns_ndvi]

# Create copy of NDVI dataframe, keeping only those to join
df_join = df_ndvi[columns_non_ndvi]

# Convert FIELD_ID index back to column
df_join['FIELD_ID'] = df_join.index

# Join dataframe to feature class (source code: https://my.usgs.gov/confluence/display/cdi/pandas.DataFrame+to+ArcGIS+Table)
output_array = numpy.array(numpy.rec.fromrecords(df_join))
array_names = df_join.dtypes.index.tolist()
output_array.dtype.names = tuple(array_names)
arcpy.da.ExtendTable(in_table = ground_truth_feature_class, table_match_field = 'FIELD_ID', in_array = output_array, array_match_field = 'FIELD_ID')

#----------------------------------------------------------------------------------------------

# TTDL

# Inner buffer fields and then calculate mean NDVI
# Use MEDIAN in zonal status(must first convert floating point to integer)
# Add boolean check mark to indicate whether to run append section or not 
# Fix formatting and numbering
# Add in region string name parameter
# Convert if checks for existing files of fields and use try except instead
# Note assumption of Sentinel imagery using nomenclature from tool 0.2*
# Add parameters to make suggested remove flexible: 1) number of days prior to harvest date, and 2) 
# Allow user to change NDVI value threshold for fallow (defalut to 0.2)
# Easier way of evaluating which NDVI columns are recent?
# Easier to make new data frame of recent NDVI or to only consider certain ones?
# How to deal with NA values in Harvest date in order to do comparison
# Use numpy to raster and do ndvi calculations with numpy or pandas
# Figure work around for error of extending table if fields already exist. In the case of delta_ndvi*, if this is being re-run it will cause error
# Find some way to test if was recently watered using NDWI before increase in delta NDVI and set as not fallow 
# Catch emergent fields with low NDVI and low delta NDVI with heterogeneity index
# Sort NDVI columns chronologically
# Replace extent table with numpy to table and then join
# Add test ensuring that imagery covers back far enough to cover fallow threshold number of days
# Add test to ensure that all features in feature class are covered by each image
# Add parameter for date run and set default to now
# Add bands as parameter to make tool more dynamic
# Change band inputs to drop down list of range of length of number of bands in image
# Auto detect associated bands based on metadata
# Avoid redundancy of adding NDVI columns to feature class only to delete them before join
# Have current date be parameter so that script can be run retroactively
# Catch exception if user re-runs tool but did not delete joined columns from ground truth feature class (e.g. ndvi, delta, harvest, and fallow_status columns)