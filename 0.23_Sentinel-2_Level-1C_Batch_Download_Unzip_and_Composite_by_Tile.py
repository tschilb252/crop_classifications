###############################################################################################
###############################################################################################

# Name:             0.23_Sentinel-2_Level-1C_Batch_Download_Unzip_and_Composite_by_Tile.py
# Author:           Kelly Meehan, USBR
# Created:          20200415
# Updated:          20200507 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will allow a user to batch download and compile (post-2017-03-31) 
#                   Sentinel-2 Level-1C products using three filters: 1) date range, 2) cloud cover range, and 3) tile id
#                   Download Sentinel-2 Tiles KML at https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products
 
# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           Tiles_Chosen_List               String-Multiple Values (Data Type) > Required (Type) > Direction (Input)
#                           Output_Directory                Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User_Name                       String (Data Type) > Required (Type) > Direction (Input) 
#                           User_Password                   String (Data Type) > Required (Type)> Direction (Input)
#                           Date_Range_Begin                String (Data Type) > Required (Type)> Direction (Input)
#                           Date_Range_End                  String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_Begin               String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud_Range_End                 String (Data Type) > Required (Type) > Direction (Input)
#                           Composite Bands?                Boolean (Data Type) > Optional (Type) > Direction (Input)
#                           Bands                           String-Multiple Values (Data Type) > Optional (Type) > Direction (Input) > Value List of 01 through 12 (Filter)


#                       Validation tab: 

# import arcpy

# class ToolValidator(object):
#     """Class for validating a tool's parameter values and controlling
#     the behavior of the tool's dialog."""

#     def __init__(self):
#         """Setup arcpy and the list of tool parameters.""" 
#         self.params = arcpy.GetParameterInfo()

#     def initializeParameters(self):
#         """Refine the properties of a tool's parameters. This method is 
#         called when the tool is opened."""

#     def updateParameters(self):
#         """Modify the values and properties of parameters before internal
#         validation is performed. This method is called whenever a parameter
#         has been changed."""

#         # Make Bands parameter only appear if composite band box is checked
#         if self.params[8].value:
#             self.params[9].enabled = True
#         else:
#             self.params[9].enabled = False
   
#         # Set a default value for Bands parameter
#         if self.params[8].value:
#             if not self.params[9].altered:
#                 self.params[9].value = '02;03;04;08'
    
#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""

#     def isLicensed(self):
#         """Set whether tool is licensed to execute."""
#         return True
    
###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicus Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Cull query results by keeping only one file per date with the smallest size
# 4. Generate csv of downloaded product metadata
# 5. Download products
# 6. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands (if user selected to composite bands)

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat, zipfile, glob, fnmatch, collections

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

# User specifies whether to generate composite raster or not
composite_is_checked = arcpy.GetParameterAsText(8)

# User selects bands to be composited 
bands = arcpy.GetParameterAsText(9) # NOTE: multi-value string is returned as string with semi-colon delimiter (e.g. '02;03;04;08')

#--------------------------------------------

# 0.2 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool 
arcpy.env.overwriteOuptut = True

#--------------------------------------------

# 0.3 Change working directory to output directory
os.chdir(output_directory)

#----------------------------------------------------------------------------------------------

# 1. Authenticate credentials to Copernicus Open Access Hub 
api = sentinelsat.SentinelAPI(user = user_name, password = user_password)

#----------------------------------------------------------------------------------------------

# 2. Run query and store resultant list of products as an ordered dictionary

# Create empty ordered dictionary
products = collections.OrderedDict()

# For each tile, run query and update products OrderedDict with results
for i in tiles_list:
    arcpy.AddMessage('Searching for Sentinel-2 Level-1C products matching query')
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

# 4. Generate csv of downloaded product metadata

# Create list comprehension of by adding 'T' to the beginning of each tile number in tiles_list 
tile_names_list = ['T' + tile for tile in tiles_list]

# Concatenate string elements in tiles_list to single string
tiles_string = '_'.join(tile_names_list)

# Write Pandas DataFrame to csv in output directory
products_df_unduplicated.to_csv('Sentinel-2_Level-1C_Query_' + tiles_string + '_' + date_range_begin + '-' + date_range_end + '_Clouds_' + cloud_range_begin + '-' + cloud_range_end + '_Metadata.csv')

#----------------------------------------------------------------------------------------------

# 5. Download products

# Download all final products to output directory
api.download_all(products = products_df_unduplicated.index, directory_path = output_directory)

# Print message confirming downloads complete
arcpy.AddMessage('Final products were either downloaded or previously existed in output directory and are ready to be composited') 

#----------------------------------------------------------------------------------------------

# 6. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands (if user selected to composite bands)

