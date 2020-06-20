
###############################################################################################
###############################################################################################

# Name:             5.00_Generate_Raster_Subsets_and _Training_and_Accuracy_Field_Shapefiles.py
# Author:           Kelly Meehan, USBR
# Created:          20190724
# Updated:          20200619 
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
# 3. Reproject rasters 
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

# 3. Reproject rasters 

# Assign variable to name of spatial reference of Edited Field Borders Shapefile
borders_spatial_reference = arcpy.Describe(edited_field_borders_shapefile).spatialReference.name

reprojected_raster_list = []

for i in raw_raster_list:
    
    # Reproject raster
    
    reprojected_raster = os.path.splitext(i)[0] + '_' + borders_spatial_reference + '.img'
    arcpy.ProjectRaster_management(in_raster = i, out_raster = reprojected_raster, out_coor_system = edited_field_borders_shapefile)
    
    arcpy.AddMessage('Generated: ' + reprojected_raster)

    # Add copied raster to list as well as copied raster name to another list 
    reprojected_raster_list.append(reprojected_raster)

#--------------------------------------------------------------------------

# 4. Mosaic rasters (if applicable)

arcpy.env.snapRaster = reprojected_raster_list[0]

# If there is more than one passed through GUI by user in Raw Sentinel Image(s) multi-value parameter:
if len(reprojected_raster_list) > 1:

    # Set Mosaiced Raw Sentinel Image(s) name and path 
    mosaic_raster_name = os.path.splitext(reprojected_raster_list[0])[0] + '_mosaic.img'
    mosaic_raster = os.path.join(img_path, mosaic_raster_name) 

#------------------ Test begin

    # Check that all rasters to be mosaiced have same no data value
    
    # Create list comprehension of no data value of reprojected rasters
    no_data_list = [arcpy.Raster(b).noDataValue for b in reprojected_raster_list]
    
    # If all no data values match, assign variable to this consistent no data value
    if len(set(no_data_list)) == 1:
        no_data_value = no_data_list[0]
        
#------------------ Test end
        
        # Mosaic rasters if there is more than one
        arcpy.Mosaic_management(inputs = reprojected_raster_list, target = reprojected_raster_list[0], mosaic_type = 'FIRST', colormap = 'FIRST', nodata_value = no_data_value)
    
        # Try to rename first input raster as this is the file all others have been mosaiced to
        try:
            arcpy.Rename_management(in_data = reprojected_raster_list[0], out_data = mosaic_raster_name)
        
        # If an exception is raised (ExecuteError: ERROR 000012: *mosaic.img already exists), and first input raster cannot be renamed, execute the following
        except Exception:
            
            arcpy.AddWarning('Cannot rename first input raster which is now a mosaic. After tool has completed running, please manually rename ' + reprojected_raster_list[0] + ' to ' + mosaic_raster)
            
            for a in reprojected_raster_list[1:]:
                
                # Keep first input raster so user can manually rename it; delete all other reprojected rasters
                arcpy.Delete_management(in_data = a)
                arcpy.AddMessage('Deleted intermediary raster: ' + a)
                
            # Assign variable to first input raster so that it is used as base for subsequent subsets
            raster = reprojected_raster_list[0]
        
        # If an exception is not raised, execute the following
        else:
            arcpy.AddMessage('Generated new mosaic raster: ' + mosaic_raster_name)
            
            for r in reprojected_raster_list:
                
                # Delete all intermediary rasters
                arcpy.Delete_management(in_data = r)
                arcpy.AddMessage('Deleted intermediary raster: ' + r)
                
        # Assign variable to mosaic raster
        raster = mosaic_raster 
    
    else:
        arcpy.AddError('No data values for input rasters were not consistent, please examine no data values of input rasters to ensure consistency before mosaicing')
        sys.exit(0)   
    
# If user only passes one raster, assign variable to the reprojected raster so that it is used as base for subsequent subsets 
else: 
    raster = reprojected_raster_list[0] 
    
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
    del out_aoi_raster
    
    arcpy.AddMessage('Generated AOI Subset Raster: ' + aoi_subset)

    # Generate Field Borders Subset Raster
    
    # Create name and path for Field Borders Subset Raster
    fields_subset = os.path.join(img_path, region_and_time + '_fields_subset.img')
    
    # Create Field Borders Subset Raster    
    arcpy.env.mask = edited_field_borders_shapefile
    out_borders_raster = ExtractByMask(in_raster = raster, in_mask_data = edited_field_borders_shapefile)
    out_borders_raster.save(fields_subset)   
    del out_borders_raster
    
    arcpy.AddMessage('Generated Field Borders Subset Raster: ' + fields_subset)
    
    # Generate Training Fields Subset Raster
    
    # Create name and path for Training Fields Subset Raster
    training_subset = os.path.join(img_path, region_and_time + '_training_subset.img')
    
    # Create Training Fields Subset Raster
    arcpy.env.mask = training_fields_mask
    out_training_raster = ExtractByMask(in_raster = raster, in_mask_data = training_fields_mask)
    out_training_raster.save(training_subset)  
    del out_training_raster
    
    arcpy.AddMessage('Generated Training Subset Raster: ' + training_subset)

else: 
    arcpy.AddError('Raster does not fully contain a minimum bounding box of edited field borders feature class. Please include additional raster in Raw Images parameter.')
    sys.exit(0)    
