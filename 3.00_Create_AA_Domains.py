
###############################################################################################
###############################################################################################

# Name:             3.00_Create_Accuracy_Assessment_Stratified_Domains.py
# Author:           Kelly Meehan, USBR; adapted from model written by Jeff Milliken and modified by Troy Wirth
# Created:          20180515
# Updated:          20200609 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro and Spatial Analyst Extension

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This script generates a value in the aa_domain field when aa value = 1 (class 1 ground truth fields + extra fields)
#                   There are 136 domain values (1-139, excluding 122-124, Asparagus)
#                   Crop code groups are usually broken into three domains based on percent cover: <20, >= 20 and <= 60, and > 60
#                   The exception to this is Small Grains, 4.* which are broken up: non-senescent < 20, non-senescent > 20, and senescent

#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#                      Parameters tab:    
#                           Field Borders Feature Class: Feature Layer (Data Type) > Required (Type) > Direction (Input) 

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Generate a value in the aa_domain field when aa value = 1 (which includes CLASS = 1 (ground truth fields) and EXTRAFIELD = 1 (extra fields))

###############################################################################################
###############################################################################################

# 0. Set-up

# 0.0 Install necessary packages
import arcpy, sys

# 0.1 Read in tool parameters

# User selects Field Borders Feature Class
field_borders_feature_class = arcpy.GetParameterAsText(0) 

# 0.2 Set environment settings
arcpy.env.overwriteOutput = True

#-----------------------------------------------------------------------------------------------

# 1. Generate a value in the aa_domain field when aa value = 1 (which includes CLASS = 1 (ground truth fields) and EXTRAFIELD = 1 (extra fields))

