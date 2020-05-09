###############################################################################################
###############################################################################################

# Name:             0.24_Sentinel-2_Level-1C_Batch_Download_by_Tile_and_Orbit.py
# Author:           Kelly Meehan, USBR
# Created:          20200505
# Updated:          20200508
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will allow a user to batch download (post-20170331) 
#                   Sentinel-2 Level-1C products using four filters: 1) date range, 2) cloud cover range, 3) relative orbit number and 4) tile id
#                   Download Sentinel-2 Relative Orbits KML file at https://sentinel.esa.int/web/sentinel/missions/sentinel-2/satellite-description/orbit
#                   Download Sentinel-2 Tiles KML at https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products

# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           Orbit: String (Data Type) > Required (Type) > Direction (Input)    
#                           Tile: String (Data Type) > Required (Type) > Direction (Input)
#                           Output_Directory: Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User_Name: String (Data Type) > Required (Type) > Direction (Input) 
#                           User_Password: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_Begin: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_Begin: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_End: String (Data Type) > Required (Type) > Direction (Input)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicus Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Generate csv of product metadata
# 4. Download products

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat

# 0.1 Assign variables to tool parameters and run checks on values passed

# User specifies tileid to filter query results
orbit = arcpy.GetParameterAsText(0)

# Raise error if user passes something other than a three character string of numbers for orbit parameter     
try:
    if len(orbit) != 3 or not orbit.isdigit():
        raise Exception
except Exception:
    print('Orbit value passed must be a three digit integer. Please do not use R as a prefix.')    
  
# User specifies tileid to filter query results
tile = arcpy.GetParameterAsText(1)

# Raise error if user passes something other than a five character string consisting of two numbers followed by three letters for tile parameter     
try:
    if len(tile) != 5 or not tile[:2].isdigit() or not tile[2:].isalpha():
        raise Exception
except Exception:
    print('Tile value should be two numbers followed by three letters. Please do not use T as a prefix.')   
    
# User specifies folder where Sentinel imagery should be saved to 
output_directory = arcpy.GetParameterAsText(2)

# User adds existing username for Copernicus Open Access Hub
user_name = arcpy.GetParameterAsText(3)

# User adds existing password for Copernicus Open Access Hub
user_password = arcpy.GetParameterAsText(4)

# User specifies query date range beginningin the form of YYYYMMDD
date_range_begin = arcpy.GetParameterAsText(5)

# Raise error if user passes something other than an eight character string of numbers for date_range_begin     
try:
    if len(date_range_begin) != 8 or not date_range_begin.isdigit():
        raise Exception
except Exception:
    print('Date_Range_Begin should be eight digit integer in the form of YYYYMMDD.')   
    
# User specifies query date range ending in the form of YYYYMMDD
date_range_end = arcpy.GetParameterAsText(6)

# Raise error if user passes something other than an eight character string of numbers for date_range_end     
try:
    if date_range_end != 'NOW' or (len(date_range_end) != 8 and date_range_end.isdigit()):
        raise Exception
except Exception:
    print('Date_Range_End should either be NOW or an eight digit integer in the form of YYYYMMDD.')   

# Raise error if user passes selects a begin date after an end date     
try:
    if int(date_range_begin) > int(date_range_end):
        raise Exception
except Exception:
    print('Date_Range_Begin must be before Date_Range_End.')   

# Raise error if user tries to search for tiles befor 20170331     
try:
    if int(date_range_begin) < 20170401:
        raise Exception
except Exception:
    print('Date search must be post-20200331.') 

# User specifies query cloud range beginning percentage as an integer value between 0 and 100
cloud_range_begin = arcpy.GetParameterAsText(7)

# Raise error if user passes something other than an integer value between 0 and 100 for cloud_range_begin     
try:
    if int(cloud_range_begin) < 0 or not cloud_range_begin.isdigit():
        raise Exception
except Exception:
    print('Cloud_Range_Begin should be a one or two digit integer.')   

# User specifies query cloud range ending percentage as an integer value between 0 and 100
cloud_range_end = arcpy.GetParameterAsText(8)

# Raise error if user passes something other than a eight character string of numbers for date_range_end     
try:
    if len(cloud_range_end) != 2 or not cloud_range_end.isdigit():
        raise Exception
except Exception:
        print('Cloud_Range_End should be a one or two digit integer.')   

# 0.2 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool 
arcpy.env.overwriteOuptut = True

# 0.3 Change working directory to output directory
os.chdir(output_directory)

#----------------------------------------------------------------------------------------------

# 1. Authenticate credentials to Copernicus Open Access Hub 
api = sentinelsat.SentinelAPI(user = user_name, password = user_password)

#----------------------------------------------------------------------------------------------

# 2. Run query 

arcpy.AddMessage('Searching for Sentinel-2 Level-1C products matching query')

products = api.query(tileid = tile, relativeorbitnumber = orbit, date = (date_range_begin, date_range_end), platformname = 'Sentinel-2', producttype = 'S2MSI1C', cloudcoverpercentage = (cloud_range_begin, cloud_range_end))

# Print number of products returned from query 
arcpy.AddMessage('Number of products returned from query: ' + str(len(products)))

#----------------------------------------------------------------------------------------------

# 3. Generate csv of product metadata

# Convert to Pandas DataFrame
products_df = api.to_dataframe(products)

# Print initial query product filenames
arcpy.AddMessage('Filenames of products returned from query: ' + str(list(products_df.filename)))

# Write Pandas DataFrame to csv in output directory
products_df.to_csv('Sentinel-2_Level-1C_Query_' + 'T' + tile + '_R' + orbit + '_' + date_range_begin + '-' + date_range_end + '_Clouds_' + cloud_range_begin + '-' + cloud_range_end + '_Metadata.csv')

#----------------------------------------------------------------------------------------------

# 4. Download products

# Download all final products to output directory
api.download_all(products = products_df.index, directory_path = output_directory)

# Print message confirming downloads complete
arcpy.AddMessage('Final products were either downloaded or previously existed in output directory and are ready to be composited') 