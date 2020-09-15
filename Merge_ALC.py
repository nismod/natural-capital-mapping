# Merge Agricultural Land Class with the land dataset
# Pre-process ALC by dissolving on ALC grade and then unioning with itself with no gaps and 1m tolerance
# to remove sliver gaps
# ---------------------------------------------------
import time, arcpy
import os
import  MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

region = "Arc"
# region = "Oxon"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "HLU"

if region == "Oxon" and method == "HLU":
    folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data"
    gdbs = [os.path.join(folder,"Merge_OSMM_HLU_CR_ALC.gdb")]
    base_map_name = "OSMM_HLU_CR"
    out_name = "OSMM_HLU_CR_ALC"
    ALC_data = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Merge_OSMM_HLU_CR_ALC.gdb\ALC_Union"
elif method == "CROME_PHI":
    folder = r"D:\cenv0389\OxCamArc\LADs"
    arcpy.env.workspace = folder
    base_map_name = "OSMM_CROME_PHI"
    out_name = "OSMM_CR_PHI_ALC"
    if region == "Arc":
        gdbs = []
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        #gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
        #gdbs.append(os.path.join(folder, "Chiltern.gdb"))
        ALC_data = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Data.gdb\ALC_diss_union"
    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
        ALC_data = os.path.join(folder, "ALC_Union.shp")

for gdb in gdbs:
    arcpy.env.workspace = gdb
    # Need to define base map here otherwise it keeps repeating the first gdb base map
    base_map = os.path.join(folder, gdb, base_map_name)

    numrows = arcpy.GetCount_management(base_map)
    print ("Processing " + gdb + ". " + base_map_name + " has " + str(numrows) + " rows.")

    print("    Selecting intensive agriculture polygons from land cover layer")
    arcpy.CopyFeatures_management(base_map_name, "noFarmland")
    arcpy.MakeFeatureLayer_management("noFarmland", "farmland_layer")
    expression = "(Interpreted_habitat LIKE 'Arable%' OR Interpreted_habitat = 'Agricultural land' "
    expression = expression + "OR Interpreted_habitat LIKE 'Improved%' OR Interpreted_habitat LIKE '%rchard%')"
    arcpy.SelectLayerByAttribute_management("farmland_layer", where_clause=expression)

    print("    Running Identity")
    out_file = os.path.join(folder, gdb, out_name)
    arcpy.Identity_analysis ("farmland_layer", ALC_data, out_file, "NO_FID")

    print("    Creating no_farmland layer")
    arcpy.DeleteFeatures_management("farmland_layer")

    print("    Appending")
    arcpy.Append_management("noFarmland", out_file, "NO_TEST")

    MyFunctions.check_and_repair((out_file))

exit()