# Create list of Sentinel-2 Level-1C zip files present in output directory 
if str(composite_is_checked) == 'true':
    
    # Create list of strings out of user selected band numbers (e.g. ['02', '03', '04', '08'])
    bands_list = bands.split(';')
    
    # 0.2 Convert user-passed argument string of bands into organized string for naming convention
    
    # Convert bands string of numbers into list of integers (e.g. [2, 3, 4, 8])
    bands_integer_list = sorted(list(map(int,(bands.split(';')))))
    
    # Function to convert list of numbers into a string that more elegantly expresses instances of consecutive sequences
    #   Adapted from: https://stackoverflow.com/questions/29418693/write-ranges-of-numbers-with-dashes
    
    def organize_list_of_integers(band_numbers):
        seq = []
        final = []
        last = 0
    
        for index, val in enumerate(band_numbers):
            # Check to see if current value is either the first in list or a consecutive number from the previous
           
            # If element is either first element or consecutive number, add value to sequence list
            if last + 1 == val or index == 0:
                seq.append(val)
                last = val
            # If element is not consecutive number
            else:
                # Either add string of first-last in the case of a sequence
                if len(seq) > 1:
                   final.append(str(seq[0]) + '-' + str(seq[len(seq)-1]))
                # Or just add previous single value to final
                else:
                   final.append(str(seq[0]))
                seq = []
                seq.append(val)
                last = val
            
            # Check to see if loop is on last number in list (seq gets converted during the next index's turn, which doesn't exist for last index)
            if index == len(band_numbers) - 1:
                # Either add string of first-last in the case of a sequence
                if len(seq) > 1:
                    final.append(str(seq[0]) + '-' + str(seq[-1]))
                # Or just add single value to final
                else:
                    final.append(str(seq[0]))
        # Concatenate list of string elements in final list into one string using '_' in between elements
        final_str = '_'.join(final)
        return final_str
    
    # Call function and assign variable to resultant string (for use at end of script in naming convention of final composite rasters)
    band_nomenclature = organize_list_of_integers(bands_integer_list)
    
    # Print list of bands to be composited by tool
    arcpy.AddMessage('This script will composite only Sentinel bands: ' + bands)

#--------------------------------------------
    
    zip_list = glob.glob('S2?_MSIL1C*.zip')
    
    for z in zip_list:
        
        # Check to see if composite raster associated with zip file and based on user-selected bands already exists
        
        # Assign variables to composite raster associated with zip file and based on user-selected bands using the following nomenclature:      
        #   S2_MSIL1C_YYYYMMDD_Rxxx_Txxxxx_Bx_.img 
        #   (i.e. S2_ProductLevel1C_SensingDate_RelativeOrbitNumber_TileNumber_BandsComposited.img)
        composite_raster_name = z.split('_')[0][:-1] + '_' + z.split('_')[1] + '_' + z.split('_')[2][:8] + '_' + z.split('_')[4] + '_' + z.split('_')[5] + '_B' + band_nomenclature + '.img' 
        
        if os.path.isfile(composite_raster_name):
            
            # If composite exists, continue to next zip file
            continue
        
        # Otherwise, if composite raster associated with zip file and based on user-selected bands, then proceed 
        else:
            arcpy.AddMessage(composite_raster_name + ' does not already exist, proceeding')
            
            # Check to see if associated SAFE directory already exists
            safe_directory = z[:-4] + '.SAFE'  
        
            if os.path.isdir(safe_directory):
                
                # If associated SAFE directory already exists, proceed
                arcpy.AddMessage(safe_directory + ' already exists')
                
            # Otherwise, if associated SAFE directory does not exist, unzip zip file to create SAFE directory 
            else:  
                
                # Identify the unique path of zip file
                zip_path = os.path.abspath(z)
               
                # Unzip to folder with same name as zip file within path directory
                with zipfile.ZipFile(zip_path, 'r') as zip_ref: 
                    zip_ref.extractall(output_directory)
                
                arcpy.AddMessage('created ' + safe_directory)
                
            # Composite rasters within IMG_DATA directory (within GRANULE directory of SAFE directory) that match user-selected bands
        
            granule_folder_path = os.path.join(safe_directory, 'GRANULE')
            level_1C_folder_list = os.listdir(granule_folder_path)
            for k in level_1C_folder_list:
                level_1C_folder_path = os.path.join(granule_folder_path, k)
                img_folder_path = os.path.join(level_1C_folder_path, 'IMG_DATA')
                raster_list = os.listdir(img_folder_path)
                all_bands_of_interest_path_list = []
                for r in raster_list:
                    raster_path = os.path.join(img_folder_path, r)
                    for b in bands_list:
                        match_string = '*' + str(b) + '.jp2'
                        if fnmatch.fnmatch(r, match_string):
                            all_bands_of_interest_path_list.append(raster_path)
                
                # Generate ERDAS IMAGINE, .img composite of rasters matching user-selected bands
                
                composite_raster = os.path.join(output_directory, composite_raster_name)
                arcpy.CompositeBands_management(in_rasters = all_bands_of_interest_path_list, out_raster = composite_raster)
                arcpy.AddMessage('Finished compositing ' + composite_raster_name)