# Merges OSMM tiles and splits into LADs
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

out_gdb = r"D:\cenv0389\OxCamArc\OSMM.gdb"
LAD_gdb = r"D:\cenv0389\OxCamArc\OSMM_update.gdb"
tile_folder = r"D:\cenv0389\OxCamArc\OSMM_update"
LAD_table = r"D:\cenv0389\OxCamArc\Arc_LADs_sort.shp"
arcpy.env.workspace = tile_folder

collate_tiles = False
merge_tiles = False
split_LADs = True

if collate_tiles:
    folders = arcpy.ListFiles()
    i = 0
    for folder in folders:
        print("Folder " + folder)
        arcpy.env.workspace = os.path.join(tile_folder, folder)
        subfolders = arcpy.ListFiles("mastermap*")
        for subfolder in subfolders:
            print ("  Subfolder " + subfolder)
            arcpy.env.workspace = os.path.join(tile_folder, folder, subfolder)
            in_gdb_list = arcpy.ListFiles("*.gdb")
            in_gdb = in_gdb_list[0]
            print ("    gdb " + in_gdb)
            arcpy.env.workspace = in_gdb
            i = i + 1
            out_fc = os.path.join(out_gdb, "OSMM_tile_" + folder)
            print ("    Copying to " + out_fc)
            arcpy.CopyFeatures_management("TopographicArea", out_fc)

if merge_tiles:
    print ("Merging tiles")
    arcpy.env.workspace = out_gdb
    in_fcs = arcpy.ListFeatureClasses()
    arcpy.Merge_management(in_fcs, "OSMM_Arc_update")
    print(''.join(["## Finished merge on : ", time.ctime()]))

# Split into LADS
# ------------------
if split_LADs:

    LAD_names = []
    LADs = arcpy.SearchCursor(LAD_table)
    # Or use this line to repeat for selected LADs only...
    # LADs = ["SouthOxfordshire", "Oxford", "Wycombe"]
    arcpy.env.workspace = out_gdb

    for LAD in LADs:
        LAD_full_name = LAD.getValue("desc_")
        LAD_name = LAD_full_name.replace(" ","")
        LAD_names.append(LAD_name)
        print("Clipping " + LAD_name)
        arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
        arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause="desc_ = '" + LAD_full_name + "'")
        out_file = os.path.join(LAD_gdb, "OSMM_" + LAD_name)
        arcpy.Clip_analysis("OSMM_Arc_update", "LAD_lyr", out_file)
        arcpy.Delete_management("sel_lyr")
        arcpy.DeleteIdentical_management(out_file, ["Shape"])
        MyFunctions.check_and_repair(out_file)
        print(''.join(["## Finished on : ", time.ctime()]))

exit()

