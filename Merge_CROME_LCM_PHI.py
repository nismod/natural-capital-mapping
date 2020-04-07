# Starts from OS Mastermap base map and:
# 1. Assigns CEH Landcover map (LCM) definition of either Arable or Improved grassland to agricultural land polygons
# 2. Assigns Rural Payments Agency CROME Crop map data (input must be dissolved by land use code and joined to description
# and simplified description (Arable, Improved grassland, Short-rotation coppice)
# 3. Assigns Natural England Priority Habitat data.
# Set up to loop through a set of Local Authority Districts
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

region = "Oxon"
# region = "Arc"

method = "HLU"
# method = "LCM_PHI"

if method == "LCM_PHI":
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    if region == "Arc":
        LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire"]
        Hab_field = "Interpreted_habitat"
    elif region == "Oxon":
        LADs_included = ["Oxfordshire"]
        Hab_field = "Interpreted_Habitat"
    data_gdb = os.path.join(folder, "Data\Data.gdb")
    LAD_table = os.path.join(data_gdb, "Arc_LADs")
    CROME_data = os.path.join(data_gdb, "CROME_Arc_dissolve")
elif region == "Oxon" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\Oxon_county\Data"
    data_gdb = os.path.join(folder, "Data.gdb")
    LAD_table = os.path.join(folder, "Data.gdb", "Oxon_LADs")
    CROME_data = os.path.join(data_gdb, "CROME_Oxon_dissolve")
    Hab_field = "BAP_Habitat"
else:
    print("ERROR: you cannot combine region " + region + " with method " + method)
    exit()

LAD_names = []
needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab"]

# What method are we using to create the base map? Merge or intersect? This affects the processing stages used.
# merge_or_intersect = "intersect"
merge_or_intersect = "merge"

# Which stages of the code do we want to run? Depends on whether we are using merge or intersect to create the base map,
# as the merge is a two-stage process in which this script is called twice. Also useful for debugging or updates.
if merge_or_intersect == "intersect":
    process_LCM = False
    process_CROME = True
    process_PHI = True
    delete_landform = False
    intersect_PHI = False
    interpret_PHI = True
    out_fc = "OSMM_LCM_PHI_intersect"
elif merge_or_intersect == "merge":
    # Change step = 1 to step = 2 after running Merge_into_base_map to merge OSMM_LCM with PHI
    step = 2
    if step == 1:
        process_LCM = True
        process_CROME = True
        process_PHI = True
        delete_landform = True
        intersect_PHI = False
        interpret_PHI = False
    elif step == 2:
        process_LCM = False
        process_CROME = False
        process_PHI = True
        delete_landform = False
        intersect_PHI = False
        interpret_PHI = True
    out_fc = "OSMM_LCM_PHI_merge"

arcpy.env.workspace = data_gdb

LADs = arcpy.SearchCursor(os.path.join(data_gdb, LAD_table))
for LAD in LADs:
    LAD_full_name = LAD.getValue("desc_")
    LAD_county = LAD.getValue("county")
    if LAD_county in LADs_included:
        LAD_name = LAD_full_name.replace(" ", "")
        LAD_names.append(LAD_name)

