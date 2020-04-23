###############################################################################################
###############################################################################################

# Name:             0.21_Sentinel-2_Level-1C_Batch_Download_by_Area_of_Interest.py
# Author:           Kelly Meehan, USBR
# Created:          20200406
# Updated:          20200422 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package download

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script. 

# Description:      This tool will allow a user to batch download and compile post-December 6th, 2016 
#                   Sentinel-2 Level-1C products using three filters: 1) date range, 2) cloud cover range, and 3) tiles that  
#                   completely contain a polygon drawn by the user in an ArcGIS Pro map.
 
# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           AOI_Polygon: Feature Set (Data Type) > Required (Type) > Direction (Input) 
#                           Output_Directory: Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User_Name: String (Data Type) > Required (Type) > Direction (Input) 
#                           User_Password: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_Begin: String (Data Type)> Required (Type)> Direction (Input)
#                           Date_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_Begin: String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_End: String (Data Type) > Required (Type) > Direction (Input)
#                           Bands_Chosen_List: String-Multiple Values (Data Type) > Required (Type) > Direction (Input) > Value List of 01 through 12 (Filter)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicus Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Cull query results by keeping only one file per date with the smallest size
# 4. Download culled products to output directory
# 5. Unzip Sentinel-2 product 1C zipped downloaded files 
# 6. Composite user selected bands

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat, zipfile, glob, fnmatch

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

# User selects bands to be composited
bands_chosen_list = arcpy.GetParameterAsText(8)

# Create list out of user selected band numbers
bands_list = bands_chosen_list.split(";")

arcpy.AddMessage('This script will composite Sentinel bands: ' + str(bands_list))

# 0.2 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Change working directory to output directory
os.chdir(output_directory)

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
arcpy.AddMessage('Final products were either downloaded or previously existed in output directory and are ready to be composited') 

#----------------------------------------------------------------------------------------------

# 5. Unzip Sentinel-2 product 1C zipped downloaded files

# Assign a variable to a list of all zip files within path directory 
file_list = os.listdir()
print(file_list)

# Assign variable to empty list (to which .zip files to be iterated through will be added)
zip_list = []

# Loop though each file in working directory and add any files that: 1) are zip files, and 2) have not already been unzipped
for h in file_list:
    pre_existing_unzipped = h[:-4] + '.SAFE'
    if fnmatch.fnmatch(h, '*.zip'): 
        if os.path.isdir(pre_existing_unzipped):
            print('unzipped file' + h + ' already exsits')
        else:
            zip_list.append(h)

print(zip_list)    

# Unzip each SAFE file

# For each zip file in the list
for i in zip_list:
    # Identify the unique path
    zip_path = os.path.abspath(i)
    print(zip_path)
    # Unzip to folder with same name as zip file within path directory
    with zipfile.ZipFile(zip_path, 'r') as zip_ref: # https://stackoverflow.com/questions/3451111/unzipping-files-in-python
        zip_ref.extractall(output_directory)

#----------------------------------------------------------------------------------------------
        
# 6. Composite user selected bands

# Get tuple of subdirectories in path
unzipped_directories_list = glob.glob('*.SAFE')
print(unzipped_directories_list)

for j in unzipped_directories_list:
    unzipped_directory_path = os.path.abspath(j)
    print(unzipped_directory_path)
    
    granule_folder_path = os.path.join(unzipped_directory_path, 'GRANULE')
    print(granule_folder_path)
    
    level_1C_folder_list = os.listdir(granule_folder_path)
    print(level_1C_folder_list)
    
    for k in level_1C_folder_list:
        print(k)
        level_1C_folder_path = os.path.join(granule_folder_path, k)
        print(level_1C_folder_path)
        img_folder_path = os.path.join(level_1C_folder_path, 'IMG_DATA')
        print(img_folder_path)
        raster_list = os.listdir(img_folder_path)
        print(raster_list)
        
        all_bands_of_interest_path_list = []
        
        for r in raster_list:
            print(r)
            raster_path = os.path.join(img_folder_path, r)
            print(raster_path)
            
            for b in bands_list:
                print(b)
                match_string = '*' + str(b) + '.jp2'
                print(match_string)
                if fnmatch.fnmatch(r, match_string):
                    all_bands_of_interest_path_list.append(raster_path)

        print(all_bands_of_interest_path_list)
        
        # Assign variables to composited rasters using the following nomenclature: MMM_MSIXXX_YYYYMMDD_Txxxxx_Bands_.img (MissionID_ProductLevel_SensingDate_TileNumber_BandsSelected.img)
        composite_raster_name = j.split('_')[0] + '_' + j.split('_')[1] + '_' + j.split('_')[2][:8] + '_' + j.split('_')[5] + '_' + '_Composited.img' 
        
        print(composite_raster_name)
        
        composite_raster = os.path.join(output_directory, composite_raster_name)
        print(composite_raster)
        
        arcpy.CompositeBands_management(in_rasters = all_bands_of_interest_path_list, out_raster = composite_raster)
        arcpy.AddMessage('Finished compositing ' + composite_raster_name)