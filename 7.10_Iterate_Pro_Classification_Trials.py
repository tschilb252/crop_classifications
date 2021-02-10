
###############################################################################################
###############################################################################################

# Name:             7.10_Iterate_Pro_Classification_Trials.py 
# Author:           Kelly Meehan, USBR
# Created:          20201216
# Updated:          20200210 
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

import arcpy, itertools, os, numpy, pandas, re
from arcpy.sa import SegmentMeanShift, TrainSupportVectorMachineClassifier, TrainRandomTreesClassifier, TrainMaximumLikelihoodClassifier, ClassifyRaster

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

# 1. Create list of tuples for all combinations of classifier OBIA attributes to iterate through (NOTE: MEAN and SD not included as no auxilary raster used) 

# Create list of all attributes to include, save for color
classifier_attributes = ['COUNT', 'COMPACTNESS', 'RECTANGULARITY']

# Create list of all possible combinations with three attributes
unique_classifier_attributes = []
for l in range(1, len(classifier_attributes)+1):
    for subset in itertools.combinations(classifier_attributes, l):
        unique_classifier_attributes.append(subset)

# Convert list of tuples to list of strings of attributes joined by semicolons
unique_classifier_attributes_list = [';'.join(w) for w in unique_classifier_attributes]

# Add Color attribute to each element in list to ensure it's use in every iteration
unique_classifier_attributes_list = [s + ';COLOR' for s in unique_classifier_attributes_list]
unique_classifier_attributes_list.insert(0, 'COLOR')

#----------------------------------------------------------------------------------------------

# 2. Create list of combinations of segmentation arguments to iterate through
     
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
unique_segmentation_arguments_list = list(itertools.product(*parameters_master_list))

#----------------------------------------------------------------------------------------------

# 3. Generate Segmentation Rasters

segmented_rasters_list = []

# Generate function to iterate through the following layers: segmentation, classifier, and classifier attributes 
def generate_segmentation_rasters(raster_to_segment, spectral, spatial, size, bands):
    
    # Generate segmented raster
    segmented_raster = SegmentMeanShift(in_raster = raster_to_segment, spectral_detail = spectral, spatial_detail = spatial, min_segment_size = size, band_indexes = bands)
    
    #segmented_raster_name = os.path.basename(raster_to_segment).split(sep = '.', maxsplit = 1)[0]

    raster_basename = os.path.basename(raster_to_segment).rsplit(sep = '_', maxsplit = 1)[0]

    segment_attributes_string = str(spectral) + '_' + str(spatial) + '_' + str(size) + '_' + bands_indexes_dictionary[bands]
    output_segmented_raster_name = raster_basename + '_' + segment_attributes_string + '.tif'
    output_segmented_raster = os.path.join(img_path, output_segmented_raster_name)
    
    # Save segmented raster
    segmented_raster.save(output_segmented_raster)
        
    # Add raster to list to iterate through later
    segmented_rasters_list.append(output_segmented_raster)   
    
    # Polygon to raster
    # = region_time + '_' + parameters_concatenated
    #segmented_polygons = os.path.join(gdb_path, segmented_polygons_name)
    
    #arcpy.conversion.RasterToPolygon(in_raster = segmented_raster, out_polygon_features = segmented_polygons, simplify = 'NO_SIMPLIFY', create_multipart_features = 'SINGLE_OUTER_PART')
   
# Create all possible combinations (based on given lists) of segmentations for Field Borders Subset Raster
for i in unique_segmentation_arguments_list:
    generate_segmentation_rasters(fields_subset, *i)

# Create all possible combinations (based on given lists) of segmentations for Training Fields Subset Raster 
for i in unique_segmentation_arguments_list:
    generate_segmentation_rasters(training_subset, *i)
    
#----------------------------------------------------------------------------------------------
    
# 4. Classify Rasters


#REMOVE
#arcpy.env.workspace = img_path
#segmented_rasters_list = arcpy.ListFiles(wild_card = '*MID2_T2_2017_fields_*.tif')    

# Iterate through each unique segmentation combinations 
#for s in unique_segment_attributes_list:
    
# Iterate through each of the three machine learning classifiers 

# Iterate through each unique OBIA classifier attribute combinations

# Create function to run iterations of SVM classification over all unique classifier attributes (called Segment Attributes in Pro Tool GUI)

#classified_rasters_svm = arcpy.ListRasters('*svm*.tif')
#classified_rasters_rt = arcpy.ListRasters('*rt*.tif')
#classified_rasters_ml = arcpy.ListRasters('*ml*.tif')

