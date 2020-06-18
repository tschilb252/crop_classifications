
###############################################################################################
###############################################################################################

# Name:             5.00_Generate_Raster_Subsets_and _Training_and_Accuracy_Field_Shapefiles.py
# Author:           Kelly Meehan, USBR
# Created:          20190724
# Updated:          20200616 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      This tool generates shapefile and raster subsets of a field border shapefile and Sentinel satellite image, respectively.  

###############################################################################################
################################################################################################ 

# This script will:
# 0. Set up
# 1. Create Accuracy Fields Shapefile and Training Fields Shapefile, subset from Edited Fields Shapefile
# 2. Create Training Fields Mask Shapefile, 30 meter inner buffer mask of Training Fields Shapefile
# 3. Assign pixels with value of 0 to NoData and reproject rasters 
# 4. Mosaic rasters (if applicable)
# 5. Create three subsets from Mosaiced Raw Raster Sentinel Image(s) or Raw Sentinel Image 

#----------------------------------------------------------------------------------------------

# 0. Set up
 
# 0.0 Import necessary packages 
import arcpy, os, sys
from arcpy.sa import ExtractByMask

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects Edited Field Borders Shapefile
edited_field_borders_shapefile = arcpy.GetParameterAsText(0) 

# User selects Raw Sentinel Image(s) in order of priority (dominant raster first)
raw_raster_list = arcpy.GetParameterAsText(1).split(';')
#raw_raster_list = raw_raster_or_rasters.split(';') 

# User selects Image Directory
img_path = arcpy.GetParameterAsText(2)

# User selects Coverage Directory
covs_path = arcpy.GetParameterAsText(3)

#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

# Set snap raster to first raster (priority raster)
arcpy.env.snapRaster = raw_raster_list[0]

#--------------------------------------------

# 0.3 Check out spacial analyst extension
arcpy.CheckOutExtension('Spatial')

#--------------------------------------------------------------------------

# 1. Create Accuracy Fields Shapefile and Training Fields Shapefile, subset from Edited Fields Shapefile

# Create Accuracy Fields Shapefile 

region_and_time = os.path.basename(edited_field_borders_shapefile).rsplit(sep = '_', maxsplit = 1)[0]
accuracy_fields_shapefile = os.path.join(covs_path, region_and_time + '_accuracy_fields.shp')

arcpy.Select_analysis(in_features = edited_field_borders_shapefile, out_feature_class = accuracy_fields_shapefile, where_clause = ' "aa" = 2 ')

arcpy.AddMessage('Generated Accuracy Fields Shapefile: ' + str(accuracy_fields_shapefile) + ' in ' + str(covs_path))

# Create Training Fields Shapefile 

training_fields_shapefile = os.path.join(covs_path, region_and_time + '_training_fields.shp')

arcpy.Select_analysis(in_features = edited_field_borders_shapefile, out_feature_class = training_fields_shapefile, where_clause = ' "aa" = 1 ')

arcpy.AddMessage('Generated Training Fields Shapefile: ' + str(training_fields_shapefile) + ' in ' + str(covs_path))

#--------------------------------------------------------------------------

# 2. Create Training Fields Mask Shapefile, 30 meter inner buffer mask of Training Fields Shapefile

training_fields_mask = os.path.join(covs_path, region_and_time + '_training_fields_mask.shp')

arcpy.Buffer_analysis(in_features = training_fields_shapefile, out_feature_class = training_fields_mask, buffer_distance_or_field = '-30') 

arcpy.AddMessage('Generated Training Fields Mask: ' + str(training_fields_mask) + ' in ' + str(covs_path))

#--------------------------------------------------------------------------

# 3. Assign pixels with value of 0 to NoData and reproject rasters 

copied_raster_list = []
copied_raster_name_list = []
    
for i in raw_raster_list:
    
    # Assign pixels with value of 0 to NoData
    arcpy.SetRasterProperties_management(in_raster = i, data_type = '#', statistics = '#', stats_file = '#', nodata = '1 0; 2 0; 3 0; 4 0; 5 0; 6 0; 7 0; 8 0; 9 0; 10 0', key_properties = '#')
    
    arcpy.AddMessage('Set pixels with value of 0 to NoData')
    
    # Reproject raster
    reprojected_raster_name = os.path.splitext(i)[0] + '_Reprojected.img'
    reprojected_raster = os.path.join(img_path, reprojected_raster_name)    
    arcpy.ProjectRaster_management(in_raster = i, out_raster = reprojected_raster, out_coor_system = edited_field_borders_shapefile)
    
    arcpy.AddMessage('Reprojected: ' + i)

    # Add copied raster to list as well as copied raster name to another list 
    copied_raster_list.append(reprojected_raster)
    copied_raster_name_list.append(reprojected_raster_name)