def assign_aa_domain():
    with arcpy.da.UpdateCursor(in_table = field_borders_feature_class, field_names = ['Crop_Type', 'CROP_PCT', 'aa', 'GROWTH_STA', 'aa_domain']) as cursor:
        for row in cursor:
            if row[2] == 1:
              # Alfalfa ------------------------------------------------------------
              if (row[0] == 100 and row[1] < 20 ):
                  row[4] = 1    
              elif (row[0] == 100 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 2
              elif (row[0] == 100 and row[1] > 60 ):
                  row[4] = 3
              # Cotton ------------------------------------------------------------
              elif (row[0] == 200 and row[1] < 20 ):
                  row[4] = 4
              elif (row[0] == 200 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 5
              elif (row[0] == 200 and row[1] > 60 ):
                  row[4] = 6
              # Small Grains ------------------------------------------------------------
              elif (row[0] >= 400 and row[0] <500 and row[1] < 20  and row[3] != 5):
                  row[4] = 7
              elif (row[0] >= 400 and row[0] <500 and row[1] >= 20  and row[3] != 5):
                  row[4] = 8
              elif (row[0] >= 400 and row[0] <500  and row[3] == 5):
                  row[4] = 9
              # Field Grains ------------------------------------------------------------
              elif (row[0] >= 500 and row[0] <600 and row[1] < 20 ):
                  row[4] = 10
              elif (row[0] >= 500 and row[0] <600 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 11
              elif (row[0] >= 500 and row[0] <600 and row[1] > 60 ):
                  row[4] = 12     
              # Lettuce (General) and Head Lettuce ------------------------------------------------------------
              elif (row[0] >= 600 and row[0] < 602 and row[1] < 20 ):
                  row[4] = 13
              elif (row[0] >= 600 and row[0] < 602 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 14
              elif (row[0] >= 600 and row[0] < 602 and row[1] > 60 ):
                  row[4] = 15
              # Leaf Lettuce (Green and Red) and Other Lettuce ------------------------------------------------------------
              elif (row[0] == 602 or row[0] == 603 or row[0] == 605 and row[1] < 20 ):
                  row[4] = 16
              elif (row[0] == 602 or row[0] == 603 or row[0] == 605 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 17
              elif (row[0] == 602 or row[0] == 603 or row[0] == 605 and row[1] > 60 ):
                  row[4] = 18
              # Spinach ------------------------------------------------------------
              elif (row[0] == 604 and row[1] < 20 ):
                  row[4] = 19
              elif (row[0] == 604 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 20
              elif (row[0] == 604 and row[1] > 60 ):
                  row[4] = 21
              # Mellons (General) and Cucumbers------------------------------------------------------------
              elif (row[0] == 700 or row[0] == 706 and row[1] < 20 ):
                  row[4] = 22
              elif (row[0] == 700 or row[0] == 706 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 23
              elif (row[0] == 700 or row[0] == 706 and row[1] > 60 ):
                  row[4] = 24
              # Watermellon, Honeydew, and Cantaloupe------------------------------------------------------------
              elif (row[0] == 701 or row[0] == 702 or row[0] == 7.03 and row[1] < 20 ):
                  row[4] = 25
              elif (row[0] == 701 or row[0] == 702 or row[0] == 7.03 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 26
              elif (row[0] == 701 or row[0] == 702 or row[0] == 7.03 and row[1] > 60 ):
                  row[4] = 27
              # Squash ------------------------------------------------------------
              elif (row[0] == 704 and row[1] < 20 ):
                  row[4] = 28
              elif (row[0] == 704 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 29
              elif (row[0] == 704 and row[1] > 60 ):
                  row[4] = 30
              # Strawberries ------------------------------------------------------------
              elif (row[0] == 705 and row[1] < 20 ):
                  row[4] = 31
              elif (row[0] == 705 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 32
              elif (row[0] == 705 and row[1] > 60 ):
                  row[4] = 33
              # Tomatoes ------------------------------------------------------------
              elif (row[0] == 1000 and row[1] < 20 ):
                  row[4] = 34
              elif (row[0] == 1000 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 35
              elif (row[0] == 1000 and row[1] > 60 ):
                  row[4] = 36
              # Sudan ------------------------------------------------------------
              elif (row[0] == 1100 and row[1] < 20 ):
                  row[4] = 37
              elif (row[0] == 1100 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 38
              elif (row[0] == 1100 and row[1] > 60 ):
                  row[4] = 39
              # Sesbania ------------------------------------------------------------
              elif (row[0] == 1101 and row[1] < 20 ):
                  row[4] = 40
              elif (row[0] == 1101 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 41
              elif (row[0] == 1101 and row[1] > 60 ):
                  row[4] = 42
              # Clover ------------------------------------------------------------
              elif (row[0] == 1102 and row[1] < 20 ):
                  row[4] = 43
              elif (row[0] == 1102 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 43
              elif (row[0] == 1102 and row[1] > 60 ):
                  row[4] = 45
              # Legumes (General) ------------------------------------------------------------
              elif (row[0] == 1200 and row[1] < 20 ):
                  row[4] = 46
              elif (row[0] == 1200 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 47
              elif (row[0] == 1200 and row[1] > 60 ):
                  row[4] = 48        
              # Beans (Green, Dry, and Garbonzo) ------------------------------------------------------------
              elif (row[0] == 1201 or row[0] == 1202 or row[0] == 1203 and row[1] < 20 ):
                  row[4] = 49
              elif (row[0] == 1201 or row[0] == 1202 or row[0] == 1203 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 50
              elif (row[0] == 1201 or row[0] == 1202 or row[0] == 1203 and row[1] > 60 ):
                  row[4] = 51
              # Peas ------------------------------------------------------------
              elif (row[0] == 1204 and row[1] < 20 ):
                  row[4] = 52
              elif (row[0] == 1204 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 53
              elif (row[0] == 1204 and row[1] > 60 ):
                  row[4] = 54
              # Peanuts ------------------------------------------------------------
              elif (row[0] == 1205 and row[1] < 20 ):
                  row[4] = 55
              elif (row[0] == 1205 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 56
              elif (row[0] == 1205 and row[1] > 60 ):
                  row[4] = 57
              # Peppers ------------------------------------------------------------
              elif (row[0] == 1206 and row[1] < 20 ):
                  row[4] = 58
              elif (row[0] == 1206 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 59
              elif (row[0] == 1206 and row[1] > 60 ):
                  row[4] = 60
              # Potatoes ------------------------------------------------------------
              elif (row[0] == 1207 and row[1] < 20 ):
                  row[4] = 61
              elif (row[0] == 1207 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 62
              elif (row[0] == 1207 and row[1] > 60 ):
                  row[4] = 63
              # Eggplant ------------------------------------------------------------
              elif (row[0] == 1208 and row[1] < 20 ):
                  row[4] = 64
              elif (row[0] == 1208 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 65
              elif (row[0] == 1208 and row[1] > 60 ):
                  row[4] = 66
              # Okra ------------------------------------------------------------
              elif (row[0] == 1209 and row[1] < 20 ):
                  row[4] = 67
              elif (row[0] == 1209 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 68
              elif (row[0] == 1209 and row[1] > 60 ):
                  row[4] = 69
              # Crucifers (General) ------------------------------------------------------------
              elif (row[0] == 1300 and row[1] < 20 ):
                  row[4] = 70
              elif (row[0] == 1300 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 71
              elif (row[0] == 1300 and row[1] > 60 ):
                  row[4] = 72        
              # Broccoli, Cauliflower, and Cabbage ------------------------------------------------------------
              elif (row[0] == 1301 or row[0] == 1302 or row[0] == 1303 and row[1] < 20 ):
                  row[4] = 73
              elif (row[0] == 1301 or row[0] == 1302 or row[0] == 1303 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 74
              elif (row[0] == 1301 or row[0] == 1302 or row[0] == 1303 and row[1] > 60 ):
                  row[4] = 75
              # Bok-choy ------------------------------------------------------------
              elif (row[0] == 1304 and row[1] < 20 ):
                  row[4] = 76
              elif (row[0] == 1304 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 77
              elif (row[0] == 1304 and row[1] > 60 ):
                  row[4] = 78  
              # Mustard ------------------------------------------------------------
              elif (row[0] == 1305 and row[1] < 20 ):
                  row[4] = 79
              elif (row[0] == 1305 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 80
              elif (row[0] == 1305 and row[1] > 60 ):
                  row[4] = 81  
              # Kale ------------------------------------------------------------
              elif (row[0] == 1306 and row[1] < 20 ):
                  row[4] = 82
              elif (row[0] == 1306 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 83
              elif (row[0] == 1306 and row[1] > 60 ):
                  row[4] = 84
      
              # Fallow ------------------------------------------------------------
              elif (row[0] == 1403 ):
                  row[4] = 85
              #elif (row[0] == 1406 ):
                  #row[4] = 137
              # Oil Crops ------------------------------------------------------------
              elif (row[0] >= 1600 and row[0] <1700 and row[1] < 20 ):
                  row[4] = 86
              elif (row[0] >= 1600 and row[0] <1700 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 87
              elif (row[0] >= 1600 and row[0] <1700 and row[1] > 60 ):
                  row[4] = 88        
              # Small Vegetables (General) ------------------------------------------------------------
              elif (row[0] == 1800 and row[1] < 20 ):
                  row[4] = 89
              elif (row[0] == 1800 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 90
              elif (row[0] == 1800 and row[1] > 60 ):
                  row[4] = 91 
              # Carrots ------------------------------------------------------------
              elif (row[0] == 1801 and row[1] < 20 ):
                  row[4] = 92
              elif (row[0] == 1801 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 93
              elif (row[0] == 1801 and row[1] > 60 ):
                  row[4] = 94 
              # Cilantro ------------------------------------------------------------
              elif (row[0] == 1802 and row[1] < 20 ):
                  row[4] = 95
              elif (row[0] == 1802 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 96
              elif (row[0] == 1802 and row[1] > 60 ):
                  row[4] = 97
              # Celery ------------------------------------------------------------
              elif (row[0] == 1803 and row[1] < 20 ):
                  row[4] = 98
              elif (row[0] == 1803 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 99
              elif (row[0] == 1803 and row[1] > 60 ):
                  row[4] = 100 
              # Garlic, Onions (Dry), and Onions ------------------------------------------------------------
              elif (row[0] == 1804 or row[0] == 1805 or row[0] == 1806 and row[1] < 20 ):
                  row[4] = 101
              elif (row[0] == 1804 or row[0] == 1805 or row[0] == 1806 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 102
              elif (row[0] == 1804 or row[0] == 1805 or row[0] == 1806 and row[1] > 60 ):
                  row[4] = 103
              # Parsley ------------------------------------------------------------
              elif (row[0] == 1807 and row[1] < 20 ):
                  row[4] = 104
              elif (row[0] == 1807 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 105
              elif (row[0] == 1807 and row[1] > 60 ):
                  row[4] = 106 
              # Radishes ------------------------------------------------------------
              elif (row[0] == 1808 and row[1] < 20 ):
                  row[4] = 107
              elif (row[0] == 1808 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 108
              elif (row[0] == 1808 and row[1] > 60 ):
                  row[4] = 109
              # Commercial Flowers ------------------------------------------------------------
              elif (row[0] == 1809 and row[1] < 20 ):
                  row[4] = 110
              elif (row[0] == 1809 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 111
              elif (row[0] == 1809 and row[1] > 60 ):
                  row[4] = 112
              # Root Vegetables (General) and Beets (Table) ------------------------------------------------------------
              elif (row[0] == 1900 or row[0] == 1901 and row[1] < 20 ):
                  row[4] = 113
              elif (row[0] == 1900 or row[0] == 1901 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 114
              elif (row[0] == 1900 or row[0] == 1901 and row[1] > 60 ):
                  row[4] = 115
              # Parsnip ------------------------------------------------------------
              elif (row[0] == 1902 and row[1] < 20 ):
                  row[4] = 116
              elif (row[0] == 1902 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 117
              elif (row[0] == 1902 and row[1] > 60 ):
                  row[4] = 118
              # Turnip and Rutabaga ------------------------------------------------------------
              elif (row[0] == 1903 and row[1] < 20 ):
                  row[4] = 119
              elif (row[0] == 1903 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 120
              elif (row[0] == 1903 and row[1] > 60 ):
                  row[4] = 121
              # Chard ------------------------------------------------------------
              elif (row[0] == 1904 and row[1] < 20 ):
                  row[4] = 122
              elif (row[0] == 1904 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 123
              elif (row[0] == 1904 and row[1] > 60 ):
                  row[4] = 124
              # Perennial Vegetables (General) ------------------------------------------------------------
              elif (row[0] == 2000 and row[1] < 20 ):
                  row[4] = 125
              elif (row[0] == 2000 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 126
              elif (row[0] == 2000 and row[1] > 60 ):
                  row[4] = 127
              # Artichokes ------------------------------------------------------------
              elif (row[0] == 2001 and row[1] < 20 ):
                  row[4] = 128
              elif (row[0] == 2001 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 129
              elif (row[0] == 2001 and row[1] > 60 ):
                  row[4] = 130        
              # Sugar Beets ------------------------------------------------------------
              elif (row[0] == 2100 and row[1] < 20 ):
                  row[4] = 131
              elif (row[0] == 2100 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 132
              elif (row[0] == 2100 and row[1] > 60 ):
                  row[4] = 133
              # Miscellaneous Herbs (General) and Basil ------------------------------------------------------------
              elif (row[0] == 3400 or row[0] == 3403 and row[1] < 20 ):
                  row[4] = 134
              elif (row[0] == 3400 or row[0] == 3403 or row[0] == 1806 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 135
              elif (row[0] == 3400 or row[0] == 3403 or row[0] == 1806 and row[1] > 60 ):
                  row[4] = 136
              # Anise ------------------------------------------------------------
              elif (row[0] == 3401 and row[1] < 20 ):
                  row[4] = 137
              elif (row[0] == 3401 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 138
              elif (row[0] == 3401 and row[1] > 60 ):
                  row[4] = 139
              # Mint ------------------------------------------------------------
              elif (row[0] == 3402 and row[1] < 20 ):
                  row[4] = 140
              elif (row[0] == 3402 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 141
              elif (row[0] == 3402 and row[1] > 60 ):
                  row[4] = 142
              # Other Herb ------------------------------------------------------------
              elif (row[0] == 3404 and row[1] < 20 ):
                  row[4] = 143
              elif (row[0] == 3404 and row[1] >= 20 and row[1] <= 60 ):
                  row[4] = 144
              elif (row[0] == 3404 and row[1] > 60 ):
                  row[4] = 145
    
            cursor.updateRow(row)

try:
    assign_aa_domain()
except RuntimeError:
    arcpy.AddError('Please close ' + field_borders_feature_class + 'and ru-run tool')
    sys.exit(0) 
else:
    arcpy.AddMessage('Assigned aa_domain value to all fields where aa value = 1')
