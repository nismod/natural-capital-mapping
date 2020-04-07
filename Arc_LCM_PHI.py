# Assigns CEH Landcover map (LCM) definition of either Arable or Improved grassland to agricultural land polygons
# for the Arc LADs. Then assigns Priority Habitat.
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

if region == "Arc":
    LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire"]
elif region == "Oxon":
    LADs_included = ["Oxfordshire"]

folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
data_gdb = os.path.join(folder, "Data\Data.gdb")
LAD_table = os.path.join(data_gdb, "Arc_LADs")
needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab"]
LAD_names = []

# Which stages of the code do we want to run? Useful for debugging or updates.
# merge_or_intersect = "intersect"
merge_or_intersect = "merge"
if merge_or_intersect == "intersect":
    process_LCM = False
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
        process_PHI = True
        delete_landform = True
        intersect_PHI = False
        interpret_PHI = False
    elif step == 2:
        process_LCM = False
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

# Now switch to processing each LAD gdb
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
        MyFunctions.check_and_add_field("OSMM_LCM", "Interpreted_habitat", "TEXT", 100)
        arcpy.CalculateField_management("OSMM_LCM", "Interpreted_habitat", "!OSMM_hab!", "PYTHON_9.3")

        print ("  Identifying arable land")
        arcpy.MakeFeatureLayer_management("OSMM_LCM", "ag_lyr")
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause="OSMM_hab = 'Agricultural land' OR OSMM_hab = 'Natural surface'")
        arcpy.SelectLayerByLocation_management("ag_lyr", "HAVE_THEIR_CENTER_IN", "LCM_arable", selection_type="SUBSET_SELECTION")
        arcpy.CalculateField_management("ag_lyr","LCM_farmland", "'Arable'", "PYTHON_9.3")
        arcpy.CalculateField_management("ag_lyr","Interpreted_habitat", "'Arable'", "PYTHON_9.3")
        arcpy.Delete_management("ag_lyr")

        print ("  Identifying improved grassland")
        arcpy.MakeFeatureLayer_management("OSMM_LCM", "ag_lyr2")
        arcpy.SelectLayerByAttribute_management("ag_lyr2", where_clause="OSMM_hab = 'Agricultural land' OR OSMM_hab = 'Natural surface'")
        arcpy.SelectLayerByLocation_management("ag_lyr2", "HAVE_THEIR_CENTER_IN", "LCM_improved_grassland",
                                               selection_type="SUBSET_SELECTION")
        arcpy.CalculateField_management("ag_lyr2","LCM_farmland", "'Improved grassland'", "PYTHON_9.3")
        arcpy.Delete_management("ag_lyr2")

        # Set interpreted habitat to Improved grassland if this is 'agricultural land'or Amenity grassland if this is 'Natural surface'
        # unless it is railside (do not want to flag this as amenity grassland because it is not generally accessible)
        expression = "LCM_farmland = 'Improved grassland' AND Interpreted_habitat = 'Agricultural land'"
        MyFunctions.select_and_copy("OSMM_LCM", "Interpreted_habitat", expression, "'Improved grassland'")
        expression = "LCM_farmland = 'Improved grassland' AND Interpreted_habitat = 'Natural surface' AND DescriptiveGroup <> 'Rail'"
        MyFunctions.select_and_copy("OSMM_LCM", "Interpreted_habitat", expression, "'Amenity grassland'")

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