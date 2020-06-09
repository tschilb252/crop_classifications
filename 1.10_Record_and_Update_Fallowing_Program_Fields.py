
###############################################################################################
###############################################################################################

# Name:             1.10_Record_and_Update_Fallowing_Program_Fields.py
# Author:           Kelly Meehan, USBR
# Created:          20190826
# Updated:          20200608 
# Version:          Created using Python 3.6.8 

# Requires:         Pyhton 3.x

# Notes:            This script is intended to be used as a stand-alone script.

# Description:      This script allows a user to draw a feature set polygon used to subset a feature class for which corresponding fields #                   will have select attribute table values overwritten. 
                  
#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#
#                      Parameters tab:    
#                           Field Borders Feature Class     Feature Layer (Data Type) > Required (Type) > Input (Direction)
#                           AOI_Polygon                     Feature Set (Data Type) > Required (Type) > Direction (Input) 
#                           Geodatabase                     Workspace (Data Type) > Required (Type) > Input (Direction)

# import arcpy

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
        
#         # Set a default value for Geodatabase parameter
#         if self.params[0].value:    
#             feature_class_workspace = os.path.dirname(self.params[0].value.value)
#             if not self.params[2].altered:
#                 self.params[2].value = feature_class_workspace
            
#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""
#             # Ensure that Geodatabase parameter receives a geodatabase 
#         if self.params[2].value:
#             workspace_name = os.path.basename(self.params[2].value.value)
#             if os.path.splitext(workspace_name)[1] != '.gdb':
#                 self.params[2].setErrorMessage(workspace_name + ' is not an appropriate value to pass to Geodatabase parameter. Please provide a geodatabase')
    
#     def isLicensed(self):
#         """Set whether tool is licensed to execute."""
#         return True

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Create a backup copy of Field Borders Feature Class
# 2. Subset Field Borders Feature Class by the User-drawn Feature Set
# 3. Create table showing which fields to change back to fallow (1430) later in Final Label
# 4. Clear Field Borders Feature Class attribute table fields CLASS and Crop_Type for Program Fallow Fields that were marked as fallow during ground truth 

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy, os, sys

# 0.1 Assign variables to tool parameters

# User selects Field Borders Feature Class
field_borders_feature_class = arcpy.GetParameterAsText(0) 

# User creates new temporary feature class (feature set) designating full area of interest
aoi_polygon = arcpy.GetParameterAsText(1)

# User selects output geodatabase
gdb_path = arcpy.GetParameterAsText(2)

# 0.2 Set environment settings

# Set overwrite permissions to true in case user reruns tool (and redraws aoi)
arcpy.env.overwriteOuptut = True

#----------------------------------------------------------------------------------------------

# 1. Create a backup copy of Field Borders Feature Class in case anything goes awtry

region_and_time = os.path.basename(field_borders_feature_class)

field_borders_copy = os.path.join(gdb_path, region_and_time + '_Backup')

arcpy.CopyFeatures_management(in_features = field_borders_feature_class, out_feature_class = field_borders_copy)

#----------------------------------------------------------------------------------------------

# 2. Subset Field Borders Feature Class by the User-drawn Feature Set

fallowing_program_fields = os.path.join(gdb_path, region_and_time + '_Fallowing_Program_Fields')

selection_layer = arcpy.SelectLayerByLocation_management(in_layer = field_borders_feature_class, overlap_type = 'HAVE_THEIR_CENTER_IN', select_features = aoi_polygon) 

# Create list of FIELD_IDs of Program Fallow Fields
program_fields_list = [row[0] for row in arcpy.da.SearchCursor(in_table = selection_layer, field_names = 'FIELD_ID')]

arcpy.CopyFeatures_management(in_features = selection_layer, out_feature_class = fallowing_program_fields)

arcpy.AddMessage('Generated feature class: ' + fallowing_program_fields)

#----------------------------------------------------------------------------------------------

# 3. Create table showing which fields to change back to fallow (1430) later in Final Label

fallowing_program_table = region_and_time + '_Fallowing_Table'

arcpy.TableToTable_conversion(in_rows = fallowing_program_fields, out_path = gdb_path, out_name = fallowing_program_table)

arcpy.AddMessage('Created table: ' + fallowing_program_table + 'in: ' + gdb_path)

#----------------------------------------------------------------------------------------------

# 4. Clear Field Borders Feature Class attribute table fields CLASS and Crop_Type for Program Fallow Fields that were marked as fallow during ground truth 

try:
    with arcpy.da.UpdateCursor(in_table = field_borders_feature_class, field_names = ['CLASS', 'Crop_Type', 'FIELD_ID']) as cursor:
        for row in cursor:
            if row[0] == 1 or row[0] == 0:
                if row[1] == 1403 and row[2] in program_fields_list:
            #if row[0] == 1 and row[1] == 1403 and row[2] in program_fields_list:
                    row[0] = 0
                    row[1] = 0
            cursor.updateRow(row)
except RuntimeError:
    arcpy.AddError('Please close ' + field_borders_feature_class + 'and ru-run tool')
    sys.exit(0) 
else:
    arcpy.AddMessage('Set Field Border Feature Class attribute table fields CLASS and Crop_Type to 0 for the following Fallowing Program Fields: ' + str(program_fields_list))



