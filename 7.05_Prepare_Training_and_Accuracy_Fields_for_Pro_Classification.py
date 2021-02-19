
###############################################################################################
###############################################################################################

# Name:             7.05_Prepare_Training_and_Accuracy_Fields_for_Pro_Classification.py 
# Author:           Kelly Meehan, USBR
# Created:          20201216
# Updated:          20210216 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      Add two attribute table fields required for both Pro classification and accuracy assessment: classvalue (identical to existing crop_type) and classname (corresponding to crop_type numerical value).

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Create dictionary as lookup table for crop numerical value to crop type name
# 2. Add necessary attribute table fields, classvalue and classname to both Training Fields Shapefile and Accuracy Fields Shapefile

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages
import arcpy

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects Training Fields Shapefile
training_fields = arcpy.GetParameterAsText(0)

# User selects Accuracy Fields Shapefile
accuracy_fields = arcpy.GetParameterAsText(1)

#----------------------------------------------------------------------------------------------

# 1. Create dictionary as lookup table for crop numerical value to crop type name

# Create list of all possible crop numbers
crop_code = [100, 200, 400, 401, 402, 403, 404, 405, 500, 501, 502, 503, 600, 601, 602, 603, 604, 605, 606, 700, 701, 702, 703, 704, 705, 706, 800, 801, 802, 803, 804, 806, 1000, 1100, 1103, 1104, 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209, 1300, 1301, 1302, 1303, 1304, 1305, 1306, 1400, 1402, 1403, 1600, 1601, 1602, 1603, 1604, 1800, 1801, 1802, 1803, 1804, 1805, 1806, 1807, 1808, 1809, 1900, 1901, 1902, 1903, 1904, 2000, 2001, 2100, 3400, 3401, 3402, 3403, 3404]

# Create list of all crop names in corresponding order to crop_code
crop_name = ['Alfalfa', 'Cotton', 'Small Grains', 'Oats', 'Rye', 'Barley', 'Millet', 'Wheat', 'Field Grain', 'Corn', 'Sorghum', 'Milo', 'Lettuce', 'Head Lettuce', 'Green Leaf Lettuce', 'Red Leaf Lettuce', 'Spinach', 'Other Lettuce', 'Chard', 'Melons', 'Watermelon', 'Honeydew', 'Cantaloupe', 'Squash', 'Strawberries', 'Cucumbers', 'Bermuda/Rye', 'Bermuda', 'Bermuda with Rye', 'Klein', 'Timothy', 'Fallowed Bermuda', 'Tomatoes', 'Sudan', 'Sesbania', 'Clover', 'Legume', 'Green Beans', 'Dry Beans', 'Garbonzo Beans', 'Peas', 'Peanuts', 'Peppers', 'Potatoes', 'Egglant', 'Okra', 'Crucifers', 'Broccoli', 'Cauliflower', 'Cabbage', 'Boy-choy', 'Mustard', 'Kale', 'Fallow', 'Fallow', 'Fallow', 'Oil Crops', 'Safflower', 'Canola', 'Sunflower', 'Sesame', 'Small Vegetables', 'Carrots', 'Cilantro', 'Celery', 'Garlic', 'Onions', 'Scallions', 'Parsley', 'Radishes', 'Commercial Flowers', 'Root Vegetables', 'Beets', 'Parsnip', 'Turnip and Rutabaga', 'Chard', 'Perennial Vegetables', 'Artichokes', 'Sugar Beets', 'Miscellaneous Herbs', 'Anise', 'Mint', 'Basil', 'Other Herb']

# Create dictionary with key: value pair as crop_code: crop_name
crop_dictionary = dict(zip(crop_code, crop_name))

#----------------------------------------------------------------------------------------------

# 2. Add necessary attribute table fields, classvalue and classname to both Training Fields Shapefile and Accuracy Fields Shapefile

# Create function to add attribute table fields classvalue and classname, and setting their values equal to crop_type, and the corresponding crop_name in crop_dictionary
def add_classvalue_classname(feature_class_updating):

    # Add two new attribute table fields: classvalue and classsname
      
    if not arcpy.ListFields(dataset = feature_class_updating, wild_card = 'classvalue'):
        arcpy.AddField_management(in_table = feature_class_updating, field_name = 'classvalue', field_type = 'LONG')
    
    if not arcpy.ListFields(dataset = feature_class_updating, wild_card = 'classname'):
        arcpy.AddField_management(in_table = feature_class_updating, field_name = 'classname', field_type = 'TEXT')
    
    # Copy attribute table field, Crop_Type values to new column classname
    arcpy.CalculateField_management(in_table = feature_class_updating, field = 'classvalue', expression = '!crop_type!', expression_type = 'PYTHON3')
    
    # Populate classname attribute table field values using key: value in dictionary
    with arcpy.da.UpdateCursor(feature_class_updating, ['classvalue', 'classname']) as cursor:
        for row in cursor:
            x = row[0]
            row[1] = crop_dictionary[x]          
            cursor.updateRow(row)

# Run function for Training Fields Shapefile
add_classvalue_classname(feature_class_updating = training_fields)

# Run function for Accuracy Assessment Shapefile
add_classvalue_classname(feature_class_updating = accuracy_fields)

#----------------------------------------------------------------------------------------------

## TTDL

