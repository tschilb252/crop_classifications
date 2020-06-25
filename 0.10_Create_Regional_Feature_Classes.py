
###############################################################################################
###############################################################################################

# Name:             0.10_Create_Regional_Feature_Classes.py
# Author:           Kelly Meehan, USBR
# Created:          20190922
# Updated:          20200625 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro and Spatial Analyst Extension

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description       This tool generates a subset ground truth feature class with long-term accuracy assessment field values cleared.

#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Project_Geodatabase             Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           Ground_Truth_Feature_Class      Feature Layer (Data Type) > Required (Type) > Direction (Input) 
#                           Region                          String (Data Type) > Required (Type) > Direction (Input) 

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Generate a new feature class subset to region of interest and with select fields cleared for long-term accuracy assessment features
# 2. Select long-term accuracy assessment features (CLASS == 4) and clear values of select attribute table fields
# 3. Print percentage of fields in this region marked as being in a harvested growth stage during ground truth

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy, os, pandas

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects file geodatabase for region (YYYY_T*_<REGION>.gdb) 
project_geodatabase = arcpy.env.workspace = arcpy.GetParameterAsText(0)

# User selects ground truth feature class
ground_truth_feature_class = arcpy.GetParameterAsText(1) 

# Assign variable to attribute table field name to be used to filter feature class
input_field = 'REGION'

# User types region name 
input_region = arcpy.GetParameterAsText(2)

#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

#-----------------------------------------------------------------------------------------------

# 1. Generate a new feature class subset to region of interest and with select fields cleared for long-term accuracy assessment features

def generate_regional_subset():
        
    # Extract basename from geodatabase
    region_and_time = os.path.splitext(os.path.basename(project_geodatabase))[0] 
    
    # Set new feature class name to basename 
    field_borders_feature_class = os.path.join(project_geodatabase, region_and_time)
    
    # Clear selection of Ground Truth Feature Class so as to avoid a prior selection limiting the number of records copied
    arcpy.SelectLayerByAttribute_management(in_layer_or_view = ground_truth_feature_class, selection_type = 'CLEAR_SELECTION')
    
    # Create a new feature class, a subset of of records from the Ground Truth Feature Class with the same REGION value as the user selected input_region 
    SQL_clause = """{} = '{}'""".format(arcpy.AddFieldDelimiters(ground_truth_feature_class, 'REGION'), input_region) 
    arcpy.Select_analysis(in_features = ground_truth_feature_class, out_feature_class = field_borders_feature_class, where_clause = SQL_clause)
    
    arcpy.AddMessage('Generated Field Borders Feature Class: ' + field_borders_feature_class)
    
    # Clear select attribute table fields for long-term accuracy assessment features
    input_fields = ['CLASS','CROP_TYPE', 'HEIGHT', 'GROWTH_STA', 'CROP_PCT', 'OTHER_PCT', 'CONDITION', 'MOISTURE', 'COMMENTS']
    with arcpy.da.UpdateCursor(in_table = field_borders_feature_class, field_names = input_fields) as cursor:
        for row in cursor:
            if (row[0] == 4):
                row[1] = 0
                row[2] = 0
                row[3] = 0
                row[4] = 0
                row[5] = 0
                row[6] = 0
                row[7] = 0
                row[8] = ''
            cursor.updateRow(row)
    
    arcpy.AddMessage('Cleared data for Long-Term Accuracy Assessment Fields')

#-----------------------------------------------------------------------------------------------

# 2. Generate a frequency table and print out percentage of fields harvested

    # Assign variable to frequency table name 
    growth_stage_table = os.path.join(project_geodatabase, region_and_time + '_Growth_Stage_Frequency')
    
    # Generate frequency table summarizing acres by growth stage values
    arcpy.Frequency_analysis(in_table = field_borders_feature_class, out_table = growth_stage_table, frequency_fields = 'GROWTH_STA', summary_fields = 'ACRES')

#-----------------------------------------------------------------------------------------------
    try:
        # 3. Print percentage of fields in this region marked as being in a harvested growth stage during ground truth 
            
        # Create numpy array from growth stage frequency table, masking NULL values with -9999
        growth_stage_array = arcpy.da.TableToNumPyArray(in_table = growth_stage_table, field_names = '*', skip_nulls = False, null_value = -9999)
        
        # Create pandas data frame from numpy array
        growth_stage_data_frame = pandas.DataFrame(data = growth_stage_array)
        
        # Remove OBJECTID column
        del growth_stage_data_frame['OBJECTID']
        
        # Convert GROWTH_STA column to string 
        growth_stage_data_frame['GROWTH_STA'] = growth_stage_data_frame['GROWTH_STA'].astype(str)
        
        # Replace row index values to GROWTH_STA values
        growth_stage_data_frame.set_index('GROWTH_STA', inplace = True)
        
        # Add summary row for FREQUENCY and ACRES columns
        columns_to_total = ['FREQUENCY', 'ACRES']
        growth_stage_data_frame.loc['Total',:] = growth_stage_data_frame[columns_to_total].sum(axis = 0)
        
        # Convert pandas data frame index to string type
        growth_stage_data_frame.index = growth_stage_data_frame.index.map(str)
      
        # Calculate percentage of fields harvested (growth stage 9)
        if '9' not in growth_stage_data_frame.index:
            arcpy.AddMessage('Percentage of fields in this region marked as harvested growth stage during ground truth is 0%.')
        else:
            harvested_percentage_by_units = round((growth_stage_data_frame.loc['9']['FREQUENCY']/growth_stage_data_frame.loc['Total']['FREQUENCY'])*100, 2)
            arcpy.AddMessage('Percentage of fields in this region marked as harvested growth stage during ground truth: ' + str(harvested_percentage_by_units) + '%')
            
            harvested_percentage_by_acres = round((growth_stage_data_frame.loc['9']['ACRES']/growth_stage_data_frame.loc['Total']['ACRES'])*100, 2)
            arcpy.AddMessage('Percentage of acreage in this region marked as harvested growth stage during ground truth: ' + str(harvested_percentage_by_acres) + '%')
            
        # Suggest that user selects earlier imagery if harvest percentage is greater than 20%
        if 'harvested_percentage_by_units' and 'harvested_percentage_by_acres' in locals(): 
            if harvested_percentage_by_units >= 20 or harvested_percentage_by_acres >= 20:
                arcpy.AddMessage('Consider using a classification image with an acquisition date prior to ground truth verification.')

    except Exception:
        arcpy.AddWarning('Was not able to calculate harvested fields percentage.')
    
#-----------------------------------------------------------------------------------------------

# Execute code
if __name__ == "__main__":
    generate_regional_subset()
 
