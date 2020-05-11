###############################################################################################
###############################################################################################

# Name:             0.24_Sentinel-2_Level-1C_Batch_Download_by_Tile_and_Orbit.py
# Author:           Kelly Meehan, USBR
# Created:          20200505
# Updated:          20200510
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will allow a user to batch download (post-20170331) 
#                   Sentinel-2 Level-1C products using four filters: 1) date range, 2) cloud cover range, 3) relative orbit number and 4) tile id
#                   Download Sentinel-2 Relative Orbits KML file at https://sentinel.esa.int/web/sentinel/missions/sentinel-2/satellite-description/orbit
#                   Download Sentinel-2 Tiles KML at https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products

# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           Orbit              String (Data Type) > Required (Type) > Direction (Input)    
#                           Tile               String (Data Type) > Required (Type) > Direction (Input)
#                           Output Directory   Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           User Name          String (Data Type) > Required (Type) > Direction (Input) 
#                           User Password      String (Data Type)> Required (Type)> Direction (Input)
#                           Date Range Begin   String (Data Type)> Required (Type)> Direction (Input)
#                           Date Range End     String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud Range Begin  String (Data Type) > Required (Type) > Direction (Input)
#                           Cloud Range End    String (Data Type) > Required (Type) > Direction (Input)
#                           Composite Bands?   Boolean (Data Type) > Required (Type) > Direction (Input)
#                           Bands              String-Multiple Values (Data Type) > Optional (Type) > Direction (Input) > Value List of 01 through 12 (Filter)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Authenticate credentials to Copernicus Open Access Hub 
# 2. Run query and store resultant list of products as an ordered dictionary
# 3. Generate csv of product metadata
# 4. Download products
# 5. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, sentinelsat, glob, zipfile, fnmatch, datetime

# 0.1 Assign variables to tool parameters and run checks on values passed

# User specifies relative orbit number to filter query results
orbit = arcpy.GetParameterAsText(0)

# User specifies tile id to filter query results
tile = arcpy.GetParameterAsText(1)

# User specifies folder where Sentinel imagery should be saved to 
output_directory = arcpy.GetParameterAsText(2)

# User adds existing username for Copernicus Open Access Hub
user_name = arcpy.GetParameterAsText(3)

# User adds existing password for Copernicus Open Access Hub
user_password = arcpy.GetParameterAsText(4)

# User specifies query date range beginningin the form of YYYYMMDD
date_range_begin = arcpy.GetParameterAsText(5)
# Raise error if user passes something other than a three character string of numbers for orbit parameter     

# User specifies query date range ending in the form of YYYYMMDD
date_range_end = arcpy.GetParameterAsText(6)

# User specifies query cloud range beginning percentage as an integer value between 0 and 100
cloud_range_begin = arcpy.GetParameterAsText(7)

# User specifies query cloud range ending percentage as an integer value between 0 and 100
cloud_range_end = arcpy.GetParameterAsText(8)

# User specifies whether to generate composite raster or not
composite_is_checked = arcpy.GetParameterAsText(9)

# User selects bands to be composited 
bands = arcpy.GetParameterAsText(10) # NOTE: multi-value string is returned as string with semi-colon delimiter (e.g. '02;03;04;08')

#--------------------------------------------

# 0.2 Run validation tests on user passed arguments; end tool and display error message if requirements not met

# Ensure that Orbit parameter receives a character string consisting of a three digigt integer
if len(orbit) != 3 or not orbit.isdigit():
    arcpy.AddError('{0} is not an appropriate value to pass to Orbit parameter. Please provide a three digit integer'.format(orbit))
    raise arcpy.ExecuteError

# Ensure that Tile parameter receives a character string consisting of a two digit integer followed by three letters
if len(tile) != 5 or not tile[:2].isdigit() or not tile[2:].isalpha():
    arcpy.AddError('{0} is not an appropriate value to pass to Tile parameter. Please provide five characters (two integers followed by three letters)'.format(tile))
    raise arcpy.ExecuteError

# Ensure that Date Range Begin parameter receives a character string consisting of eight integers
if len(date_range_begin) != 8 or not date_range_begin.isdigit():
    arcpy.AddError('{0} is not an appropriate value to pass to Date Range Begin parameter. Please provide eight integers in the following format: YYYYMMDD'.format(date_range_begin))
    raise arcpy.ExecuteError

# Ensure that Date Range End parameter receives a character string consisting of eight integers or the word NOW (in caps)
if date_range_end == 'NOW' or (len(date_range_end) == 8 and date_range_end.isdigit()):
    pass
else:
    arcpy.AddError('{0} is not an appropriate value to pass to Date Range End parameter. Please provide either 1) eight integers in the following format: YYYYMMDD, or 2) NOW'.format(date_range_end))
    raise arcpy.ExecuteError
    
# Ensure that Date Range Begin parameter receives a date value that precedes Date Range End
if date_range_end == 'NOW':
    date_end = datetime.datetime.today().strftime("%Y%m%d")
else: 
    date_end = date_range_end

if int(date_range_begin) > int(date_end):
    arcpy.AddError('{0} and {1} are not appropriate values to pass to Date Range Begin and Date Range End parameters. Please provide a date for Date Range Begin that preceeds Date Range End'.format(date_range_begin, date_range_end))
    raise arcpy.ExecuteError

# Ensure that Date Range End (and consequently Date Range Begin) parameters receive a date value that does not precede March 31st, 2017      
if int(date_end) < 20170401:
    arcpy.AddError('{0} and {1} are not appropriate values to pass to Date Range Begin and Date Range End parameters. Please provide a dates that precede April 1st, 2017'.format(date_range_begin, date_range_end))
    raise arcpy.ExecuteError

# Ensure that Cloud Range Begin parameter receives an integer between 0 and 100
if int(cloud_range_begin) < 0 or int(cloud_range_begin) > 100 or not cloud_range_begin.isdigit():
    arcpy.AddError('{0} is not an appropriate value to pass to Cloud Range Begin. Please provide an integer value between 0 and 100'.format(cloud_range_begin))
    raise arcpy.ExecuteError
    
# Ensure that Cloud Range End parameter receives an integer between 0 and 100
if int(cloud_range_end) < 0 or int(cloud_range_end) > 100 or not cloud_range_end.isdigit():
    arcpy.AddError('{0} is not an appropriate value to pass to Cloud Range End. Please provide an integer value between 0 and 100'.format(cloud_range_end))
    raise arcpy.ExecuteError
    
#--------------------------------------------

# 0.3 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool 
arcpy.env.overwriteOuptut = True

#--------------------------------------------

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

#----------------------------------------------------------------------------------------------

# 5. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands

# Create list of strings out of user selected band numbers (e.g. ['02', '03', '04', '08'])
bands_list = bands.split(';')

# 0.2 Convert user-passed argument string of bands into organized string for naming convention

# Convert bands string of numbers into list of integers (e.g. [2, 3, 4, 8])
bands_integer_list = list(map(int,(bands.split(';'))))

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

# Create list of Sentinel-2 Level-1C zip files present in output directory 
if str(composite_is_checked) == 'true':
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