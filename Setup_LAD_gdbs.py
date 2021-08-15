# Sets up one geodatabase for each LAD, clips and copies in the input files for OSMM, LAD boundary, and either LCM and PHI
# or Phase 1 habitat (HLU). Can be applied either to Oxfordshire or the other LADs in the Arc.
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

# region = "Oxon"
# region = "Arc"
region = "NP"
# Which method are we using - Phase 1 habitat data or LCM and PHI?
# method = "HLU"
method = "LCM_PHI"

if region == "NP":
    folder = r"M:\urban_development_natural_capital"
    data_gdb = os.path.join(folder, "Data.gdb")
    LAD_table = os.path.join(data_gdb, "NP_LADs")
    LADs_included = ["Leeds"]

elif method == "LCM_PHI":
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    data_gdb = os.path.join(folder, "Data\Data.gdb")
    LAD_table = os.path.join(data_gdb, "Arc_LADs")
    if region == "Arc":
        LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire"]
    elif region == "Oxon":
        LADs_included = ["Oxfordshire"]
    else:
        print("ERROR: Invalid region")
        exit()

elif region == "Oxon" and method == "HLU":
    # Caution - OSMM for Oxon has already been copied to the LAD gdbs and deleted from data.gdb, so need to replace it for updates
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\Oxon_county"
    data_gdb = os.path.join(folder, "Data\Data.gdb")
    LAD_table = os.path.join(data_gdb, "Oxon_LADs")
    HLU_data = os.path.join(data_gdb, "HLU")
    LADs_included = ["Oxfordshire"]

else:
    print("ERROR: you cannot currently use the HLU method with the whole Arc region")
    exit()

arable = os.path.join(data_gdb, "LCM_arable")
improved = os.path.join(data_gdb, "LCM_improved_grassland")

LAD_names = []
needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab"]

# Which stages of the code do we want to run? Depends on method - also can be useful for debugging or updates.
if method == "LCM_PHI":
    prep_PHI = True
    setup_LCM = False
    setup_PHI = False
    setup_HLU = False    # Always false for the LCM_PHI method
elif method == "HLU":
    prep_PHI = False     # Always false for the HLU method
    setup_LCM = False    # Always false for the HLU method
    setup_PHI = False    # Always false for the HLU method
    setup_HLU = True
else:
    print("ERROR: Invalid region")
    exit()

setup_LAD_gdbs = False
create_gdb = False
copy_OSMM = False
setup_boundary = False

arcpy.env.workspace = data_gdb

