
###############################################################################################
###############################################################################################

# Name:             0.50_Reshape_Field_Borders.py
# Author:           Kelly Meehan, USBR
# Created:          20181212
# Updated:          20200521 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool allows a user to use selected features within a Reshape Fields feature class to update the geometries of two sets of feature classes, each with differing unique IDs (i.e. earlier and later FIELD_IDs). 
#                   User should have a Reshaped Fields feature class with the following attribute table fields complete: earlier_field_id, later_field_id, and REGION
                    
#----------------------------------------------------------------------------------------------
 
# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Reshaped Fields:            Feature Layer (Data Type) > Required (Type) > Input (Direction)
#                           Earlier Feature Classes:    Feature Layer-Multiple Values (Data Type) > Optional (Type) > Input (Direction)
#                           Later Feature Classes:      Feature Layer-Multiple Values (Data Type) > Optional (Type) > Input (Direction)
#                           Region:                     String (Data Type) > Required (Type) > Input (Direction) 
#                           GIS Comment:                String (Data Type) > Required (Type) > Input (Direction)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Iterate through features of Earlier Feature Classes and overwrite geometry with that of a selected feature in Reshaped Fields of matching FIELD_ID and REGION values; update ACRES; replace GIS_COMMENTS value
# 2. Iterate through features of Later Feature Classes and overwrite geometry with that of a selected feature in Reshaped Fields of matching FIELD_ID and REGION values; update ACRES; replace GIS_COMMENTS value
 
###############################################################################################
###############################################################################################

# 0. Set-up

# 0.0 Install necessary packages
import arcpy

# 0.1 Read in tool parameters

# User selects reshaped fields feature class
reshaped_fields = arcpy.GetParameterAsText(0)

# User selects one or more Earlier Feature Classes that share a consistent FIELD_ID labeling system
earlier_feature_classes = arcpy.GetParameterAsText(1)

# User selects one or more Later Feature Classes that share a consistent FIELD_ID labeling system
later_feature_classes = arcpy.GetParameterAsText(2)

# User selects region that feature belongs to (so as to avoid overwritting feature with same ID in another region)
region =  arcpy.GetParameterAsText(3)

# User provides uniform comment string to denote classification period initiating new border delineation
gis_comment = arcpy.GetParameterAsText(4)

#----------------------------------------------------------------------------------------------

# 1. Iterate through features of Earlier Feature Classes and overwrite geometry with that of a selected feature in Reshaped Fields of matching FIELD_ID and REGION values; update ACRES; replace GIS_COMMENTS value

def update_earlier_feature_classes():
    
    # Create list of strings out of semicolon delineated string
    earlier_feature_classes_list = earlier_feature_classes.split(';')     
    
    # Create a dictionary from attribute table of Reshaped Fields feature class (key: value is earlier_field_id: SHAPE@) 

    # Create empty dictionary
    earlier_id_dictionary = {}
    
    # Create Update Cursor with fields: earlier_field_id and SHAPE@
    with arcpy.da.UpdateCursor(reshaped_fields, ['earlier_field_id', 'SHAPE@']) as eCursor:
        for row in eCursor:
            # Populate empty dictionary with key: value pairs from the two attribute table fields (earlier_field_id: SHAPE)
            earlier_id_dictionary[row[0]] = row[1]
    
    # Iterate through each feature and if FIELD_ID matches a key value (earlier_field_id), replace @SHAPE with that of the dictionary value, and update ACRES
    
    # Check whether any Earlier Feature Classes were selected by user 
    if earlier_feature_classes:
        for i in earlier_feature_classes_list:  
            # Clear selection of Earlier Feature Class
            arcpy.SelectLayerByAttribute_management(in_layer_or_view = i, selection_type = 'CLEAR_SELECTION')
            # Create cursor with which to iterate through each feature
            with arcpy.da.UpdateCursor(i, ['FIELD_ID', 'SHAPE@', 'REGION', 'GIS_COMMENTS']) as cursor: 
                for row in cursor:
                    # Set variable, earlier_id, to current record's FIELD_ID value
                    earlier_id = row[0]
                    # If FIELD_ID matches that of earlier_field_id and REGION matches, update Shape and GIS_COMMENTS attribute table fields
                    if earlier_id in earlier_id_dictionary and row[2] == region: 
                        row[1] = earlier_id_dictionary[earlier_id]
                        row[3] = gis_comment
                        cursor.updateRow(row)
                        arcpy.AddMessage('Updated shape in earlier feature class: ' + str(i) + ' for FIELD_ID: ' + str(earlier_id))
            
            # Update ACRES in attribute table for Earlier Feature Class
            arcpy.CalculateField_management(in_table = i, field = 'ACRES', expression = '!shape.area@ACRES!', expression_type = 'PYTHON3')
            arcpy.AddMessage('Updated ACRES in Earlier Feature Class: ' + str(i))
    else:
        arcpy.AddMessage('No Earlier Feature Classes inputted.')
        
#----------------------------------------------------------------------------------------------

# 2. Iterate through features of later feature classes and overwrite geometry with that of a selected feature in Reshaped Fields of matching FIELD_ID values

def update_later_feature_classes():
    
    # Create list of strings out of semicolon delineated string
    later_feature_classes_list = later_feature_classes.split(';')
    
    # Create a dictionary from attribute table of Reshaped Fields feature class (key: value is later_field_id: SHAPE@) 
    
    # Create empty dictionary
    later_id_dictionary = {}

    # Create Update Cursor with fields: later_field_id and SHAPE@    
    with arcpy.da.UpdateCursor(reshaped_fields, ['later_field_id', 'SHAPE@']) as fCursor:
        for row in fCursor:
            # Populate empty dictionary with key: value pairs from the two attribute table fields (later_field_id: SHAPE)
            later_id_dictionary [row[0]] = row[1]

    # Iterate through each feature and if FIELD_ID matches a key value (later_field_id), replace @SHAPE with that of the dictionary value, and update ACRES
            
    # Check whether any Later Feature Classes were selected by user 
    if later_feature_classes:
        for k in later_feature_classes_list:
            # Clear selection of Later Feature Class
            arcpy.SelectLayerByAttribute_management(in_layer_or_view = k, selection_type = 'CLEAR_SELECTION')
            # Create cursor with which to iterate through each feature
            with arcpy.da.UpdateCursor(k, ['FIELD_ID', 'SHAPE@']) as cursor:
                for row in cursor:
                    later_id = row[0]
                    # If FIELD_ID matches that of earlier_field_id and REGION matches, update Shape and GIS_COMMENTS attribute table fields
                    if later_id in later_id_dictionary and row[2] == region:
                        row[1] = later_id_dictionary[later_id]
                        row[3] = gis_comment
                        cursor.updateRow(row)
                        arcpy.AddMessage('Updated shape in Later Feature Class: ' + str(k) + ' for FIELD_ID: ' + str(later_id))
        
            # Update ACRES in attribute table for Later Feature Class
            arcpy.CalculateField_management(in_table = k, field = 'ACRES', expression = '!shape.area@ACRES!', expression_type = 'PYTHON3')
            arcpy.AddMessage('Updated ACRES in Later Feature Class: ' + str(k))
    else:
        arcpy.AddMessage('No Later Feature Classes inputted.')
    
#----------------------------------------------

if __name__ == '__main__':
    update_earlier_feature_classes()
    update_later_feature_classes()


