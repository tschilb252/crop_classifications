
###############################################################################################
###############################################################################################

# Name:             2.00_Prepare_Feature_Class_for_Accuracy_Assessment_Selection.py
# Author:           JM and modified by TW and KM, USBR
# Created:          
# Updated:          20200601 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool identifies fields that can be used as either training points or accuracy assessment points for the classification.

#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Field Borders Feature Class:    Feature Layer (Data Type) > Required (Type) > Input (Direction)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Add new attribute table field EXTRAFIELD
# 2. Populate a value of 1 for this attribute table field, EXTRAFIELD, for records meeting either one of the following two criteria:
    # a) CLASS == 0 AND CROP_PCT > 0 AND Crop_Type != 0
    # b) CLASS == 0 AND CROP_PCT == 0 AND Crop_Type == 1403
# 3. Add new attribute table fields aa and aa_domain
# 4. Populate the aa field with a value of 1 for records meeting either one of the following two criteria:
    # a) CLASS == 1 AND Crop_Type != 0
    # b) EXTRAFIELD == 1

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy

# 0.1 Read in tool parameters

# User selects Field Borders Feature Class 
field_borders_feature_class = arcpy.GetParameterAsText(0)

# 0.2 Set environment settings

# Set overwrite permissions to true in case user reruns tool (and redraws aoi)
arcpy.env.overwriteOuptut = True

#----------------------------------------------------------------------------------------------

# 1. Add three new fields: EXTRAFIELD, aa, and aa_domain

new_fields = ['EXTRAFIELD', 'aa', 'aa_domain']

existing_fields = [field.name for field in arcpy.ListFields(field_borders_feature_class)] 

for i in new_fields:
    if i in existing_fields:
        arcpy.DeleteField_management(in_table = field_borders_feature_class, drop_field = i)
    arcpy.AddField_management(in_table = field_borders_feature_class, field_name = i, field_type = 'SHORT')

#----------------------------------------------

# 2. Populate a value of 1 for this new field, ‘EXTRAFIELD’, for records meeting either one of the following two criteria:
    # a) CLASS == 0 AND CROP_PCT > 0 AND Crop_Type != 0 AND GROWTH_STA > 0
    # b) CLASS == 0 AND CROP_PCT == 0 AND Crop_Type == 14.03
    
fields = ['CLASS', 'CROP_PCT', 'EXTRAFIELD', 'Crop_Type', 'GROWTH_STA']

with arcpy.da.UpdateCursor(in_table = field_borders_feature_class, field_names = fields) as cursor:
    for row in cursor:
        # Note: int(0 if row[1] is None else row[1])) > 0 means: if CROP_PCT is <NULL> (None), return 0, otherwise return the value of CROP_PCT as an interger
        if (row[0] == 0 and int(0 if row[1] is None else row[1]) > 0 and int(0 if row[3] is None else row[3]) != 0 and int(0 if row[4] is None else row[4]) > 0) : 
            row[2] = 1
        
        elif (row[0] == 0 and (row[1] is None or row[1] == 0) and row[3] == 1403):
            row[2] = 1
        # Otherwise, assign EXTRAFIELD a value of 0
        else:
            row[2] = 0
        cursor.updateRow(row)

#----------------------------------------------

# 4. Populate the aa field with a value of 1 for records meeting either one of the following two criteria:
    # a) CLASS == 1 AND Crop_Type != 0 AND CROP_PCT != 0 AND GROWTH_STA != 0
    # b) CLASS == 1 AND Crop_Type == 1403
    # b) EXTRAFIELD == 1
    
field_list = ['CLASS', 'EXTRAFIELD', 'aa', 'Crop_Type', 'CROP_PCT', 'GROWTH_STA',]
with arcpy.da.UpdateCursor(in_table = field_borders_feature_class, field_names = field_list) as cursor:
    for row in cursor:
        # if CLASS == 1 and Crop_Type != 0 
        if (row[0] == 1 and int(0 if row[3] is None else row[3]) != 0 and row[4] is not None and int(0 if row[5] is None else row[5]) != 0):
            # set aa = 1
            row[2] = 1
        # if CLASS == 1 AND Crop_Type == 1403
        elif (row[0] == 1 and row[3] == 1403):
             # set aa = 1
            row[2] = 1
        # if EXTRAFIELD == 1, set aa = 1 (already checked for Crop_Type != 0 above)
        elif (row[1] == 1):
             # set aa = 1
            row[2] = 1
        cursor.updateRow(row)




