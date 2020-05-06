###############################################################################################
###############################################################################################

# Name:             0.24_Sentinel-2_Level-1C_Unzip_and_Copmosite.py
# Author:           Kelly Meehan, USBR
# Created:          20200423
# Updated:          20200505 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro license and sentinelsat Python package

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script 

# Description:      This tool will unzip Sentinel-2 Level-1C products and will composite user-selected bands
 
# Tool setup:       The script tool's properties can be set as follows (label does not matter, only the order): 
#                       Parameters tab:    
#                           Output_Directory: Workspace (Data Type) > Required (Type) > Direction (Input) 
#                           Bands: String-Multiple Values (Data Type) > Required (Type) > Direction (Input) > Value List of 01 through 12 (Filter)

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Import necessary packages
import os, arcpy, zipfile, glob, fnmatch

# 0.1 Assign variables to tool parameters

# User specifies folder where Sentinel imagery should be saved to 
output_directory = arcpy.GetParameterAsText(0)

# User selects bands to be composited 
bands = arcpy.GetParameterAsText(1) # NOTE: multi-value string is returned as string with semi-colon delimiter (e.g. '02;03;04;08')

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

# 0.3 Set environment settings

# Set workspace to output directory
arcpy.env.workspace = output_directory

# Set overwrite permissions to true in case user reruns tool 
arcpy.env.overwriteOuptut = True

# 0.4 Change working directory to output directory
os.chdir(output_directory)

#----------------------------------------------------------------------------------------------

# 1. Iterate through Sentinel-2 product Level-1C product zip files, unzip files to retreive .SAFE if necessary, and composite user-selected bands

# Create list of Sentinel-2 Level-1C zip files present in output directory 
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
    
        
