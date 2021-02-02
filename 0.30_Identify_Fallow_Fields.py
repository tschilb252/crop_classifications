###############################################################################################
###############################################################################################

# Name:             Identify_Fallow_Fields.py
# Author:           Kelly Meehan, USBR
# Created:          20200501
# Updated:          20210201 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool calculates the following for each agricultural field: 1) NDVI for each image, 2) delta NDVI between each image, 3) most recent harvest date, and 4) fallow status. There is an assumption imagery is a composited ERDAS IMAGINE raster using the following nomenclature: S2_MSIL1C_YYYYMMDD_Rxxx_Txxxxx_Bx_.img 

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

# Tool setup:       The script tool's properties can be set as follows: 
#
#                      Parameters tab:    
#                           Imagery Directory               Workspace (Data Type) > Required (Type) > Input (Direction)  
#                           Ground Truth Feature Class      Feature Class (Data Type) > Required (Type) > Input (Direction)
#                           Days Required Fallow            String (Data Type) > Required (Type) > Input (Direction)
#                           Fallow NDVI Threshold           String (Data Type) > Required (Type) > Input (Direction)
#                           Harvest NDVI Threshold          String (Data Type) > Required (Type) > Input (Direction)
#                           Red Band                        String (Data Type) > Required (Type) > Input (Direction)
#                           NIR Band                        String (Data Type) > Required (Type) > Input (Direction)
#
#                       Validation tab:
#
# import arcpy, glob

# class ToolValidator(object):
#     """Class for validating a tool's parameter values and controlling
#     the behavior of the tool's dialog."""

#     def __init__(self):
#         """Setup arcpy and the list of tool parameters.""" 
#         self.params = arcpy.GetParameterInfo()

#     def initializeParameters(self):
#         """Refine the properties of a tool's parameters. This method is 
#         called when the tool is opened."""
 
#         # Set defalut parameter values for Days Required Fallow, Fallow NDVI Threshold, and Harvest NDVI Threshold     
#         if not self.params[2].altered:
#             self.params[2].value = '28'
#         if not self.params[3].altered:
#             self.params[3].value = '0.20'
#         if not self.params[4].altered:
#             self.params[4].value = '-0.13'
                                    
#     def updateParameters(self):
#         """Modify the values and properties of parameters before internal
#         validation is performed. This method is called whenever a parameter
#         has been changed."""
                    
#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""

#         # Ensure Days Required Fallow is an integer value
#         if self.params[2].value:
#             days_required_fallow_value = self.params[2].value
#             try:
#                 int(days_required_fallow_value)
#             except ValueError:
#                 self.params[2].setErrorMessage('{0} is not an appropriate value to pass to Days Required Fallow parameter. Please provide an integer value.'.format(days_required_fallow_value))
        
#         # Ensure Fallow NDVI Threshold is float between 0 and 1
#         if self.params[3].value:
#             fallow_ndvi_threshold_value = self.params[3].value 
#             try:
#                 float(fallow_ndvi_threshold_value)
#             except ValueError:
#                 self.params[3].setErrorMessage('{0} is not an appropriate value to pass to NDVI Fallow Threshold parameter. Please provide a decimal value between 0 and 1.'.format(fallow_ndvi_threshold_value))                                              
#             if float(fallow_ndvi_threshold_value) < 0 or float(fallow_ndvi_threshold_value) > 1:
#                 self.params[3].setErrorMessage('{0} is not an appropriate value to pass to NDVI Fallow Threshold parameter. Please provide a decimal value between 0 and 1.'.format(fallow_ndvi_threshold_value)) 
        
#         # Ensure Harvest NDVI Threshold is float between -1 and 0
#         if self.params[4].value:
#             harvest_ndvi_threshold_value = self.params[4].value
#             try:
#                 float(harvest_ndvi_threshold_value)
#             except ValueError:
#                 self.params[4].setErrorMessage('{0} is not an appropriate value to pass to NDVI Fallow Threshold parameter. Please provide a decimal value between -1 and 0.'.format(harvest_ndvi_threshold_value))
            
#             if float(harvest_ndvi_threshold_value) < -1 or float(harvest_ndvi_threshold_value) > 0:
#                 self.params[4].setErrorMessage('{0} is not an appropriate value to pass to Harvest NDVI Threshold parameter. Please provide a decimal value between -1 and 0.'.format(harvest_ndvi_threshold_value))
                
#         if self.params[5].value:
#             red_band_value = self.params[5].value
#             try:
#                 int(red_band_value)
#             except ValueError:
#                 self.params[5].setErrorMessage('{0} is not an appropriate value to pass to Red Band parameter. Please provide an integer value.'.format(red_band_value))
                
