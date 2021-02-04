
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
# 1. Create list of tuples for all combinations of OBIA attributes to iterate through (NOTE: MEAN and SD not included as no auxilary raster used) 

#----------------------------------------------------------------------------------------------

# 0. Set-up

# 0.0 Install necessary packages

import arcpy, itertools, os
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

#--------------------------------------------

# 0.2 Set environment settings

# Overwrite output
arcpy.env.overwriteOutput = True

# 0.3 Check out Spatial Analyst Extension
arcpy.CheckOutExtension('Spatial')

#----------------------------------------------------------------------------------------------

# 1. Create list of tuples for all combinations of OBIA attributes to iterate through (NOTE: MEAN and SD not included as no auxilary raster used) 

# Create list of all attributes to include, save for color
segment_attributes = ['COUNT', 'COMPACTNESS', 'RECTANGULARITY']

# Create list of all possible combinations with three attributes
unique_segment_attributes = []
for l in range(1, len(segment_attributes)+1):
    for subset in itertools.combinations(segment_attributes, l):
        unique_segment_attributes.append(subset)

# Convert list of tuples to list of strings of attributes joined by semicolons
unique_segment_attributes_list = [';'.join(w) for w in unique_segment_attributes]

# Add Color attribute to each element in list to ensure it's use in every iteration
unique_segment_attributes_list = [s + ';COLOR' for s in obia_attributes_combinations]
unique_segment_attributes_list.insert(0, 'COLOR')

#----------------------------------------------------------------------------------------------

# 2. Create list of combinations of segmentation arguments to iterate through

# Delete local variable if exists 
if 'segmented_training' in locals():
    arcpy.AddMessage('delecting segmented_training')
    del segmented_training
 
# Create list of spectral detail arguments to iterate through and pass to spectral detail parameter
spectral_detail_list = ['5', '10', '15', '20']

# Create list of spatial detail arguments to iterate through and pass to spatial detail parameter
spatial_detail_list = ['5', '10', '15', '20']

# Create list of minimum segment size arguments to iterate through and pass to maximum segment size parameter
min_segment_size_list = ['10', '20', '30']

# Create list of band selection arguments to iterate through and pass to band indexes parameter
bands_indexes_dictionary = {'2 3 7': '237', '3 7 9': '379'}
band_indexes_list = list(bands_indexes_dictionary.keys())

# Create list of all parameters iterating through in Segment Mean Shift function
parameters_master_list = [spectral_detail_list, spatial_detail_list, min_segment_size_list, band_indexes_list]

# Create one master list of tuples, each of which is a unique combination of the four individual segmentation parameter lists unpacked
parameters_combination_list = list(itertools.product(*parameters_master_list))

# 3. Generate function to iterate through the following layers: segmentation, classifier, and classifier attributes 

fields_subset_name = os.path.basename(fields_subset).rsplit(sep = '_', maxsplit = 1)[0]

def iterate_segmentation_training(raster_to_segment, spectral, spatial, size, bands):
    
    # Generate segmented raster
    #segmented_raster = SegmentMeanShift(in_raster = raster_to_segment, spectral_detail = spectral, spatial_detail = spatial, min_segment_size = size, band_indexes = bands)
    
    #segmented_raster_name = os.path.basename(raster_to_segment).split(sep = '.', maxsplit = 1)[0]

    #region_time = training_subset_name.rsplit(sep = '_', maxsplit = 1)[0]

    segment_attributes_string = str(spectral) + '_' + str(spatial) + '_' + str(size) + '_' + bands_indexes_dictionary[bands]
    print(segment_attributes_string) 
    output_segmented_raster_name = fields_subset_name + '_' + segment_attributes_string + '.tif'
    print(output_segmented_raster_name)
    output_segmented_raster = os.path.join(img_path, output_segmented_raster_name)
    print(output_segmented_raster)
    
    # Save segmented raster
    #segmented_raster.save(output_training_raster)
    
    # Polygon to raster
    # = region_time + '_' + parameters_concatenated
    #segmented_polygons = os.path.join(gdb_path, segmented_polygons_name)
    
    #arcpy.conversion.RasterToPolygon(in_raster = segmented_raster, out_polygon_features = segmented_polygons, simplify = 'NO_SIMPLIFY', create_multipart_features = 'SINGLE_OUTER_PART')
    
# Iterate through each unique segmentation combinations 
#for s in unique_segment_attributes_list:
    
# Iterate through each of the three machine learning classifiers 

# Iterate through each unique OBIA classifier attribute combinations


# Create all possible combinations (based on given lists) of segmentations for Field Borders Subset Raster
for i in parameters_combination_list:
    iterate_segmentation_training(fields_subset, *i)

# Create all possible combinations (based on given lists) of segmentations for Training Fields Subset Raster 
for i in parameters_combination_list:
    iterate_segmentation_training(training_subset, *i)
    
#----------------------------------------------------------------------------------------------
    
#2 Train classifier


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
# Add band selection as parameter
# Add OBIA attributes as drop down list multi-value parameter 


