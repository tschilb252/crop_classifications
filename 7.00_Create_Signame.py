
###############################################################################################
###############################################################################################

# Name:             7.00_Create_Signame.py
# Author:           JM, USBR; edited by Troy Wirth, USBR, and Kelly Meehan, USBR
# Created:          20070410
# Updated:          20201120 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This script adds two new attribute table fields to the Segments Shapefile, croptype and Signame, and populates with Crop_Type, and the concatenation of FIELD_ID - eCognition Segment number - Crop_Type - CROP_PCT - GROWTH_STA - CONDITION, respectively.           
                  
#----------------------------------------------------------------------------------------------
 
# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Segments Shapefile      Feature Layer (Data Type) > Required (Type) > Input (Direction)
#                           Shapefile Directory     Workspace (Data Type) > Required (Type) > Input (Direction)

#                      Validation tab:

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
        
#           # Set default directory for Documents Directory
#         if self.params[0].value:
#             if not self.params[1].altered:
#                 covs_directory = os.path.dirname(self.params[0].value.value)              
#                 self.params[1].value = covs_directory

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
# 1. Add two new attribute fields to Segmentation Shapefile: croptype and Signame
# 2. Populate croptype with Crop_Type, and Signame with the concatenation of FIELD_ID - eCognition Segment number - Crop_Type - CROP_PCT - GROWTH_STA - CONDITION

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy

#----------------------------------------------

# 0.1 Read in tool parameters

# User selects Segments Shapefile, <REGION>_T*_YYYY_segments_*.shp
segments_shapefile = arcpy.GetParameterAsText(0) 

# User selects Coverage Directory
covs_path = arcpy.GetParameterAsText(1)

#--------------------------------------------

# 0.2 Set environment settings

# Do not overwrite outputs
arcpy.env.overwriteOutput = False

#----------------------------------------------------------------------------------------------

# 1. Add two new attribute fields to Segmentation Shapefile: croptype and Signame

fields_dict = {'croptype':'SHORT', 'Signame': 'TEXT'}

for key, value in fields_dict.items():
    if arcpy.ListFields(dataset = segments_shapefile, wild_card = key):
        arcpy.DeleteField_management(in_table = segments_shapefile, drop_field = key)
    arcpy.AddField_management(in_table = segments_shapefile, field_name = key, field_type = value)

# 2. Populate croptype with Crop_Type, and Signame with the concatenation of FIELD_ID - eCognition Segment number - Crop_Type - CROP_PCT - GROWTH_STA - CONDITION

fields = ['Crop_Type', 'croptype', 'Signame', 'FIELD_ID', 'FID', 'CROP_PCT', 'GROWTH_STA', 'CONDITION']

with arcpy.da.UpdateCursor(in_table = segments_shapefile, field_names = fields) as cursor:
    for row in cursor:
        row[1] = row[0]
        row[2] = str(row[3]) + '-' + str(row[4]) + '-' + str(row[0]) + '-' + str(row[5]) + '-' + str(row[6]) + '-' + str(row[7]) 
        cursor.updateRow(row)

