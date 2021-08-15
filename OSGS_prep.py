# Merges OSMM or OSMM greenspace tiles from different folders and splits into LADs
# This version expects one level of sub-folders each containing a list of shapefiles (tiles)
# In the end I gave up on this and just copied files into one directory by hand, as the
# main pre-processing is done in join_greenspace.py
# -----------------------------------------------------------------------------------------------------------------

import time
import arcpy
import os
import MyFunctions

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

# Location of the input tiles
# tile_folder = r"D:\cenv0389\OxCamArc\OSMM_update"
# tile_folder = r"D:\cenv0389\Oxon_GIS\GIS_data\2020_OSMM"
tile_folder = r"M:\urban_development_natural_capital\osmm_greenspace"

# Template for the feature classes or shapefiles containing the tiled data (can be gdb or shapefile)
tile_type = "shp"
fc_template = "*.shp"
# If input is in gdbs, enter the name of the target feature class here (assuming it is always the same)
in_fc_name = ""

# Define location for output gdb, which should be created in advance
# out_gdb = r"D:\cenv0389\OxCamArc\OSMM.gdb"
# out_gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\OSMM_Aug2020.gdb"
# out_gdb = r"M:\urban_development_natural_capital\osmm-northern-powerhouse\OSMM_Feb2021.gdb"
out_gdb = r"M:\urban_development_natural_capital\osmm_greenspace\OSGS_Feb2021.gdb"

tile_prefix = "OSMM_GS__"

# Name for merged dataset containing all tiles
# merged_fc = "OSMM_Oxon_Aug2020"
merged_fc = "OSMM_GS_NP"

# Define gdb to contain the output split into LADs
# LAD_gdb = r"D:\cenv0389\OxCamArc\OSMM_update.gdb"
LAD_gdb = out_gdb

LAD_table = r"D:\cenv0389\OxCamArc\Arc_LADs_sort.shp"
LAD_table = r"M:\urban_development_natural_capital\data.gdb\LADs"
LAD_name_field = "LAD_name_simple"
LAD_out_prefix = "OSMM_GS_"

# Or can just clip to a single boundary
boundary = r"D:\cenv0389\Oxon_GIS\GIS_data\Oxfordshire.shp"

collate_tiles = True
merge_tiles = True
# Split into LADs OR trim to county boundary
split_LADs = True
trim_county = False
delete_overlaps = True

arcpy.env.workspace = tile_folder

if collate_tiles:
    # Loop through all the subfolders in the main folder and add the name of the relevant feature classes to the merge list
    merge_list =[]
    folders = arcpy.ListFiles()
    for folder in folders:
        print("Folder " + folder)
        arcpy.env.workspace = os.path.join(tile_folder, folder)
        in_file_list = arcpy.ListFiles(fc_template)
        print str(len(in_file_list)) + " files matching the template found in this folder"
        for in_file in in_file_list:
            print ("    Tile fc name is " + in_file)
            # this won't work for gdbs yet - need to split outside this loop
            if tile_type == "gdb":
                arcpy.env.workspace = in_file
                # in_fc = in_fc_name
                # full_fc_path = os.path.join(tile_folder, folder, in_fc)
                # out_fc = os.path.join(out_gdb, tile_prefix + folder)
            elif tile_type == "shp":
                in_fc = in_file
                full_fc_path = os.path.join(tile_folder, folder, in_fc)
                # out_name = os.path.splitext(in_fc)[0]
                # out_fc = os.path.join(out_gdb, tile_prefix + out_name)

            # print ("    Copying to " + out_fc)
            # arcpy.CopyFeatures_management(in_fc, out_fc)

            print "Appending feature class " + full_fc_path + " to merge list"
            merge_list.append(full_fc_path)

if merge_tiles:
    print ("Merging tiles")
    arcpy.env.workspace = out_gdb
    # in_fcs = arcpy.ListFeatureClasses()
    print '\n'.join(merge_list)
    in_fcs = merge_list
    arcpy.Merge_management(in_fcs, merged_fc)
    print(''.join(["## Finished merge on : ", time.ctime()]))

# Split into LADS
# ------------------
if split_LADs:

    arcpy.env.workspace = out_gdb
    LAD_names = []
    LADs = arcpy.SearchCursor(LAD_table)
    # Use this line to select certain LADs only, otherwise comment out... doesn't work yet though, fails to match
    # Target_LADs = ["Leeds"]

    for LAD in LADs:

        LAD_full_name = LAD.getValue(LAD_name_field)
        # if LAD_full_name in Target_LADs:
        if LAD_full_name == "Leeds":
            LAD_name = LAD_full_name.replace(" ","")
            LAD_names.append(LAD_name)
            print("Clipping " + LAD_name)
            arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
            arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause= LAD_name_field + " = '" + LAD_full_name + "'")
            out_file = os.path.join(LAD_gdb, LAD_out_prefix + LAD_name)
            arcpy.Clip_analysis(merged_fc, "LAD_lyr", out_file)
            arcpy.Delete_management("sel_lyr")

if trim_county:
    print("Clipping to " + boundary)
    arcpy.MakeFeatureLayer_management(merged_fc, "lyr")
    arcpy.SelectLayerByLocation_management("lyr", "INTERSECT", boundary)
    out_file = os.path.join(out_gdb, merged_fc + "_clip")
    arcpy.Clip_analysis("lyr", boundary, out_file)
    arcpy.Delete_management("lyr")

if delete_overlaps:
    arcpy.DeleteIdentical_management(out_file, ["Shape"])
    MyFunctions.check_and_repair(out_file)
    print(''.join(["## Finished on : ", time.ctime()]))

exit()