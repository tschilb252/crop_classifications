
###############################################################################################
###############################################################################################

# Name:             0.30_Rank_Fields_by_Heterogeneity.py
# Author:           Kelly Meehan, USBR
# Created:          20200629
# Updated:          20200701 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro and Spatial Analyst Extension

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description       This tool assigns all fields a rank heterogeneity value, where 1 is the field with the greatest heterogeneity.

#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Field Borders Feature Class     Feature Class (Data Type) > Required (Type) > Input (Direction) 
#                           Project Geodatabase             Workspace (Data Type) > Required (Type) > Input (Direction) 
#                           Raw Raster                      Raster Dataset (Data Type) > Required (Type) > Input (Direction) 
#                           Blue Band                       String (Data Type) > Required (Type) > Input (Direction) 
#                           Green Band                      String (Data Type) > Required (Type) > Input (Direction) 
#                           Red Band                        String (Data Type) > Required (Type) > Input (Direction) 
#                           NIR Band                        String (Data Type) > Required (Type) > Input (Direction) 

#                       Validation tab:

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
        
#         # Set default value for argument passed to Project Geodatabase
#         if self.params[0].value:
#             if not self.params[1].altered:
#                 self.params[1].value = os.path.dirname(self.params[0].value.value)
        
#         # Generate a drop down value list of Layers within Raw Raster 
#         if self.params[2].value:
#             layer_list = []
#             desc = arcpy.Describe(self.params[2].value)
#             for child in desc.children:
#                 layer_list.append(child.name) 
#             self.params[3].filter.list = layer_list
#             self.params[4].filter.list = layer_list
#             self.params[5].filter.list = layer_list
#             self.params[6].filter.list = layer_list
            
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
# 1. For each field, calculate the standard deviation of each specified band 
# 2. Assign rank value to fields, where 1 is the field with greatest heterogeneity (excluding class 2, static fields)

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy, os

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects Field Borders Feature Class 
field_borders_feature_class = arcpy.GetParameterAsText(0)

# User selects Project Geodatabase
project_geodatabase = arcpy.GetParameterAsText(1)

# User selects predominant raster used in classification
raw_raster = arcpy.GetParameterAsText(2)

# User selects layer corresponding to blue layer
blue_layer = arcpy.GetParameterAsText(3)

# User selects layer corresponding to green layer
green_layer = arcpy.GetParameterAsText(4)

# User selects layer corresponding to red layer
red_layer = arcpy.GetParameterAsText(5)

# User selects layer corresponding to near infrared layer
nir_layer = arcpy.GetParameterAsText(6)

#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

#-----------------------------------------------------------------------------------------------

# 1. Calculate for each field the standard deviation for the blue, green, red, and nir bands 

def calculate_band_standard_deviation(feature_class, raster, blue, green, red, nir):
    
    # Create dictionary with key, value pair: names of bands, raster layer 
    
    names_list = ['blue', 'green', 'red', 'nir']    
    layer_list = [blue, green, red, nir]
    layer_dict = dict(zip(names_list, layer_list))
    
    # Iterate through dictionary and calculate for each field, the standard deviation for each band
    
    sd_fields_list = []
    for key, value in layer_dict.items():
        layer = os.path.join(raster, value)
        arcpy.AddMessage('Layer: ' + layer)
        sd_table_name = key + '_sd_table'
        sd_table = os.path.join(project_geodatabase, sd_table_name)
        arcpy.sa.ZonalStatisticsAsTable(in_zone_data = feature_class, zone_field = 'FIELD_ID', in_value_raster = layer, out_table = sd_table, statistics_type = 'STD')
        
        # Join standard deviation values to Field Borders Feature Class
        
        arcpy.JoinField_management(in_data = feature_class, in_field = 'FIELD_ID', join_table = sd_table, join_field = 'FIELD_ID', fields = 'STD')
        new_sd_field = key + '_sd'
        sd_fields_list.append(new_sd_field)
        if arcpy.ListFields(dataset = field_borders_feature_class, wild_card = new_sd_field):
            arcpy.DeleteField_management(in_table = feature_class, drop_field = new_sd_field)
        arcpy.AlterField_management(in_table = feature_class, field = 'STD', new_field_name = new_sd_field, new_field_alias = new_sd_field)  
        arcpy.DeleteField_management(in_table = feature_class, drop_field = 'STD')

        
    # Generate field calculating sum of blue, green, red, and nir standard deviation values
    
    aggregate_sd_field = 'aggregate_sd'
    
    if not arcpy.ListFields(dataset = field_borders_feature_class, wild_card = aggregate_sd_field):
        arcpy.AddField_management(in_table = feature_class, field_name = aggregate_sd_field, field_type = 'FLOAT')
    
    sd_fields_list.append(aggregate_sd_field)
    
    with arcpy.da.UpdateCursor(feature_class, sd_fields_list) as cursor:
        for row in cursor:
            if row[0] is not None and row[1] is not None and row[2] is not None and row[3] is not None:        
                row[4] = row[0] + row[1] + row[2] + row[3]
                cursor.updateRow(row)

#-----------------------------------------------------------------------------------------------

# 2. Assign rank value to fields, where 1 is the field with greatest heterogeneity (excluding class 2, static fields)

def calculate_heterogeneity(features): # Adapted from: https://arcpy.wordpress.com/2013/08/02/ranking-field-values/

    # Add rank field if it does not already exist
    heterogeneity_rank_field = 'heterogeneity_rank'
    
    if not arcpy.ListFields(dataset = features, wild_card = heterogeneity_rank_field):
        arcpy.AddField_management(in_table = features, field_name = heterogeneity_rank_field, field_type = 'SHORT')

    # Assign rank value
          
    cursor_fields = ['aggregate_sd', heterogeneity_rank_field, 'CLASS']
    rank = 1
  
    with arcpy.da.UpdateCursor(in_table = features, field_names = cursor_fields, sql_clause = (None, 'ORDER BY aggregate_sd DESC')) as cursor:
        for row in cursor:
            if row[2] != 2:    
                if row[0] is not None:        
                    row[1] = rank
                    rank += 1    
                    cursor.updateRow(row)

#-----------------------------------------------------------------------------------------------

if __name__ == '__main__':
    
    calculate_band_standard_deviation(feature_class = field_borders_feature_class, raster = raw_raster, blue = blue_layer, green = green_layer, red = red_layer, nir = nir_layer)
    
    calculate_heterogeneity(features = field_borders_feature_class)
    
    
    
    
   