# Now process each LAD gdb
# Use CEH LCM to determine whether OSMM 'Agricultural land' is arable or improved grassland.
if process_LCM:
    for LAD in LAD_names:
        print ("Processing " + LAD)
        arcpy.env.workspace = os.path.join(folder, LAD + ".gdb")
        print("Copying OSMM to OSMM_LCM")
        arcpy.CopyFeatures_management("OSMM", "OSMM_LCM")
        print ("Adding LCM farmland interpretation to " + LAD)
        MyFunctions.delete_fields("OSMM_LCM", needed_fields, "")
        print ("  Adding habitat fields")
        MyFunctions.check_and_add_field("OSMM_LCM", "LCM_farmland", "TEXT", 100)
        MyFunctions.check_and_add_field("OSMM_LCM", Hab_field, "TEXT", 100)
        arcpy.CalculateField_management("OSMM_LCM", Hab_field, "!OSMM_hab!", "PYTHON_9.3")

        print ("  Identifying arable land")
        arcpy.MakeFeatureLayer_management("OSMM_LCM", "ag_lyr")
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause="OSMM_hab = 'Agricultural land' OR OSMM_hab = 'Natural surface'")
        arcpy.SelectLayerByLocation_management("ag_lyr", "HAVE_THEIR_CENTER_IN", "LCM_arable", selection_type="SUBSET_SELECTION")
        arcpy.CalculateField_management("ag_lyr","LCM_farmland", "'Arable'", "PYTHON_9.3")
        arcpy.CalculateField_management("ag_lyr", Hab_field, "'Arable'", "PYTHON_9.3")
        arcpy.Delete_management("ag_lyr")

        print ("  Identifying improved grassland")
        arcpy.MakeFeatureLayer_management("OSMM_LCM", "ag_lyr2")
        arcpy.SelectLayerByAttribute_management("ag_lyr2", where_clause="OSMM_hab = 'Agricultural land' OR OSMM_hab = 'Natural surface'")
        arcpy.SelectLayerByLocation_management("ag_lyr2", "HAVE_THEIR_CENTER_IN", "LCM_improved_grassland",
                                               selection_type="SUBSET_SELECTION")
        arcpy.CalculateField_management("ag_lyr2", "LCM_farmland", "'Improved grassland'", "PYTHON_9.3")
        arcpy.Delete_management("ag_lyr2")

        # Set interpreted habitat to Improved grassland if this is 'agricultural land'or Amenity grassland if this is 'Natural surface'
        # unless it is railside (do not want to flag this as amenity grassland because it is not generally accessible)
        expression = "LCM_farmland = 'Improved grassland' AND " + Hab_field + " = 'Agricultural land'"
        MyFunctions.select_and_copy("OSMM_LCM", Hab_field, expression, "'Improved grassland'")
        expression = "LCM_farmland = 'Improved grassland' AND " + Hab_field + " = 'Natural surface' AND DescriptiveGroup <> 'Rail'"
        MyFunctions.select_and_copy("OSMM_LCM", Hab_field, expression, "'Amenity grassland'")

        print(''.join(["## Finished on : ", time.ctime()]))

# Add crop type from CROME map, but only for agricultural land. This is probably better data then LCM and is freely available.
# This assumes we are adding CROME after adding LCM (so the Interpreted habitat field is already added and populated in the process_LCM
# step above), but in fact it is probably best just to use CROME (once we have tested vs LCM), so need to modify this step to include
# adding the interpreted habitat field
if process_CROME:
    for LAD in LAD_names:
        print ("Processing " + LAD)
        arcpy.env.workspace = os.path.join(folder, LAD + ".gdb")
        in_map = "OSMM_LCM"
        out_map = in_map + "_CROME"
        print("Copying " + in_map + " to " + out_map)
        arcpy.CopyFeatures_management(in_map, out_map)
        print ("Adding CROME farmland interpretation to " + LAD)
        print ("  Adding habitat fields")
        MyFunctions.check_and_add_field(out_map, "CROME_farmland", "TEXT", 50)

        print("      Copying OBJECTID for base map")
        MyFunctions.check_and_add_field(out_map, "BaseID_CROME", "LONG", 0)
        arcpy.CalculateField_management(out_map, "BaseID_CROME", "!OBJECTID!", "PYTHON_9.3")

        print ("  Identifying farmland")
        arcpy.MakeFeatureLayer_management(out_map, "ag_lyr")
        expression = "Interpreted_hab IN ('Agricultural land', 'Natural surface') OR Interpreted_hab LIKE 'Arable%'"
        expression = expression + " OR Interpreted_hab LIKE 'Improved grassland%'"
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause=expression)

        print("      Calculating percentage of farmland features within CROME polygons")
        arcpy.TabulateIntersection_analysis(CROME_data, ["LUCODE", "Land Use Description", "field", "Shape_Area"],
                                            "ag_lyr", "CROME_TI", ["BaseID_CROME", Hab_field, "Shape_Area"])

        print("      Sorting TI table by size so that larger intersections are first in the list")
        arcpy.Sort_management("CROME_TI", "CROME_TI_sort", [["AREA", "ASCENDING"]])

        print ("      Adding fields for CROME data")
        MyFunctions.check_and_add_field(out_map, "CROME_desc", "TEXT", 50)
        MyFunctions.check_and_add_field(out_map, "CROME_simple", "TEXT", 30)

        print ("      Joining CROME info for base map polygons that are >50% inside CROME polygons")
        arcpy.AddJoin_management("ag_lyr", "BaseID_CROME", "CROME_TI_sort", "BaseID_CROME", "KEEP_ALL")

        print("      Copying CROME data")
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause="CROME_TI_sort.PERCENTAGE > 50")
        arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_desc", "!CROME_TI_sort.Land Use Description!", "PYTHON_9.3")
        arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_simple", "!CROME_TI_sort.field!", "PYTHON_9.3")

        # Remove the join
        arcpy.RemoveJoin_management("ag_lyr", "CROME_TI_sort")
        arcpy.Delete_management("ag_lyr")

        # Set interpreted habitat to Improved grassland if this is 'agricultural land'or Amenity grassland if this is 'Natural surface'
        # unless it is railside (do not want to flag this as amenity grassland because it is not generally accessible)
        expression = "CROME_desc IN ('Grass', 'Fallow Land') AND " + Hab_field + " IN ('Agricultural land', 'Arable')"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland'")
        expression = "CROME_desc IN ('Grass', 'Fallow Land') AND " + Hab_field + " = 'Natural surface' AND DescriptiveGroup <> 'Rail'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Amenity grassland'")
        expression = "CROME_desc = 'Arable' AND " + Hab_field + " = 'Agricultural land'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")
        expression = "CROME_desc = 'Short Rotation Coppice' AND " + Hab_field + " = 'Agricultural land'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")

        print(''.join(["## Finished on : ", time.ctime()]))