if prep_PHI:
    print ("Preparing PHI datasets")
    # main PHI dataset
    # arcpy.Dissolve_management("PHI", "PHI_diss_over10m2", "Main_habit", multi_part="SINGLE_PART")
    # MyFunctions.delete_by_size("PHI_diss_over10m2", 10)
    # # Copy 'Main_habit' into a new field called 'PHI' (for neatness)
    # MyFunctions.check_and_add_field("PHI_diss_over10m2", "PHI", "TEXT", 100)
    # arcpy.CalculateField_management("PHI_diss_over10m2", "PHI", "!Main_habit!", "PYTHON_9.3")
    # arcpy.DeleteField_management("PHI_diss_over10m2", "Main_habit")
    # Wood pasture and parkland with scattered trees
    arcpy.Dissolve_management("WoodPastureAndParkland", "WPP_diss_over10m2", "PRIHABTXT", multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("WPP_diss_over10m2", 10)
    # Copy 'Main_habit' into a new field called 'WPP' (for neatness)
    MyFunctions.check_and_add_field("WPP_diss_over10m2", "WPP", "TEXT", 100)
    arcpy.CalculateField_management("WPP_diss_over10m2", "WPP", "!PRIHABTXT!", "PYTHON_9.3")
    arcpy.DeleteField_management("WPP_diss_over10m2", "PRIHABTXT")
    # Open mosaic habitats on previously developed land
    arcpy.Dissolve_management("OMHD", "OMHD_diss_over10m2", "PRIHABTXT", multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("OMHD_diss_over10m2", 10)
    # Copy 'Main_habit' into a new field called 'OMHD' (for neatness)
    MyFunctions.check_and_add_field("OMHD_diss_over10m2", "OMHD", "TEXT", 100)
    arcpy.CalculateField_management("OMHD_diss_over10m2", "OMHD", "!PRIHABTXT!", "PYTHON_9.3")
    arcpy.DeleteField_management("OMHD_diss_over10m2", "PRIHABTXT")
    # Union
    print("Unioning the three PHI datasets")
    arcpy.Union_analysis(["PHI_diss_over10m2", "WPP_diss_over10m2", "OMHD_diss_over10m2"], "PHI_union", "NO_FID")

    print ("Copying WPP or OMHD to blank PHI fields")
    # Fill in "PHI" field where it is blank, with WPP or OMHD (OMHD takes priority as WPP can cover large mixed areas indiscriminately)
    # This bit not tested since rewrite...
    expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (OMHD IS NOT NULL AND OMHD <> '')"
    MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!OMHD!")
    expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%') AND (WPP IS NOT NULL AND WPP <> '')"
    MyFunctions.select_and_copy("PHI_union", "PHI", expression, "!WPP!")

if setup_LAD_gdbs:
    LADs = arcpy.SearchCursor(LAD_table)
    for LAD in LADs:
        LAD_full_name = LAD.getValue("desc_")
        LAD_county = LAD.getValue("county")
        if LAD_county in LADs_included:
            LAD_name = LAD_full_name.replace(" ", "")
            LAD_names.append(LAD_name)

            # Set up a new geodatabase for each LAD, copy clipped OSMM, copy boundary, and clip LCM and PHI to the boundaries
            print ("Setting up " + LAD_full_name)

            if create_gdb:
                print ("  Creating new geodatabase for " + LAD_name)
                arcpy.CreateFileGDB_management(folder, LAD_name)

            LAD_gdb = os.path.join(folder, LAD_name + ".gdb")

            if copy_OSMM:
                print("  Copying OSMM for " + LAD_name + " to new geodatabase")
                outfc = os.path.join(LAD_gdb, "OSMM")
                arcpy.CopyFeatures_management("OSMM_" + LAD_name, outfc)

            if setup_boundary:
                print ("  Creating boundary for " + LAD_name)
                arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
                arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause="desc_ = '" + LAD_full_name + "'")
                arcpy.CopyFeatures_management("LAD_lyr", os.path.join(LAD_gdb, "boundary"))
                arcpy.Delete_management("LAD_lyr")

            boundary = os.path.join(LAD_gdb, "boundary")

            if setup_LCM:
                print ("  Clipping Land Cover Map farmland to LAD boundary")
                out_file = os.path.join(LAD_gdb, "LCM_arable")
                arcpy.Clip_analysis("LCM_arable", boundary, out_file)
                MyFunctions.check_and_repair(out_file)
                out_file = os.path.join(LAD_gdb, "LCM_improved_grassland")
                arcpy.Clip_analysis("LCM_improved_grassland", boundary, out_file)
                MyFunctions.check_and_repair(out_file)
            if setup_PHI:
                print ("  Clipping PHI to LAD boundary")
                out_file = os.path.join(LAD_gdb, "PHI")
                arcpy.Clip_analysis("PHI_union", boundary, out_file)
                MyFunctions.check_and_repair(out_file)
            if setup_HLU:
                print ("  Clipping HLU to LAD boundary")
                out_file = os.path.join(LAD_gdb, "HLU")
                arcpy.Clip_analysis(HLU_data, boundary, out_file)
                MyFunctions.check_and_repair(out_file)

            print(''.join(["## Finished setting up " + LAD_name + " gdb on : ", time.ctime()]))

exit()