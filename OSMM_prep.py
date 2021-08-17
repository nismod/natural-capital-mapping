# Merges OSMM tiles from different folders and splits into LADs
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
tile_folder = r"M:\urban_development_natural_capital\osmm_northern_powerhouse"

# Target feature class name
fc_name = "TopographicArea"
# Typo in name!
# fc_name = "Topgraphicarea"

# Define location for output gdb, which should be created in advance
# OSMM_out_gdb = r"D:\cenv0389\OxCamArc\OSMM.gdb"
OSMM_out_gdb = r"M:\urban_development_natural_capital\osmm_northern_powerhouse\OSMM_large_areas.gdb"

# Either copy the output (OSMM split into LADs) into a single gdb (LAD_gdb), or copy into separate gdbs for each LAD, in LAD_gdb_folder
separate_LAD_gdbs = True
LAD_gdb = r"D:\cenv0389\OxCamArc\OSMM_update.gdb"
LAD_gdb_folder = r"M:\urban_development_natural_capital\LADs"

# new_fc = "OSMM_Oxon_Aug2020"
new_fc = "OSMM_North_NP"
OSMM_fc = new_fc

LAD_table = r"M:\urban_development_natural_capital\data.gdb\LADs"
LAD_name_field = "LAD_name_simple"
County_name_field = "County"
# LADs_included = ["Northumberland", "Allerdale", "Carlisle", "Newcastle upon Tyne", "North Tyneside", "South Tyneside", "Sunderland",
#                 "Gateshead", "County Durham", "Copeland", "Darlington", "Stockton-on-Tees", "Hartlepool", "Middlesbrough",
#                 "Redcar and Cleveland"]
LADs_included = ["Northumberland", "Carlisle", "Copeland", "Hartlepool", "Allerdale"]
# LADs_included = ["Pendle", "Burnley", "Rossendale", "Rochdale", "Manchester", "Trafford", "Salford", "Bury", "Hyndburn",
#                  "Ribble Valley", "Lancaster", "Wyre", "Barrow-in-Furness", "Blackpool", "Fylde", "Preston",
#                  "South Ribble", "Blackburn with Darwen". "Chorley", "Wigan", "West Lancashire", "Bolton", "Warrington",
#                  "Halton", "St Helens", "Knowsley", "Liverpool", "Wirral", "Sefton", "Cheshire West and Chester"]
# LADs_included = ["North Lincolnshire", "North East Lincolnshire", "East Riding of Yorkshire", "York", "Selby", "Wakefield",
#                  "Barnsley", "Doncaster", "Rotherham", "Sheffield"]

# boundary = r"D:\cenv0389\Oxon_GIS\GIS_data\Oxfordshire.shp"
boundary = r"M:\urban_development_natural_capital\data.gdb\NP_boundary"

collate_tiles = False
merge_tiles = False
' Split into LADs OR trim to county boundary'
split_LADs = True
trim_county = False
delete_overlaps = True

if collate_tiles:
    arcpy.env.workspace = tile_folder
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
            out_fc = os.path.join(OSMM_out_gdb, "OSMM_tile_" + folder)
            print ("    Copying to " + out_fc)
            arcpy.CopyFeatures_management(fc_name, out_fc)

if merge_tiles:
    print ("Merging tiles")
    arcpy.env.workspace = OSMM_out_gdb
    in_fcs = arcpy.ListFeatureClasses()
    arcpy.Merge_management(in_fcs, new_fc)
    print(''.join(["## Finished merge on : ", time.ctime()]))

# Split into LADS
# ------------------
if split_LADs:

    LAD_names = []
    LADs = arcpy.SearchCursor(LAD_table)

    arcpy.env.workspace = OSMM_out_gdb

    for LAD in LADs:
        LAD_full_name = LAD.getValue(LAD_name_field)
        if LAD_full_name in LADs_included:
            LAD_name = LAD_full_name.replace(" ","")
            LAD_names.append(LAD_name)

            print("Clipping OSMM for " + LAD_name)
            arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
            arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause= LAD_name_field + "= '" + LAD_full_name + "'")
            if separate_LAD_gdbs:
                # Option for copying direct to LAD gdb
                out_file = os.path.join(LAD_gdb_folder, LAD_name + ".gdb", "OSMM")
            else:
                # Option for copying to a single folder
                out_file = os.path.join(LAD_gdb, "OSMM_" + LAD_name)

            arcpy.Clip_analysis(OSMM_fc, "LAD_lyr", out_file)
            arcpy.Delete_management("sel_lyr")

            if delete_overlaps:
                print "Deleting overlaps"
                arcpy.DeleteIdentical_management(out_file, ["Shape"])
                MyFunctions.check_and_repair(out_file)

            print(''.join(["## Finished ", LAD_full_name, " on : ", time.ctime()]))

if trim_county:
    print("Clipping to " + boundary)
    arcpy.MakeFeatureLayer_management(new_fc, "lyr")
    arcpy.SelectLayerByLocation_management("lyr", "INTERSECT", boundary)
    out_file = os.path.join(OSMM_out_gdb, new_fc + "_clip")
    arcpy.Clip_analysis("lyr", boundary, out_file)
    arcpy.Delete_management("lyr")

    if delete_overlaps:
        print "Deleting overlaps"
        arcpy.DeleteIdentical_management(out_file, ["Shape"])
        MyFunctions.check_and_repair(out_file)

print(''.join(["## Finished on : ", time.ctime()]))

exit()

