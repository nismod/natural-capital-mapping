# Sets up one geodatabase for each LAD, clips and copies in the input files for OSMM, LAD boundary, and either CROME (formerly used LCM)
# and PHI or Phase 1 habitat (HLU). Can be applied either to Oxfordshire or the other LADs in the Arc.
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
# region = "NP"
# region = "NP_Wales"
# Which method are we using - Phase 1 habitat data or LCM and PHI?
method = "HLU"
# method = "CROME_PHI"

if region == "NP" or region == "NP_Wales":
    folder = r"M:\urban_development_natural_capital"
    LAD_folder = r"M:\urban_development_natural_capital\LADs"
    data_gdb = os.path.join(folder, "Data.gdb")
    LAD_table = os.path.join(data_gdb, "LADs")
    # LADs_included = ["Northumberland", "Allerdale", "Carlisle", "Newcastle upon Tyne", "North Tyneside", "South Tyneside", "Sunderland",
    #                  "Gateshead", "County Durham", "Copeland", "Darlington", "Stockton-on-Tees", "Hartlepool", "Middlesbrough",
    #                  "Redcar and Cleveland", "Middlesborough" ]
    # Use either counties or LADs as the list to include by commenting out the appropriate line in the code
    LADs_included = [ "Richmondshire"]
    # counties_included = ["Northumberland", "Tyne_and_Wear", "Durham", "Cumbria", "Lancashire",
    #                      "North_Yorkshire", "South_Yorkshire", "East_Yorkshire", "West_Yorkshire",
    #                      "Lincolnshire", "Greater_Manchester", "Merseyside", "Cheshire"]
    counties_included = ["Clwyd", "Gwynedd"]
    needed_fields = ["fid", "primary_key", "versiondate", "descriptivegroup", "descriptiveterm", "make"]
    LAD_name_field = "LAD_name_simple"
    County_field = "County"
    if region == "NP":
        PHI = "PHI"
        PHI_hab_field = "Main_habit"
    elif region == "NP_Wales":
        PHI = "NRW_SensitiveHabitats"
        PHI_hab_field = "Habitat_2"

elif method == "CROME_PHI":
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    data_gdb = os.path.join(folder, "Data\Data.gdb")
    LAD_table = os.path.join(data_gdb, "Arc_LADs")
    # arable = os.path.join(data_gdb, "LCM_arable")
    # improved = os.path.join(data_gdb, "LCM_improved_grassland")
    if region == "Arc":
        LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire"]
    elif region == "Oxon":
        LADs_included = ["Oxfordshire"]
    else:
        print("ERROR: Invalid region")
        exit()
    needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab"]
    LAD_name_field = "_desc"
    County_field = "county"
    PHI = "PHI"
    PHI_hab_field = "Main_habit"

elif region == "Oxon" and method == "HLU":
    # Need to replace OSMM for Oxon in data.gdb for updates
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\Oxon_county"
    data_gdb = os.path.join(folder, "Data\Data.gdb")
    LAD_table = os.path.join(data_gdb, "Oxon_LADs")
    HLU_data = os.path.join(data_gdb, "HLU")
    counties_included = ["Oxfordshire"]  # This is for doing whole county in one go
    LADs_included = ["Cherwell", "Oxford", "South Oxfordshire", "Vale of White Horse", "West Oxfordshire"]   # This is for doing separate LADs
#    needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab"]  # Old version of OSMM
    needed_fields = ["fid", "theme", "descriptivegroup", "descriptiveterm", "make", "OSMM_hab"]    # Updated for new version of OSMM
    LAD_name_field = "_desc"
    County_field = "county"
    PHI = "PHI"  # not needed as using HLU  - not sure why I left this here
    PHI_hab_field = "Main_habit"   # not needed as using HLU - not sure why I left this here

else:
    print("ERROR: you cannot currently use the HLU method with the whole Arc region")
    exit()

LAD_names = []

# Which stages of the code do we want to run? Depends on method - also can be useful for debugging or updates.
if method == "CROME_PHI":
    prep_PHI = True
    setup_PHI = True
    setup_HLU = False    # Always false for the LCM_PHI method
    setup_LCM = False    # False if LCM not being used (default)
elif method == "HLU":
    prep_PHI = False     # Always false for the HLU method
    setup_LCM = False    # Always false for the HLU method
    setup_PHI = False    # Always false for the HLU method
    setup_HLU = True
else:
    print("ERROR: Invalid region")
    exit()

setup_LAD_gdbs = True
create_gdb = True
setup_OSMM = True
clip_OSMM = False
setup_boundary = True

arcpy.env.workspace = data_gdb

if prep_PHI:
    print ("Preparing PHI datasets")
    # main PHI dataset
    arcpy.Dissolve_management(PHI, "PHI_diss_over10m2", PHI_hab_field, multi_part="SINGLE_PART")
    MyFunctions.delete_by_size("PHI_diss_over10m2", 10)
    # Copy habitat into a new field called 'PHI' (for neatness)
    MyFunctions.check_and_add_field("PHI_diss_over10m2", "PHI", "TEXT", 100)
    arcpy.CalculateField_management("PHI_diss_over10m2", "PHI", "!" + PHI_hab_field + "!", "PYTHON_9.3")
    arcpy.DeleteField_management("PHI_diss_over10m2", PHI_hab_field)
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
        LAD_full_name = LAD.getValue(LAD_name_field)
        LAD_county = LAD.getValue(County_field)
        # if LAD_county in counties_included:          # This can be used if there is a county field and we want to select all LADs for a county
        if LAD_full_name in LADs_included:             # Or if listing each LAD separately
            LAD_name = LAD_full_name.replace(" ", "")
            LAD_names.append(LAD_name)

            # Set up a new geodatabase for each LAD, copy clipped OSMM, copy boundary, and clip HLU or PHI to the boundaries
            print ("Setting up " + LAD_full_name)

            if create_gdb:
                print ("  Creating new geodatabase for " + LAD_name)
                arcpy.CreateFileGDB_management(LAD_folder, LAD_name)

            LAD_gdb = os.path.join(LAD_folder, LAD_name + ".gdb")

            if setup_boundary:
                print ("  Creating boundary for " + LAD_name)
                arcpy.MakeFeatureLayer_management(LAD_table, "LAD_lyr")
                arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause= LAD_name_field + " = '" + LAD_full_name + "'")
                arcpy.CopyFeatures_management("LAD_lyr", os.path.join(LAD_gdb, "boundary"))
                arcpy.Delete_management("LAD_lyr")

            boundary = os.path.join(LAD_gdb, "boundary")

            if setup_OSMM:
                out_fc = os.path.join(LAD_gdb, "OSMM")
                if clip_OSMM:
                    print ("  Clipping OSMM to LAD boundary")
                    arcpy.MakeFeatureLayer_management("OSMM", "OSMM_lyr")
                    arcpy.SelectLayerByLocation_management("OSMM_lyr", "INTERSECT", "boundary")  # To save time select all the intersecting features first
                    arcpy.Clip_analysis("OSMM_lyr", boundary, out_fc)
                    MyFunctions.check_and_repair(out_fc)
                else:    # If OSMM has already been clipped to a feature class called OSMM_LADname (which should be in the current folder)
                    print("  Copying OSMM for " + LAD_name + " to new geodatabase")
                    arcpy.CopyFeatures_management("OSMM_" + LAD_name, out_fc)

            if setup_LCM:    # Note: we don't use LCM (UK CEH Land Cover Map) any more
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