classified_rasters_svm = []

def iterate_svm_classifer(segmented_raster_classifying, classifier_attributes):
    
    raster_basename = os.path.splitext(segmented_raster_classifying)[0] 

    #REMOVE
    #unique_segmentation_tif = os.path.basename(segmented_raster_classifying).split(sep = '_', maxsplit = 4)[4]
    #unique_segmentation = unique_segmentation_tif.split(sep = '.')[0]
    classifier_attributes_name = classifier_attributes.replace(';', '_')
    
    definition_file_name_svm = raster_basename + '_svm_' + classifier_attributes_name + '.ecd'
    definition_file_svm = os.path.join(img_path, definition_file_name_svm)
     
    # Run training
    TrainSupportVectorMachineClassifier(in_raster = segmented_raster_classifying, in_training_features = training_fields, out_classifier_definition = definition_file_svm, max_samples_per_class = 0, used_attributes = classifier_attributes)
    
    # Run classification
    classified_raster_svm = ClassifyRaster(in_raster = segmented_raster_classifying, in_classifier_definition = definition_file_svm)    
    
    # Save classification output
    classified_raster_name_svm = os.path.splitext(definition_file_svm)[0] + '.tif'
    classified_raster_svm.save(classified_raster_name_svm)
    classified_rasters_svm.append(classified_raster_svm)

# Iterate through segmented rasters and then obia attribute combinations

for s in segmented_rasters_list:
    print(s)
    
    for o in unique_classifier_attributes_list:
        print(o)
        iterate_svm_classifer(segmented_raster_classifying = s, classifier_attributes = o)

#----------------------------------------------------------------------------------------------

# Create function to run iterations of Maximum Likelihood classifier over all unique classifier attributes (called Segment Attributes in Pro Tool GUI)

classified_rasters_ml = []

def iterate_ml_classifier(segmented_raster_classifying, classifier_attributes):
    
    raster_basename = os.path.splitext(segmented_raster_classifying)[0] 

    classifier_attributes_name = classifier_attributes.replace(';', '_')
    
    definition_file_ml = raster_basename + '_ml_' + classifier_attributes_name + '.ecd'
    definition_file_ml = os.path.join(img_path, definition_file_ml)
     
    # Run training
    TrainMaximumLikelihoodClassifier(in_raster = segmented_raster_classifying, in_training_features = training_fields, out_classifier_definition = definition_file_ml, used_attributes = classifier_attributes)
    
    # Run classification
    classified_raster_ml = ClassifyRaster(in_raster = segmented_raster_classifying, in_classifier_definition = definition_file_ml)    
    
    # Save classification output
    classified_raster_name_ml = os.path.splitext(definition_file_ml)[0] + '.tif'
    classified_raster_ml.save(classified_raster_name_ml)
    classified_rasters_ml.append(classified_raster_ml)

    # Create 
# Iterate through segmented rasters and then obia attribute combinations

for l in segmented_rasters_list:
    print(l)
    
    for c in unique_classifier_attributes_list:
        print(c)
        iterate_ml_classifier(segmented_raster_classifying = l, classifier_attributes = c)

# Create function to run iterations of Maximum Likelihood classifier over all unique classifier attributes (called Segment Attributes in Pro Tool GUI)

classified_rasters_rt = []

def iterate_rt_classifier(segmented_raster_classifying, classifier_attributes):
    
    raster_basename = os.path.splitext(segmented_raster_classifying)[0] 

    classifier_attributes_name = classifier_attributes.replace(';', '_')
    
    definition_file_rt = raster_basename + '_rt_' + classifier_attributes_name + '.ecd'
    definition_file_rt = os.path.join(img_path, definition_file_rt)
     
    # Run training
    TrainRandomTreesClassifier(in_raster = segmented_raster_classifying, in_training_features = training_fields, out_classifier_definition = definition_file_rt, used_attributes = classifier_attributes)
    
    # Run classification
    classified_raster_rt = ClassifyRaster(in_raster = segmented_raster_classifying, in_classifier_definition = definition_file_rt)    
    
    # Save classification output
    classified_raster_name_rt = os.path.splitext(definition_file_rt)[0] + '.tif'
    classified_raster_rt.save(classified_raster_name_rt)
    classified_rasters_rt.append(classified_raster_rt)

# Iterate through segmented rasters and then obia attribute combinations

for r in segmented_rasters_list:
    print(r)
    
    for u in unique_classifier_attributes_list:
        print(u)
        iterate_rt_classifier(segmented_raster_classifying = r, classifier_attributes = u)

