
###############################################################################################
###############################################################################################

# Name:             7.10_Segment_Training_Samples_and_Image.py
# Author:           Kelly Meehan, USBR
# Created:          20201216
# Updated:          20200204 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.

# Description:      

#----------------------------------------------------------------------------------------------


###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. 
#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages

import arcpy, itertools, os, re
from arcpy.sa import SegmentMeanShift, TrainSupportVectorMachineClassifier, ClassifyRaster

#--------------------------------------------

# 0.1 Read in tool parameters

# User selects Training Fields Subset Raster
training_subset = arcpy.GetParameterAsText(0) 

# User selects Fields Borders Subset Raster 
fields_subset = arcpy.GetParameterAsText(1)

# User selects Image Directory
img_path = arcpy.GetParameterAsText(2)

# User selects Coverage Directory
covs_path = arcpy.GetParameterAsText(3)

# User selects Documents Directory
docs_path = arcpy.GetParameterAsText(4)

# User selects Project Geodatabase
gdb_path = arcpy.GetParameterAsText(5)

# User selects Training Fields Shapefile
training_fields = arcpy.GetParameterAsText(6)

# User selects two digit classification iteration number
#iteration_number = arcpy.GetParameterAsText(6)


#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

# 0.3 Check out Spatial Analyst Extension
arcpy.CheckOutExtension('Spatial')

#----------------------------------------------------------------------------------------------

# 1. Segment Training Samples

# Delete local variable if exists 
if 'segmented_training' in locals():
    arcpy.AddMessage('delecting segmented_training')
    del segmented_training
 
## Segment image

# Create list of all parameters to consider for unique combinations
spectral_detail_list = ['5', '10', '15', '20']
spatial_detail_list = ['5', '10', '15', '20']
min_segment_size_list = ['10', '20', '30']

# Remove
#band_indexes_list = ['2 3 7', '3 7 9']

bands_indexes_dictionary = {'2 3 7': '237', '3 7 9': '379'}
band_indexes_list = list(bands_indexes_dictionary.keys())
parameters_master_list = [spectral_detail_list, spatial_detail_list, min_segment_size_list, band_indexes_list]

parameters_combination_list = list(itertools.product(*parameters_master_list))

len(parameters_combination_list)

#### Splat operator example
for i in parameters_combination_list:
    print(i)

def print_test(spectral, spatial, size, bands):
    print('spectral_detail is: ' + spectral)
    print('spatial detail is: ' + spatial)
    print('min segment is: ' + size) 
    print('band_indexes is: ' + bands)

for i in parameters_combination_list:
    print_test(*i)

#### END Splat example

training_subset_name = os.path.basename(training_subset).split(sep = '.', maxsplit = 1)[0]

region_time = training_subset_name.rsplit(sep = '_', maxsplit = 2)[0]

def iterate_segmentation_training(raster_to_segment, spectral, spatial, size, bands):
    segmented_training_raster = SegmentMeanShift(in_raster = raster_to_segment, spectral_detail = spectral, spatial_detail = spatial, min_segment_size = size, band_indexes = bands)
    
    training_subset_name = os.path.basename(raster_to_segment).split(sep = '.', maxsplit = 1)[0]

    region_time = training_subset_name.rsplit(sep = '_', maxsplit = 1)[0]

    parameters_concatenated = str(spectral) + '_' + str(spatial) + '_' + str(size) + '_' + bands_indexes_dictionary[bands]
     
    output_training_raster_name = region_time + '_' + parameters_concatenated + '.tif'
    print(output_training_raster_name)
    output_training_raster = os.path.join(img_path, output_training_raster_name)
    
    # Save output
    segmented_training_raster.save(output_training_raster)
    
    # Polygon to raster
    segmented_polygons_name = region_time + '_' + parameters_concatenated
    segmented_polygons = os.path.join(gdb_path, segmented_polygons_name)
    
    arcpy.conversion.RasterToPolygon(in_raster = segmented_training_raster, out_polygon_features = segmented_polygons, simplify = 'NO_SIMPLIFY', create_multipart_features = 'SINGLE_OUTER_PART')

# Create all possible combinations (based on given lists) of segmentations for Field Borders Subset Raster
for i in parameters_combination_list:
    iterate_segmentation_training(fields_subset, *i)

# Create all possible combinations (based on given lists) of segmentations for Training Fields Subset Raster 
for i in parameters_combination_list:
    iterate_segmentation_training(training_subset, *i)
    
#----------------------------------------------------------------------------------------------
    
#2 Train classifier

arcpy.env.workspace = img_path

# Make list of fields segments
field_segment_rasters = arcpy.ListRasters(wild_card = '*MID2_T2_2017_fields_*.tif')    

# Create list of tuples for all combinations of OBIA attributes to iterate through 
# Remove MEAN and SD as only available with auxilary raster
#attributes_possible = ['COLOR', 'MEAN', 'STD', 'COUNT', 'COMPACTNESS', 'RECTANGULARITY']
#attributes_possible = ['COLOR', 'COUNT', 'COMPACTNESS', 'RECTANGULARITY']
attributes_possible = ['COUNT', 'COMPACTNESS', 'RECTANGULARITY']

# Create list of all possible combinations of three attributes
obia_attributes_master_list = []
for l in range(1, len(attributes_possible)+1):
    for subset in itertools.combinations(attributes_possible, l):
        obia_attributes_master_list.append(subset)

# Convert list of tuples to list of strings of attributes joined by semicolons
obia_attributes_combinations = [';'.join(w) for w in obia_attributes_master_list]

# Add Color attribute to each element in list
obia_attributes_list = [s + ';COLOR' for s in obia_attributes_combinations]
obia_attributes_list.insert(0, 'COLOR')


def iterate_svm_training(segmented_raster_classifying, obia_combination):
    
    unique_segmentation_tif = os.path.basename(segmented_raster_classifying).split(sep = '_', maxsplit = 4)[4]
    unique_segmentation = unique_segmentation_tif.split(sep = '.')[0]
    definition_file_name = region_time + '_svm_' + unique_segmentation + '.ecd'
    definition_file = os.path.join(img_path, definition_file_name)
     
    # Run training
    TrainSupportVectorMachineClassifier(in_raster = segmented_raster_classifying, in_training_features = training_fields, out_classifier_definition = definition_file, max_samples_per_class = 0, used_attributes = obia_combination)
    
    # Run classification
    classified_raster = ClassifyRaster(in_raster = segmented_raster_classifying, in_classifier_definition = definition_file)    
    
    # Save classification output
    classified_raster_name = os.path.splitext(definition_file)[0] + '_' + obia_combination + '.tif'
    classified_raster.save(classified_raster_name)

# Iterate through segmented rasters and then obia attribute combinations

for raster in field_segment_rasters:
    print(raster)
    
    for attribute in obia_attributes_list:
        print(attribute)
        iterate_svm_training(raster, attribute)


########################################################################################################################


## TTDL
# When converting to tool, allow user to select argument values to pass to segmentation parameter.
# Add if statement to convert to polygon only if *_training_* (fileds segmentation stays raster)
# Change names to include training_segments so can be distinguished when searching geodatabase by wildcard training
# Change baseline to region_time
# Change filed_segment_rasters to point to direct file (without needing env.workspace) or have all one function: segmentation -> train -> classification
# Must reorganize so that parameter combinations written first, then segments made and immediately used for classification (instead of making list of segmented rasters later), or just add 'segments' to the name to distinguish from origial raster 



