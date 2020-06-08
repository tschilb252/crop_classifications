
###############################################################################################
###############################################################################################

# Name:             0.00_Create_Directories_Projects_and_Geodatabases_for_Whole_Year.py
# Author:           Kelly Meehan, USBR
# Created:          20190528
# Updated:          20200607 
# Version:          Created using Python 3.6.8 

# Requires:         ArcGIS Pro 

# Notes:            This script is intended to be used for a Script Tool within ArcGIS Pro; it is not intended as a stand-alone script.
#                   User should have template .aprx (e.g. Classification_Project_Template.aprx) and ReadMe files (e.g. ReadMe.txt) for duplication.                

# Description:      This tool creates new Classification Year Directory, cyYYYY;
#                   creates sub-directories, geodatabases, and .aprx files within the newly created year directory; 
#                   for each .aprx, creates database and folder connections and assign their defaults 
        
#----------------------------------------------------------------------------------------------

# Tool setup:       The script tool's properties can be set as follows: 
#
#                      Parameters tab:    
#                           Year                            Raster Layer (Data Type) > Required (Type) > Input (Direction)                  
#                           ArcGIS Pro Project Template     File (Data Type) > Required (Type) > Input (Direction)
#                           Read MeTemplate                 File (Data Type) > Required (Type) > Input (Direction)                    
#                           Output Directory                Workspace (Data Type) > Required (Type) > Input (Direction)                    
#                           Number of Time periods          Long (Data Type) > Required (Type) > Input (Direction)                    
#                           Regions                         String-Multiple Values (Data Type) > Required (Type) > Input (Direction)
#                           Subfolders                      String-Multiple Values (Data Type) > Required (Type) > Input (Direction) 
#
#                       Validation tab:

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

#     def updateMessages(self):
#         """Modify the messages created by internal validation for each tool
#         parameter. This method is called after internal validation."""
#         if self.params[0].value:
#             year_value = self.params[0].value
#             if len(year_value) !=4 or not year_value.isdigit():
#                 self.params[0].setErrorMessage('{0} is not an appropriate value to pass to Year parameter. Please provide a four digit integer'.format(year_value))
#             if self.params[3].value:
#                 root_path = self.params[3].value.value
#                 if os.path.exists(os.path.join(root_path, 'cy' + year_value)):
#                     self.params[0].setErrorMessage('Directory for this year already exists an will not be overwritten; please either change year or root directory.')

###############################################################################################
###############################################################################################

# This script will:

# 0. Set-up
# 1. Create New Year Directory for year within root directory (if does not already exist)
# 2. Create all sub-directories, geodatabases, and .aprx files; for each .aprx, create database and folder connections and assign their defaults 

# Example of directories, projects, readMe, and geodatabases created with this tool (if run for 2017 as an example)
# Please note though only T1 and its CVWD child directory are expanded below, the same pattern carries throughout

# ~/cy2017    
    # T1_2017
      # CVWD_T1_2017
        # covs_CVWD_T1_2017
        # docs_CVWD_T1_2017
        # img_CVWD_T1_2017 
        # sig_CVWD_T1_2017
        # CVWD_T1_2017.aprx
        # CVWD_T1_2017.gdb
        # ReadMe_CVWD_T1_2017.docx
      # IID_2017 
      # L12WM_2017
      # MID1_2017
      # MID2_2017
      # TOP_2017
    # T2_2017
    # T3_2017
    # T4_2017
    # T5_2017

#----------------------------------------------------------------------------------------------

# 0. Set up

# 0.0 Install necessary packages
import arcpy, os, shutil

# 0.1 Assign variables to tool parameters and run checks on values passed

# User specifies year of analysis
year = arcpy.GetParameterAsText(0) # Tool parameter set as string

# User specifies ArcGIS project file (.aprx) to serve as a template
arc_project = arcpy.GetParameterAsText(1)

# User specifies ReadMe Word document (.docx) to serve as temlapte
read_me_template = arcpy.GetParameterAsText(2)

# User specifies root directory where New Year Directory should be created
root_directory= arcpy.GetParameterAsText(3)