#         if self.params[6].value:
#             nir_band_value = self.params[6].value
#             try:
#                 int(nir_band_value)
#             except ValueError:
#                 self.params[6].setErrorMessage('{0} is not an appropriate value to pass to NIR Band parameter. Please provide an integer value.'.format(nir_band_value))

#         # Set drop down list for Red and NIR band selection based on number on imagery band count
#         if self.params[0].value:
#             file_list = os.listdir()
#             imagery_list = []
#             imagery_list = glob.glob('*.img')
#             band_count_result = arcpy.GetRasterProperties_management(in_raster = imagery_list[0], property_type = 'BANDCOUNT')
#             band_count = band_count_result.getOutput(0)
#             self.params[5].filter.list = list(range(1, int(band_count) + 1))
#             self.params[6].filter.list = list(range(1, int(band_count) + 1))
            
#     def isLicensed(self):
#         """Set whether tool is licensed to execute."""
#         return True

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

# User specifies threshold number of days fields should be below NDVI threshold in order to be labeled fallow
days_required_fallow = arcpy.GetParameterAsText(2)

# User sets NDVI threshold value (float between 0 and 1.0) below which fallow fields should fall 
fallow_ndvi_threshold = arcpy.GetParameterAsText(3)

# User sets delta NDVI threshold value (float between -1 and 0) below which harvested fields should fall
harvest_ndvi_threshold = arcpy.GetParameterAsText(4)

# User selects Red Band
red_band = arcpy.GetParameterAsText(5)

# User selects NIR Band
nir_band = arcpy.GetParameterAsText(6)

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
        majority_table = r'in_memory/ndvi_' + image_date
    
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

# Create numpy array from Ground Truth Feature Class
array_ndvi = arcpy.da.TableToNumPyArray(in_table = ground_truth_feature_class, field_names = include_fields)

# Create pandas data frame from numpy array
df_ndvi = pandas.DataFrame(data = array_ndvi)

# Set FIELD_ID column as index
df_ndvi.set_index('FIELD_ID', inplace = True)

# Create copy of NDVI dataframe without Crop_Type
df_ndvi_no_crop = df_ndvi.loc[:,df_ndvi.columns != 'Crop_Type']

# Calculate delta NDVI 
df_delta_ndvi = df_ndvi_no_crop.diff(axis = 1)

# Delete first delta NDVI column with no data
df_delta_ndvi.dropna(axis = 1, how = 'all', inplace = True)

# Change column names to indicate delta NDVI
df_delta_ndvi.columns = [col.replace('ndvi', 'delta') for col in df_delta_ndvi.columns]

#--------------------------------------------------------------------------

# 3. Identify most recent harvest date

# Function to identify most recent harvest date, using -9999 in lieu NA   
def get_recent_harvest(v):
    s = pandas.Series(v < float(harvest_ndvi_threshold))
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

df_ndvi['Fallow_Status'] = numpy.where((df_ndvi[columns_ndvi_recent] < float(fallow_ndvi_threshold)).all(axis = 1), 'Fallow', 'Not_Fallow')

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

# Catch exception caused when trying to join dataframe columns pre-existing in attribute table  
try:
    arcpy.da.ExtendTable(in_table = ground_truth_feature_class, table_match_field = 'FIELD_ID', in_array = output_array, array_match_field = 'FIELD_ID')
except TypeError:
    arcpy.AddWarning('One or more of the following columns:{0} already exist. Please delete and re-run tool.'.format(array_names))
#----------------------------------------------------------------------------------------------

# TTDL

# Convert if checks for existing files of fields and use try except instead
# Easier way of evaluating which NDVI columns are recent?
# Easier to make new data frame of recent NDVI or to only consider certain ones?
# Use numpy to raster and do ndvi calculations with numpy or pandas
# Incorporate either soil moisture check (to catch emergent fields)
# Figure work around for error of extending table if fields already exist. In the case of delta_ndvi*, if this is being re-run it will cause error
# Sort NDVI columns chronologically
# Replace extent table with numpy to table and then join
# Add test ensuring that imagery covers back far enough to cover fallow threshold number of days
# Add test to ensure that all features in feature class are covered by each image (or that will just return NA for area not covered)
# Avoid redundancy of adding NDVI columns to feature class only to delete them before join
# Catch exception if user re-runs tool but did not delete joined columns from ground truth feature class (e.g. ndvi, delta, harvest, and fallow_status columns)
# Have delta NDVI values be daily rates for better comparison between disparate image time intervals