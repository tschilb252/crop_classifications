
###############################################################################################
###############################################################################################

# Name:             1.00_Crop_Type_Frequency_Table.py
# Author:           Kelly Meehan, USBR
# Created:          20190812
# Updated:          20200827 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool allows a user to create a dbf and Excel frequency table of acreage and number of fields by crop type.
#                   User should have a feature class of with ACRES and Crop_Type attribute table fields. 
                    
#----------------------------------------------------------------------------------------------
 
# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Field Borders Feature Class    Feature Layer (Data Type) > Required (Type) > Input (Direction)
#                           Documents Directory            Workspace (Data Type) > Required (Type) > Input (Direction)

#                       Validation tab:

# import arcpy, os

# import arcpy, os

# class ToolValidator(object):
#     """Class for validating a tool's parameter values and controlling
#     the behavior of the tool's dialog."""

#     def __init__(self):
#         """Setup arcpy and the list of tool parameters.""" 
#         self.params = arcpy.GetParameterInfo()

#     def initializeParameters(self):
#         """Refine the properties of a tool's parameters. This method is 
#         called when the tool is opened."""

#     def updateParameters(self):
#         """Modify the values and properties of parameters before internal
#         validation is performed. This method is called whenever a parameter
#         has been changed."""
        
#          # Set default directory for Documents Directory
#         if self.params[0].value:
#             if not self.params[1].altered:
#                 covs_directory = os.path.dirname(self.params[0].value.value) 
#                 shapefile_name = os.path.basename(self.params[0].value.value)
#                 region_time_caps = shapefile_name.rsplit(sep = '_', maxsplit = 1)[0].upper()              
#                 docs_directory = os.path.abspath(os.path.join(covs_directory, '..', 'docs_' + region_time_caps))   
#                 self.params[1].value = docs_directory

#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""
   
#     def isLicensed(self):
#         """Set whether tool is licensed to execute."""
#         return True

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Create a dbf and Excel frequency table of acreage and number of fields by crop type

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy, os

# 0.1 Read in tool parameters

# User selects Field Borders Feature Class 
field_borders_feature_class = arcpy.GetParameterAsText(0)

# 0.2 Read in tool arguments
output_directory = arcpy.GetParameterAsText(1)

# 0.2 Set environment settings

# Set overwrite permissions to true in case user reruns tool (and redraws aoi)
arcpy.env.overwriteOuptut = True

# ---------------------------------------------------------------------------------

# 1. Create a dbf and Excel frequency table of acreage and number of fields by crop type

# Create frequency dBASE table

frequency_table_name = os.path.basename(field_borders_feature_class) + '_Crop_Summary.dbf' 
frequency_table = os.path.join(output_directory, frequency_table_name) 

arcpy.Frequency_analysis(in_table = field_borders_feature_class, out_table = frequency_table, frequency_fields = 'Crop_Type', summary_fields = 'ACRES')

arcpy.AddMessage('Generated frequency table:' + str(frequency_table))

# Convert dBASE table to Excel file

excel_file_name = os.path.splitext(frequency_table)[0] + '.xlsx'
excel_file = os.path.join(output_directory, excel_file_name) 

arcpy.TableToExcel_conversion(Input_Table = frequency_table, Output_Excel_File = excel_file)

arcpy.AddMessage('Converting: ' + str(frequency_table_name) + 'to Excel table: ' + str(excel_file))     