#----------------------------------------------------------------------------------------------

# Create Accuracy Assessment Points with attribute table field GrndTruth populated with values from Accuracy Assessment Feature Class

accuracy_points_basename = accuracy_fields.rsplit(sep = '_', maxsplit = 2)[0] 
accuracy_points = accuracy_points_basename + '_accuracy_points.shp'
arcpy.sa.CreateAccuracyAssessmentPoints(in_class_data = accuracy_fields, out_points = accuracy_points, target_field = 'GROUND_TRUTH')

# Create empty dataframe to which all accuracy assessment data will be added
df_master_matrix = pandas.DataFrame(columns = ['Accuracy'])

# Create function to add accuracy assessment for each classified raster to master dataframe
def generate_master_accuracy_assessment(classified_raster_list, classifier_string):
    
    for v in classified_raster_list:
        
        # Populate accuracy assessment feature class attribute table field Classified with value from classified raster
        
        raster_basename = os.path.splitext(v)[0] 
        accuracy_assessment_points_name = raster_basename.replace('fields', 'accuracy_assessment')
        accuracy_assessment_points = r'in_memory\accuracy_assessment_points' 
        arcpy.sa.UpdateAccuracyAssessmentPoints(in_class_data = v, in_points = accuracy_points, out_points = accuracy_assessment_points, target_field = 'CLASSIFIED')
        
        # Create Confusion Matrix
        confusion_matrix_table = os.path.join(gdb_path, raster_basename.replace('fields', 'accuracy_assessment'))
        arcpy.sa.ComputeConfusionMatrix(in_accuracy_assessment_points = accuracy_assessment_points, out_confusion_matrix = confusion_matrix_table)
        print('completed confusion')
    
        # Get list of Pro confusion matrix column names
        confusion_matrix_fields = [field.name for field in arcpy.ListFields(dataset = confusion_matrix_table)]
        
        # Create numpy array from confusion matrix    
        array_confusion_matrix = arcpy.da.TableToNumPyArray(in_table = confusion_matrix_table, field_names = confusion_matrix_fields)
           
        # Create dataframe from numpy array
        df_confusion_matrix = pandas.DataFrame(data = array_confusion_matrix)
        
        # Convert ClassValue column to index
        df_confusion_matrix.set_index('ClassValue', inplace = True)
        
        # Extract overall accuracy rate from matrix and add to master dataframe
        df_master_matrix.at[raster_basename, 'Accuracy'] = df_confusion_matrix.loc['P_Accuracy', 'U_Accuracy']
        
        # Add attribute columns distinguishing unique attributes
        
        for index, row in df_master_matrix.iterrows():
            df_master_matrix.loc[index, 'classifier'] = row.name.split('_')[8]
            df_master_matrix.loc[index, 'segmentation_attributes'] = segmentation_attributes = re.search('fields_(.+?)_' + classifier_string, row.name).group(1)
            df_master_matrix.loc[index, 'classifier_attributes'] = row.name.split(classifier_string + '_', 1)[1]     
     
# Run accuracy assessment function for svm rasters
generate_master_accuracy_assessment(classified_raster_list = classified_rasters_svm, classifier_string = 'svm')

# Run accuracy assessment function for rt rasters
generate_master_accuracy_assessment(classified_raster_list = classified_rasters_rt, classifier_string = 'rt')

# Run accuracy assessment function for ml rasters
generate_master_accuracy_assessment(classified_raster_list = classified_rasters_ml, classifier_string = 'ml')

# Export master accuracy assessment dataframe
df_master_matrix.to_csv(path_or_buf = os.path.join(docs_path, 'master_accuracy_asssessment' '.csv'), sep = ',')  

#----------------------------------------------------------------------------------------------


########################################################################################################################


## TTDL
# When converting to tool, allow user to select argument values to pass to segmentation parameter.
# Add if statement to convert to polygon only if *_training_* (fields segmentation stays raster)
# Change names to include training_segments so can be distinguished when searching geodatabase by wildcard training
# Change baseline to region_time
# Change filed_segment_rasters to point to direct file (without needing env.workspace) or have all one function: segmentation -> train -> classification
# Must reorganize so that parameter combinations written first, then segments made and immediately used for classification (instead of making list of segmented rasters later), or just add 'segments' to the name to distinguish from origial raster 
# Add band selection as parameter
# Add OBIA attributes as drop down list multi-value parameter 
# Add classified to name of classified raster in place of _fields