if process_PHI:
    for LAD in LAD_names:
        arcpy.env.workspace = os.path.join(folder, LAD + ".gdb")

        if delete_landform:
            print("   Deleting overlapping 'Landform' and 'Pylon' from OSMM for " + LAD)
            arcpy.MakeFeatureLayer_management("OSMM_LCM", "OSMM_layer")
            expression = "DescriptiveGroup LIKE '%Landform%' OR DescriptiveTerm IN ('Cliff','Slope','Pylon')"
            arcpy.SelectLayerByAttribute_management("OSMM_layer", where_clause=expression)
            arcpy.DeleteFeatures_management("OSMM_layer")
            arcpy.Delete_management("OSMM_layer")

        if intersect_PHI:
            print ("Intersecting " + LAD)
            arcpy.Identity_analysis("OSMM_LCM", "PHI", out_fc, "NO_FID")

        if interpret_PHI:
            print ("Interpreting " + LAD)
            # Copy PHI habitat across, but not for manmade, gardens, water, unidentified PHI, wood pasture or OMHD (dealt with later)
            expression = "Make = 'Natural' AND DescriptiveGroup NOT LIKE '%water%' AND DescriptiveGroup NOT LIKE '%Water%' AND " \
                          "OSMM_hab <> 'Roadside - unknown surface' AND OSMM_hab <> 'Track' AND OSMM_hab <> 'Standing water' "
            expression2 = expression +  " AND PHI IS NOT NULL AND PHI <> '' AND PHI NOT LIKE 'No main%' AND " \
                                        "PHI NOT LIKE 'Wood-pasture%' AND PHI NOT LIKE 'Open Mosaic%'"
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", expression2, "!PHI!")

            # Correction for traditional orchards in large gardens
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "PHI = 'Traditional orchard' AND OSMM_hab = 'Garden'",
                                        "'Traditional orchards'")

            # Other corrections / consolidations
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat = 'Deciduous woodland'",
                                        "'Broadleaved woodland - semi-natural'")
            expression3 = "Interpreted_habitat LIKE '%grazing marsh%' OR Interpreted_habitat LIKE 'Purple moor grass%'"
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", expression3, "'Marshy grassland'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat LIKE '%semi-improved grassland%'",
                                        "'Semi-natural grassland'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat LIKE '%meadow%'",
                                        "'Neutral grassland'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat = 'Traditional orchard'",
                                        "'Traditional orchards'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat LIKE '%alcareous%'",
                                        "'Calcareous grassland'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat = 'Lowland heathland'",
                                        "'Heathland'")
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", "Interpreted_habitat = 'Reedbeds'",
                                        "'Reedbed'")


            # Copy over OMHD only if the habitat is fairly generic (OMHD dataset covers areas of mixed habitats)
            expression5 = "(OMHD IS NOT NULL AND OMHD <> '') AND (Interpreted_habitat IN ('Arable', 'Agricultural land'," \
                          " 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land', 'Bare ground', 'Landfill (inactive)'," \
                          "'Quarry or spoil (disused)', 'Sealed surface'))"
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", expression5, "'Open mosaic habitats'")

            # Copy over Wood pasture only if the habitat is fairly generic (WPP dataset covers very large areas of mixed habitats)
            expression4 = "(WPP IS NOT NULL AND WPP <> '') AND (Interpreted_habitat IN ('Arable', 'Agricultural land', " \
                          "'Improved grassland', 'Natural surface', 'Cultivated/disturbed land') OR " \
                          "Interpreted_habitat LIKE 'Scattered%' OR Interpreted_habitat LIKE 'Semi-natural grassland%')"
            MyFunctions.select_and_copy(out_fc, "Interpreted_habitat", expression4, "'Parkland and scattered trees - broadleaved'")

            print(''.join(["## Finished on : ", time.ctime()]))

if merge_or_intersect == "merge":
    if step == 1:
        print ("Now run Merge_into_Base_Map.py to merge OSMM_LCM with PHI, then set step = 2 in this code and re-run to interpret habitats")
exit()