#--------------------------------------------------------------------------

# 4. Mosaic rasters (if applicable)

arcpy.env.snapRaster = copied_raster_list[0]

# If there is more than one passed through GUI by user in Raw Sentinel Image(s) multi-value parameter:
if len(copied_raster_list) > 1:

    # Set Mosaiced Raw Sentinel Image(s) name and path 
    mosaic_raster_name = os.path.splitext(copied_raster_name_list[0])[0] + '_mosaic.img'
    mosaic_raster = os.path.join(img_path, mosaic_raster_name) 

    # Mosaic rasters if there is more than one
    arcpy.Mosaic_management(inputs = copied_raster_list, target = copied_raster_list[0], mosaic_type = 'FIRST', colormap = 'FIRST', nodata_value = 0)

    arcpy.Rename_management(in_data = copied_raster_list[0], out_data = mosaic_raster_name)
    arcpy.Delete_management(in_data = copied_raster_list[1])
    arcpy.AddMessage('Generated new mosaic raster: ' + mosaic_raster_name)

    raster = mosaic_raster # Used here so as to avoid duplicated code 
    arcpy.AddMessage('Appended rasters to ' + str(copied_raster_list[0]) + ' to create mosaiced raster: ' + str(mosaic_raster_name))

# If only one raster is passed through GUI by user in Raw Sentinel Image(s) multi-value parameter:
else: 
    raster = copied_raster_list[0] 

#--------------------------------------------------------------------------

# 5. Create three subsets from Mosaiced Raw Raster Sentinel Image(s) or Raw Sentinel Image 

# Reset snap raster environment parameter
arcpy.env.snapRaster = raster

# Generate bounding box, a square polygon that containsall polygons of edited field borders shapefile
bounding_box = os.path.join(covs_path, region_and_time + '_bounding_box.shp') 
arcpy.MinimumBoundingGeometry_management(in_features = edited_field_borders_shapefile, out_feature_class = bounding_box, geometry_type = 'ENVELOPE', group_option = 'ALL')

# Find extent of bounding box and raster 

describe_box = arcpy.Describe(bounding_box)
extent_box = describe_box.extent

describe_raster = arcpy.Describe(raster)
extent_raster = describe_raster.extent

box_contains_raster = extent_raster.contains(extent_box)

# Test whether bounding box extent is within raster; if so, subset raster 
if box_contains_raster == True:
    
    # Set path name and file name for AOI Subset Raster
    aoi_subset = os.path.join(img_path, region_and_time + '_AOI_subset.img')
    
    # Create AOI Subset Raster   
    arcpy.env.mask = bounding_box
    out_aoi_raster = ExtractByMask(in_raster = raster, in_mask_data = bounding_box)
    out_aoi_raster.save(aoi_subset)    
    
    arcpy.AddMessage('Generated AOI Subset Raster: ' + aoi_subset)

    # Generate Field Borders Subset Raster
    
    # Create name and path for Field Borders Subset Raster
    fields_subset = os.path.join(img_path, region_and_time + '_fields_subset.img')
    
    # Create Field Borders Subset Raster    
    arcpy.env.mask = edited_field_borders_shapefile
    out_borders_raster = ExtractByMask(in_raster = raster, in_mask_data = edited_field_borders_shapefile)
    out_borders_raster.save(fields_subset)   
    
    arcpy.AddMessage('Generated Field Borders Subset Raster: ' + fields_subset)
    
    # Generate Training Fields Subset Raster
    
    # Create name and path for Training Fields Subset Raster
    training_subset = os.path.join(img_path, region_and_time + '_training_subset.img')
    
    # Create Training Fields Subset Raster
    arcpy.env.mask = training_fields_mask
    out_training_raster = ExtractByMask(in_raster = raster, in_mask_data = training_fields_mask)
    out_training_raster.save(training_subset)  
    
    arcpy.AddMessage('Generated Training Subset Raster: ' + training_subset)

else: 
    arcpy.AddError('Raster does not fully contain a minimum bounding box of edited field borders feature class. Please include additional raster in Raw Images parameter.')
    sys.exit(0)    
