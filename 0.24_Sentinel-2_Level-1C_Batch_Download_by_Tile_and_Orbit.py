###############################################################################################
###############################################################################################

# Name:             0.24_Sentinel-2_Level-1C_Batch_Download_by_Tile_and_Orbit.py
# Author:           Kelly Meehan, USBR
# Created:          20200505
# Updated:          20200506
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will allow a user to batch download (post-March 3rd, 2017) 
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

# 0.1 Assign variables to tool parameters

# User specifies tileid to filter query results
orbit = '127'
orbit = arcpy.GetParameterAsText(0)

# User specifies tileid to filter query results
tile = '11SQS'
tile = arcpy.GetParameterAsText(1)

# User specifies folder where Sentinel imagery should be saved to 
output_directory = r'C:\Users\kmeehan\Documents\COVID-19_Telework\T2_2020_Fallow_Analysis\Data\To_Composite'
output_directory = arcpy.GetParameterAsText(2)

# User adds existing username for Copernicus Open Access Hub
user_name = arcpy.GetParameterAsText(3)

# User adds existing password for Copernicus Open Access Hub
user_password = arcpy.GetParameterAsText(4)

# User specifies query date range beginningin the form of YYYYMMDD
date_range_begin = '20200419'
date_range_begin = arcpy.GetParameterAsText(5)

# User specifies query date range ending in the form of YYYYMMDD
date_range_end= 'NOW'
date_range_end = arcpy.GetParameterAsText(6)

# User specifies query cloud range beginning percentage as an integer value between 0 and 100
cloud_range_begin = '0'
cloud_range_begin = arcpy.GetParameterAsText(7)

# User specifies query cloud range ending percentage as an integer value between 0 and 100
cloud_range_end = '100'
cloud_range_end = arcpy.GetParameterAsText(8)

# 0.3 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool 
arcpy.env.overwriteOuptut = True

# 0.4 Change working directory to output directory
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