# User specifies number of time periods for which directories will be generated within New Year Directory
number_time_periods = arcpy.GetParameterAsText(4)

# User specifies names of regions for which region directories will be generated within each time period directory:
region_directory_list = arcpy.GetParameterAsText(5).split(';')

# User specifies names of subfolders for which region directories will be generated within each region directory:
subfolder_directory_list = arcpy.GetParameterAsText(6).split(';')

# 0.2 Set environment settings

# Set overwrite permissions to false; otherwise a whole year's analysis could be overwritten
arcpy.env.overwriteOutput = False

#----------------------------------------------------------------------------------------------

# 1. Create New Year Directory for year within root directory (if does not already exist)

new_year_directory = os.path.join(root_directory, 'cy' + year)

if not os.path.exists(new_year_directory):
    os.makedirs(new_year_directory)
    arcpy.AddMessage('Generated directory:' + new_year_directory)

#----------------------------------------------------------------------------------------------

# 2. Create all sub-directories, geodatabases, and .aprx files within the newly created year directory; set default geodatabase and folder connection for each .aprx

# Instantiate ArcGISProject object and assign variable aprx to it
aprx = arcpy.mp.ArcGISProject(arc_project)
arcpy.AddMessage('Using ' + arc_project + ' as template ArcGIS Pro project')

# Create time-period directories; within each create region folders ; within each create subfolder, geodatabase, and .aprx (with assigned default geodatabase and folder connections)

# Gerenate range for time periods
outer_range = int(number_time_periods) + 1
for t in range (1, outer_range):
    # Create new directory for time-periods T1 - T*
    year_time = 'T' + str(t) + '_' + year 
    time_directory_name = year_time
    time_directory = os.path.join(new_year_directory, time_directory_name)  
    os.makedirs(time_directory)
    arcpy.AddMessage('Created time-period folder: ' + time_directory_name)  
    
    # Loop through regions
    for r in region_directory_list:
        # Create six directories within each T* directory
        year_time_region = str(r) + '_' + year_time 
        region_directory = os.path.join(time_directory, year_time_region)
        os.makedirs(region_directory)
        arcpy.AddMessage('Creatied region folder: ' + year_time_region)
        
        # Create associated copy of .aprx template for region
        aprx_copy_name = year_time_region + '.aprx'
        aprx_copy_path = os.path.join(region_directory, aprx_copy_name)
        aprx_copy = aprx.saveACopy(aprx_copy_path)
        # NOTE: aprx_copy in lieu of aprx_new will not work as the saveACopy method creates a new output project file, but the project variable continues to reference the original ArcGISProject object
        aprx_new = arcpy.mp.ArcGISProject(aprx_copy_path)  
        arcpy.AddMessage('Created ArcGIS Pro project: ' + aprx_copy_name)
        
        # Create file geodatabase for each region directory 
        geodatabase_name = year_time_region + '.gdb'
        geodatabase_path = os.path.join(region_directory, geodatabase_name)
        arcpy.CreateFileGDB_management(out_folder_path = region_directory, out_name = geodatabase_name)
        
        # Set resultant file geodatabase as default
        aprx_new.defaultGeodatabase = geodatabase_path
        
        # Set default folder for each project 
        aprx_new.homeFolder = region_directory
        
        # NOTE: you must save project, otherwise changes will be lost (https://gis.stackexchange.com/questions/325631/dynamically-set-default-file-geodatabase-to-newly-created-one-in-for-loop-with-a)
        aprx_new.save()
        
        # Make copy of Classification_Read_Me_Template_2017.docx
        read_me_copy_name = 'ReadMe_' + year_time_region + '.docx'
        read_me_copy = os.path.join(region_directory, read_me_copy_name)
        shutil.copyfile(read_me_template, read_me_copy)

        # Loop through sub-directory names (covs, docs, img, sig)
        for s in subfolder_directory_list:
            # Within each region directory, create four child directories
            subfolder_directory_name = str(s) + '_' + year_time_region 
            subfolder_directory = os.path.join(region_directory, subfolder_directory_name)
            os.makedirs(subfolder_directory)
            arcpy.AddMessage('Created sub folder directory: ' + subfolder_directory_name)


