###############################################################################################
###############################################################################################

# Name:             0.22_Sentinel-2_Level-1C_Batch_Download_by_Tile.py
# Author:           Kelly Meehan, USBR
# Created:          20200415
# Updated:          20200423
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will allow a user to batch download and compile (post-December 6th, 2016) 
#                   Sentinel-2 Level-1C products using three filters: 1) date range, 2) cloud cover range, and 3) tile id
 
# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           Tiles_Chosen_List: String-Multiple Values (Data Type) > Required (Type) > Direction (Input)
#                           Output_Directory: Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User_Name: String (Data Type) > Required (Type) > Direction (Input) 
#                           User_Password: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_Begin: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_Begin: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Bands: String-Multiple Values (Data Type) > Required (Type) > Direction (Input) > Value List of 01 through 12 (Filter)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicus Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Cull query results by keeping only one file per date with the smallest size
# 4. Download products
# 5. Unzip Sentinel-2 product Level-1C zipped downloaded files 
# 6. Composite user selected bands

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat, collections

# 0.1 Assign variables to tool parameters

# User specifies tileid to filter query results
tiles_chosen_list = arcpy.GetParameterAsText(0)

# Create list out of user selected tile ids
tiles_list = tiles_chosen_list.split(";")

# User specifies folder where Sentinel imagery should be saved to 
output_directory = arcpy.GetParameterAsText(1)

# User adds existing username for Copernicus Open Access Hub
user_name = arcpy.GetParameterAsText(2)

# User adds existing password for Copernicus Open Access Hub
user_password = arcpy.GetParameterAsText(3)

# User specifies query date range beginningin the form of YYYYMMDD
date_range_begin = arcpy.GetParameterAsText(4)

# User specifies query date range ending in the form of YYYYMMDD
date_range_end = arcpy.GetParameterAsText(5)

# User specifies query cloud range beginning percentage as an integer value between 0 and 100
cloud_range_begin = arcpy.GetParameterAsText(6)

# User specifies query cloud range ending percentage as an integer value between 0 and 100
cloud_range_end = arcpy.GetParameterAsText(7)

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

# 2. Run query and store resultant list of products as an ordered dictionary

# Create empty ordered dictionary
products = collections.OrderedDict()

# For each tile, run query and a
for i in tiles_list:
    arcpy.AddMessage('Searching for ' + str(i) + ' tiles matching query')
    pp = api.query(tileid = i, date = (date_range_begin, date_range_end), platformname = 'Sentinel-2', producttype = 'S2MSI1C', cloudcoverpercentage = (cloud_range_begin, cloud_range_end))
    products.update(pp)
    
# Print initial number of products returned from query 
arcpy.AddMessage('Initial number of products returned from query: ' + str(len(products)))

#----------------------------------------------------------------------------------------------

# 3. Cull query results by keeping only one file per date with the smallest size

# Convert to Pandas DataFrame
products_df = api.to_dataframe(products)

# Print initial query product filenames
arcpy.AddMessage('Initial query product filenames: ' + str(list(products_df.filename)))

# Sort products based on beginposition (beginning of acquisition) and then by size
products_df_sorted = products_df.sort_values(['beginposition', 'tileid', 'size'], ascending = [True, True, False])

# Keep first entry (thereby selecting the smallest) in cases where there are multiple images per day (i.e. multiple tiles contain whole area of interest) 
products_df_unduplicated = products_df_sorted.drop_duplicates(['beginposition', 'tileid'], keep = 'first')

# Print number of products culled 
arcpy.AddMessage('Number of products culled: ' + str(len(products_df) - len(products_df_unduplicated.index)))

# Print final number of products 
arcpy.AddMessage('Final number of products to be downloaded: ' + str(len(products_df_unduplicated.index)))

# Print final product filenames
arcpy.AddMessage('Filenames of final products to be downloaded: ' + str(list(products_df_unduplicated.filename)))

#----------------------------------------------------------------------------------------------

# 4. Download products

# Download all final products to output directory
api.download_all(products = products_df_unduplicated.index, directory_path = output_directory)

# Print message confirming downloads complete
arcpy.AddMessage('Final products were either downloaded or previously existed in output directory and are ready to be composited') 