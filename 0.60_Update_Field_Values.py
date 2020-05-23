
###############################################################################################
###############################################################################################

# Name:             0.60_Update_Field_Values.py
# Author:           Kelly Meehan, USBR
# Created:          20181214
# Updated:          20200522 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool allows a user to iterate through two sets of feature classes, each with differing unique IDs (i.e. earlier and later FIELD_IDs) and update select attribute table fields for one identified feature.                
                    
#----------------------------------------------------------------------------------------------
 
# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Earlier Feature Classes:    Feature Layer-Multiple Values (Data Type) > Optional (Type) > Input (Direction)
#                           Earlier FIELD_ID:           Long (Data Type) > Required (Type) > Input (Direction)
#                           Later Feature Classes:      Feature Layer-Multiple Values (Data Type) > Optional (Type) > Input (Direction)
#                           Later FIELD_ID:             Long (Data Type) > Required (Type) > Input (Direction)
#                           Class:                      Long (Data Type) > Required (Type) > Input (Direction)
#                           Crop Type:                  Double (Data Type) > Required (Type) > Input (Direction)
#                           GIS Comment:                String (Data Type) > Required (Type) > Input (Direction)
#                           Study Area:                 Long (Data Type) > Required (Type) > Input (Direction)
#                           Region:                     String (Data Type) > Required (Type) > Input (Direction)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Test for duplicate FIELD_ID
# 2. For each feature class, update the attribute table fields of CLASS, CROP_TYPE, and GIS_COMMENTS, and STUDY_AREA for any features with matching FIELD_ID and REGION 

###############################################################################################
###############################################################################################

# 0. Set-up

# 0.0 Install necessary packages
import arcpy

# 0.1 Read in tool parameters

# User selects one or more Earlier Feature Classes that share a consistent FIELD_ID labeling system
earlier_feature_classes = arcpy.GetParameterAsText(0)

# User selects Earlier FIELD ID corresponding to feature to update
earlier_field_id = arcpy.GetParameterAsText(1)

# User selects one or more Later Feature Classes that share a consistent FIELD_ID labeling system
later_feature_classes = arcpy.GetParameterAsText(2)

# User selects Later FIELD ID corresponding to feature to update
later_field_id = arcpy.GetParameterAsText(3)

# User inputs value that feature's CLASS value will be updated to
class_value = arcpy.GetParameterAsText(4) 

# User inputs value that feature's Crop_Type value will be update to
crop_type = arcpy.GetParameterAsText(5)

# User inputs value that feature's STUDI_AREA value will be updated to
study_area = arcpy.GetParameterAsText(6)

# User provides uniform comment string to denote classification period initiating new border delineation
gis_comment = arcpy.GetParameterAsText(7)

# User selects region that feature belongs to (so as to avoid overwritting feature with same ID in another region)
region =  arcpy.GetParameterAsText(8)

#----------------------------------------------------------------------------------------------

# 1. Test for duplicate FIELD_ID
        
def check_duplicate_id():
    for c in earlier_feature_classes.split(';'): 
        with arcpy.da.UpdateCursor(in_table = c, field_names = ['FIELD_ID']) as cursor:
            field_id_values = [r[0] for r in cursor]
            duplicates = set([x for x in field_id_values if field_id_values.count(x) > 1])
            arcpy.AddMessage('Duplicate values for ' + str(c) + ' found were: ' + str(duplicates))

# 2. For each feature class, update the attribute table fields of CLASS, CROP_TYPE, and GIS_COMMENTS, and STUDY_AREA for any features with matching FIELD_ID and REGION 

def update_feature():
    # Create list of uniform attribute table field names of which the like will be searched for 
    desired_field_names = ['FIELD_ID', 'CLASS', 'CROP_TYPE', 'STUDY_AREA', 'GIS_COMMENTS', 'REGION']
    
    # Iterate through all Earlier Feature Classes
    for i in earlier_feature_classes.split(";"): 
        # Clear selection of Feature Class
        arcpy.SelectLayerByAttribute_management(in_layer_or_view = i, selection_type = 'CLEAR_SELECTION')
        # Make list of fields in feature class
        existing_fields  = [field.name for field in arcpy.ListFields(dataset = i)]
        
        # Make empty list to which will be added existing field name that have a fuzzy match with a desired field name
        field_names_list = []
        
        # Create a list of existing fields that have a fuzzy match with a desired field name
        for e in existing_fields:
            for d in desired_field_names:
                e_insensitive = e.casefold()
                d_insensitive = d.casefold()
                if e_insensitive[0:6] == d_insensitive[0:6]:
                    field_names_list.append(e)
    
        # Create a sorted list so that fields can always be referenced in the same order             
        field_names_list.sort() # Order should always be (case-insensitive): class, crop_type, field_id, gis_comments, region, study_area
    
        with arcpy.da.UpdateCursor(in_table = i, field_names = field_names_list) as cursor:
            for row in cursor:
                if row[2] == int(earlier_field_id) and row[4] == region: # NOTE: conditional test will not work without int(); region used here because there's duplicated field_ids among different regions
                    row[0] = class_value
                    row[1] = crop_type
                    row[5] = study_area
                    if row[3] is not None or not str(row[1]).strip():
                        row[3] = gis_comment
                    else:
                        row[3] = str(row[3]) + '; ' + gis_comment
                    cursor.updateRow(row)
        arcpy.AddMessage('Updated feature with FIELD_ID: ' + str(earlier_field_id) + ' within ' + str(i))                    


#----------------------------------------------

if __name__ == '__main__':
    check_duplicate_id()
    update_feature()
    