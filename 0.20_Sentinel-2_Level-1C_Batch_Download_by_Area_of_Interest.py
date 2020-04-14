###############################################################################################
###############################################################################################

# Name:             0.20_Sentinel-2_Level-1C_Batch_Download_by_Area_of_Interest.py
# Author:           Kelly Meehan, USBR
# Created:          20200406
# Updated:          20200413 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package download

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool will allow a user to batch download Sentinel-2 Level-1C products using three filters: 
#                   1) date range, 2) cloud cover range, and 3) tiles that completely contain a polygon drawn by the user in an ArcGIS Pro map. 

# Tool setup:       The script tool's properties can be set as follows (Label does not matter, only the order): 
#                       Parameters tab:    
#                           AOI_Polygon: Feature Set (Data Type) > Required (Type) > Direction (Input) 
#                           Output_Directory: Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User_Name: String (Data Type) > Required (Type) > Direction (Input) 
#                           User_Password: String (Data Type) > Required (Type) > Direction (Input)
#                           Date_Range_Begin: String (Data Type) > Required (Type) > Direction (Input)
#                           Date_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_Begin: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_End: String (Data Type) > Required (Type) > Direction (Input)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicul Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Cull query results by keeping only one file per date with the smallest size
# 4. Download culled products to output directory

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat

# 0.1 Assign variables to tool parameters

# User creates new temporary feature class (feature set) designating full area of interest
aoi_polygon = arcpy.GetParameterAsText(0)

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

# 0.2 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool (and redraws aoi)
arcpy.env.overwriteOuptut = True

# 0.3 Assign variable to the default geodatabase of the map the user is running the tool from
aprx = arcpy.mp.ArcGISProject('CURRENT')
default_geodatabase = aprx.defaultGeodatabase

#----------------------------------------------------------------------------------------------

# 1. Authenticate credentials to Copernicus Open Access Hub 
api = sentinelsat.SentinelAPI(user = user_name, password = user_password)

#----------------------------------------------------------------------------------------------

# 2. Run query and store resultant list of products as an ordered dictionary

# Convert feature set to GeoJSON format, project to WGS 1984 coordinate system, and save as aoi.geojson within output directory
arcpy.FeaturesToJSON_conversion(in_features = aoi_polygon, out_json_file = os.path.join(output_directory, 'aoi'), outputToWGS84 = 'WGS84', geoJSON = True)

# Read GeoJSON file into a GeoJSON object and then convert to Well-Known Text
footprint = sentinelsat.geojson_to_wkt(sentinelsat.read_geojson(os.path.join(output_directory, 'aoi.geojson')))

# Search SciHub for Sentinel-2, Level 1C products for which the AOI is completely inside the footprint of the image
products = api.query(area = footprint, area_relation = 'Contains', date = (date_range_begin, date_range_end), platformname = 'Sentinel-2', producttype = 'S2MSI1C', cloudcoverpercentage = (cloud_range_begin, cloud_range_end))

# Print initial number of products returned from query 
print(len(products))
arcpy.AddMessage('Initial number of products returned from query: ' + str(len(products)))

#----------------------------------------------------------------------------------------------

# 3. Cull query results by keeping only one file per date with the smallest size

# Convert to Pandas DataFrame
products_df = api.to_dataframe(products)
print(products_df)

# View pandas data frame column headers
print(list(products_df.columns.values))

# Sort products based on beginposition (beginning of acquisition) and then by size
products_df_sorted = products_df.sort_values(['beginposition', 'size'], ascending=[True, True])
print(products_df_sorted)

# Keep first entry (thereby selecting the smallest) in cases where there are multiple images per day (i.e. multiple tiles contain whole area of interest) 
products_df_unduplicated = products_df_sorted.drop_duplicates(['beginposition'], keep = 'first')
print(products_df_unduplicated[['filename']])

# Print culled number of products 
print(len(products_df_unduplicated.index))
arcpy.AddMessage('Final number of products to be downloaded: ' + str(len(products_df_unduplicated.index)))

#----------------------------------------------------------------------------------------------

# 4. Download culled products to output directory
api.download_all(products = products_df_unduplicated.index, directory_path = output_directory)

# Print message confirming downloads complete
arcpy.AddMessage('Final products were either downloaded or previously existed in output directory') 