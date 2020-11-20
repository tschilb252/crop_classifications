
###############################################################################################
###############################################################################################

# Name:             6.00_Create_Segments_Shapefile_Populated_with_Ground_Truth_Data.py
# Author:           Jeff Milliken, USBR; modified by Troy Worth, USBR and Kelly Meehan, USBR
# Created:          20180329
# Updated:          20200824 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool runs the identity tool with default values for parameters.

#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#
#                      Parameters tab:    
#                           eCognition Segments             Feature Layer (Data Type) > Required (Type) > Input (Direction) 
#                           Edited Field Borders Shapefile  Feature Layer (Data Type) > Required (Type) > Input (Direction)
#                           Scale Parameter                 String (Data Type) > Required (Type) > Input (Direction)
#                           Shapefile Directory             Workspace (Data Type) > Required (Type) > Input (Direction)

#                       Validation tab: 

# import arcpy, re

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

#         # Set a default value for Edited Field Borders Shapefile
#         if self.params[0].value:
#             if not self.params[1].altered:
#                 eCog_name = os.path.basename(self.params[0].value.value)
#                 region_time_caps = eCog_name.rsplit(sep = '_', maxsplit = 2)[0].upper()
#                 covs_directory = os.path.dirname(self.params[0].value.value)
#                 edtd_shp = os.path.join(covs_directory, region_time_caps + '_edtd.shp')
#                 self.params[1].value = edtd_shp 

#         # Set a default value for Scale Parameter
#         if self.params[0].value:
#             eCog_name = os.path.basename(self.params[0].value.value)
#             if not self.params[2].altered:
#                 scale_param = re.split('[_.]', os.path.basename(eCog_name))[4]
#                 self.params[2].value = scale_param

#         # Set a default value for Scale Parameter
#         if self.params[0].value:
#             if not self.params[3].altered:
#                 self.params[3].value = covs_directory
                                        
#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""

#         # Ensure that Scale Parameter parameter receives a character string consisting of two integers
#         if self.params[2].value:
#             scale_parameter_value = self.params[2].value
#             if len(scale_parameter_value) != 2 or not scale_parameter_value.isdigit():
#                 self.params[2].setWarningMessage('{0} is not an appropriate value to pass to Date Range Begin parameter. Please provide two integer value (e.g. 09 for scale parameter of 9)'.format(scale_parameter_value))
                
#     def isLicensed(self):
#         """Set whether tool is licensed to execute."""
#         return True
    
###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Create a new shapefile based on all intersections between eCognition Segments and Edited Field Borders Shapefile and populate with attribute table data from Edited Field Borders Shapefile

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
 
# 0.1 Import necessary packages 
import arcpy, os

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects eCognition Segments
eCognition_segments = arcpy.GetParameterAsText(0)

# User selects Edited Field Borders Shapefile
edited_field_borders_shapefile = arcpy.GetParameterAsText(1)

# User selects eCognition Scale Parameter used
scale_parameter = arcpy.GetParameterAsText(2)

# User selects Shapefile Directory
covs_path = arcpy.GetParameterAsText(3)

#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

# 0.3 Check out Spatial Analyst Extension
arcpy.CheckOutExtension('Spatial')

#--------------------------------------------------------------------------

# 1. Create a new shapefile based on all intersections between eCognition Segments and Edited Field Borders Shapefile and populate with attribute table data from Edited Field Borders Shapefile

region_and_time = os.path.basename(edited_field_borders_shapefile).rsplit(sep = '_', maxsplit = 1)[0]

segments_shapefile= os.path.join(covs_path, region_and_time + '_segments_scale_' + scale_parameter + '.shp')

arcpy.Identity_analysis(in_features = eCognition_segments, identity_features = edited_field_borders_shapefile, out_feature_class = segments_shapefile, join_attributes = 'ALL', cluster_tolerance = '#', relationship = 'NO_RELATIONSHIPS')


