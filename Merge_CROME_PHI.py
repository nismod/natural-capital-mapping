# Starts from OS Mastermap base map and:
# 1. Assigns Rural Payments Agency CROME Crop map data (input must be dissolved by land use code and joined to description
# and simplified description (Arable, Improved grassland, Short-rotation coppice)
# 2. Assigns Natural England Priority Habitat data.
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

# region = "Oxon"
# region = "Arc"
region = "NP"

# method = "HLU"
method = "CROME_PHI"

if method == "CROME_PHI":
    if region == "Arc":
        folder = r"D:\cenv0389\OxCamArc\LADs"
        Counties_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire", "Oxfordshire", "Peterborough"]
        data_gdb = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Data.gdb"
        CROME_data = os.path.join(data_gdb, "CROME_2019_Arc_Dissolve")
        OSMM_Term = "DescriptiveTerm"
        OSMM_Group = "DescriptiveGroup"
        OSMM_Make = "Make"
    elif region == "Oxon":
        folder = r"D:\cenv0389\Oxon_GIS\Oxon_county"
        Counties_included = ["Oxfordshire"]
        data_gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Data.gdb"
        CROME_data = os.path.join(data_gdb, "CROME_2019_Arc_Dissolve")
        OSMM_Term = "DescriptiveTerm"
        OSMM_Group = "DescriptiveGroup"
        OSMM_Make = "Make"
    elif region == "NP":
        folder = r"M:\urban_development_natural_capital\LADs"
        # CROME_North dataset (done)
        # LADs_included = ["Northumberland", "Newcastle upon Tyne", "North Tyneside", "South Tyneside",
        #                  "Sunderland",  "Gateshead", "County Durham", "Darlington", "Stockton-on-Tees", "Hartlepool",
        #                  "Middlesbrough", "Redcar and Cleveland", "Carlisle", "Allerdale", "Eden"]
        # CROME_West dataset (done)
        # LADs_included = ["Blackburn with Darwen", "Blackpool", "Bolton", "Burnley", "Bury", "Calderdale", "Cheshire East",
        #                  "Cheshire West and Chester", "Chorley", "Fylde", "Halton", "Hyndburn", "Kirklees", "Knowsley",
        #                  "Liverpool", "Manchester", "Oldham", "Preston", "Rochdale", "Rossendale","Salford", "South Ribble"]
        # CROME_North_West dataset (done)
        # LADs_included = ["Barrow-in-Furness", "Bradford", "Copeland", "Craven", "Lancaster", "Pendle", "Ribble Valley",
        #                  "South Lakeland", "Wyre"]
        # CROME_East dataset (done) Add back  "Leeds" , , if re-doing
        # LADs_included = ["Barnsley", "Doncaster", "East Riding of Yorkshire", "North East Lincolnshire", "North Lincolnshire",
        #                  "Richmondshire", "Rotherham",  "Scarborough",
        #                  "Selby", "Sheffield", "Wakefield", "York", "Hambleton", "Harrogate", "Ryedale", "South Ribble", "Sefton",
        #                  "Stockport", "St Helens", "Tameside", "Trafford", "Warrington", "Wigan", "Wirral", "West Lancashire" ]
        LADs_included = ["Allerdale", "Barnsley", "Barrow-in-Furness", "Blackburn with Darwen", "Blackpool",
                         "Bolton", "Bradford", "Burnley", "Bury", "Calderdale", "Carlisle",
                         "Cheshire East", "Cheshire West and Chester", "Chorley", "Copeland", "County Durham",
                         "Craven", "Darlington", "Doncaster", "East Riding of Yorkshire", "Eden", "Fylde",
                         "Gateshead", "Halton", "Hambleton", "Harrogate", "Hartlepool", "Hyndburn", "Kirklees", "Knowsley",
                         "Lancaster", "Leeds", "Liverpool", "Manchester", "Middlesbrough", "Newcastle upon Tyne",
                         "North East Lincolnshire", "North Lincolnshire", "Northumberland", "North Tyneside", "Oldham",
                         "Pendle", "Preston", "Redcar and Cleveland", "Ribble Valley",
                         "Richmondshire", "Rochdale", "Rossendale", "Rotherham", "Ryedale", "Salford",
                         "Scarborough", "Sefton", "Selby", "Sheffield", "South Lakeland", "South Ribble",
                         "South Tyneside", "St Helens", "Stockport", "Stockton-on-Tees", "Sunderland",
                         "Tameside", "Trafford", "Wakefield", "Warrington", "West Lancashire", "Wigan", "Wirral",
                         "Wyre", "York"]
        data_gdb = r"M:\urban_development_natural_capital\Data.gdb"
        CROME_data = os.path.join(data_gdb, "CROME_North_West_diss")
        OSMM_Term = "descriptiveterm"
        OSMM_Group = "descriptivegroup"
        OSMM_Make = "make"
#    Hab_field = "Interpreted_habitat"
    Hab_field = "Interpreted_habitat_temp"
    LAD_table = os.path.join(data_gdb, "LADs")
elif region == "Oxon" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\Oxon_county\Data"
    data_gdb = os.path.join(folder, "Data.gdb")
    LAD_table = os.path.join(folder, "Data.gdb", "Oxon_LADs")
    CROME_data = os.path.join(data_gdb, "CROME_Oxon_dissolve")
    Hab_field = "Interpreted_habitat"
else:
    print("ERROR: you cannot combine region " + region + " with method " + method)
    exit()
in_map_name = "OSMM"
out_map_name = "OSMM_CROME"

LAD_names = []
needed_fields = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make", "OSMM_hab",
                 "primary_key", "fid", "versiondate", "descriptivegroup", "descriptiveterm", "make"]

# Which stages of the code do we want to run? Change step = 1 to step = 2 after running Merge_into_base_map to merge OSMM_CROME with PHI
step = 2
if step == 1:
    add_interpreted_habitat = True   # ONLY for Arc version that uses only OSMM, CROME and PHI etc
    merge_CROME = True
    interpret_PHI = False
elif step == 2:
    add_interpreted_habitat = False
    merge_CROME = False
    interpret_PHI = True

arcpy.env.workspace = data_gdb

# LADs = arcpy.SearchCursor(os.path.join(data_gdb, LAD_table))
# for LAD in LADs:
#     LAD_full_name = LAD.getValue("desc_")
#     County = LAD.getValue("county")
#     if County in counties_included:
#         LAD_name = LAD_full_name.replace(" ", "")
#         LAD_names.append(LAD_name)
# Or use this line to repeat for selected LADs only...
LAD_names = LADs_included

# Now process each LAD gdb

# Add crop type from CROME map, but only for agricultural land. This is probably better data then LCM and is freely available.

if merge_CROME:
    i=0
    for LAD in LAD_names:
        i=i+1
        print ("Processing " + LAD + " which is number " + str(i) + " out of " + str(len(LAD_names)))
        LAD_name = LAD.replace(" ", "")
        arcpy.env.workspace = os.path.join(folder, LAD_name + ".gdb")
        in_map = in_map_name
        out_map = out_map_name

        print("  Copying " + in_map + " to " + out_map)
        arcpy.CopyFeatures_management(in_map, out_map)

        if add_interpreted_habitat == True:
            print("  Copying OSMM_hab to new Interpreted habitat field")
            MyFunctions.check_and_add_field(out_map, Hab_field, "TEXT", 100)
            arcpy.CalculateField_management(out_map, Hab_field, "!OSMM_hab!", "PYTHON_9.3")

        print("  Copying OBJECTID for base map")
        MyFunctions.check_and_add_field(out_map, "BaseID_CROME", "LONG", 0)
        arcpy.CalculateField_management(out_map, "BaseID_CROME", "!OBJECTID!", "PYTHON_9.3")

        print ("  Identifying farmland and amenity grass")
        # 'Natural surface' is mainly road verges and amenity grass in urban areas
        arcpy.MakeFeatureLayer_management(out_map, "ag_lyr")
        expression = Hab_field + " IN ('Agricultural land', 'Natural surface')"
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause=expression)

        print("  Calculating percentage of farmland and amenity features within CROME polygons")
        arcpy.TabulateIntersection_analysis("ag_lyr", ["OBJECTID", Hab_field, "BaseID_CROME", "Shape_Area"],
                                            CROME_data, "CROME_TI", ["lucode", "Land_Use_Description", "Simple", "Shape_Area"])

        # Sorting TI table by size so that larger intersections are first in the list
        print("  Sorting table with largest intersections first")
        arcpy.Sort_management("CROME_TI", "CROME_TI_sort", [["AREA", "DESCENDING"]])
        # Delete all but the largest intersection. We need to do this, otherwise the join later is not robust - the wrong rows can be
        # copied across even if we think we have selected and joined to the right rows.
        print("Deleting identical (smaller intersection) rows")
        arcpy.DeleteIdentical_management("CROME_TI_sort", ["OBJECTID_1"])

        # Adding fields for CROME data
        out_map = "OSMM_CROME"
        print ("Adding new fields for CROME data")
        MyFunctions.check_and_add_field(out_map, "CROME_desc", "TEXT", 50)
        MyFunctions.check_and_add_field(out_map, "CROME_simple", "TEXT", 50)

        # Join the intersected table to join in the largest intersection to each polygon
        print ("Joining CROME info for base map polygons")
        arcpy.MakeTableView_management("CROME_TI_sort", "CROME_lyr")
        arcpy.AddJoin_management("ag_lyr", "BaseID_CROME", "CROME_lyr", "BaseID_CROME", "KEEP_ALL")
        # Select only agricultural CROME polygons and intersections where there is >30% overlap
        # Data will only be copied for the selected polygons
        expression = "CROME_TI_sort.Simple <> 'Non-agricultural land' AND PERCENTAGE > 30"
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause=expression)
        # Copy data from ag_lyr which is now joined with CROME into the main layer
        print("Copying CROME data")
        arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_desc", "!CROME_TI_sort.Land_Use_Description!", "PYTHON_9.3")
        print("Finished copying CROME desc")
        arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_simple", "!CROME_TI_sort.Simple!", "PYTHON_9.3")
        print("Finished copying CROME simple")

        # Remove the join
        arcpy.RemoveJoin_management("ag_lyr", "CROME_TI_sort")
        arcpy.Delete_management("ag_lyr")
        arcpy.Delete_management("CROME_lyr")
        print("Finished merging CROME")

        print ("Interpreting")
        # Copy over CROME for grass to 'Agricultural land' but not for 'Natural surface' as that is mainly road verges
        # and amenity grass in urban areas
        expression = "CROME_desc = 'Grass' AND " + Hab_field + " IN ('Agricultural land')"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland'")
        # Copy over CROME for arable to 'Agricultural land' but not for 'Natural surface'.
        # Most 'fallow' land in CROME looks more like arable than grass
        # in Google earth, so set that to arable as well (even though CROME simple description is grass).
        expression = "CROME_simple IN ('Arable', 'Fallow land') AND " + Hab_field + " IN ('Agricultural land')"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")
        # Examination for Oxon shows only two single CROME polygons for SRC, both look like mis-classifications so ignore
        # Similarly, ignore for now the Nursery trees and Perennial crops or isolated trees categories in CROME as they look dodgy,
        # some look like grassland and some like arable though some could actually be correct.

        # This is commented out as it is better to wait for Join_Greenspace to identify amenity grass, because OSMM GreenSpace distinguishes
        # transport from general amenity and other natural surface such as old airfields or golf courses) (though only in urban areas):
        # Set interpreted habitat to Amenity grassland if this is 'Natural surface'
        # unless it is railside (do not want to flag this as amenity grassland because it is not generally accessible)
        # expression = "CROME_desc = 'Grass' AND " + Hab_field + " = 'Natural surface' AND DescriptiveGroup <> 'Rail'"
        # MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Amenity grassland'")

        print(''.join(["## Finished adding CROME data to " + LAD + " on : ", time.ctime()]))

if interpret_PHI:
    i = 0
    for LAD in LAD_names:
        i=i+1
        print ("Processing " + LAD + " which is number " + str(i) + " out of " + str(len(LAD_names)))
        LAD_name = LAD.replace(" ", "")
        arcpy.env.workspace = os.path.join(folder, LAD_name + ".gdb")
        print("Interpreting " + LAD)

        out_map = out_map_name + "_PHI"
        # *** temporary fix for corrections
        # out_map = "OSMM_CR_PHI_ALC_Desig_GS"

        # Copy PHI habitat across, but not for manmade, gardens, water, unidentified PHI, grazing marsh, wood pasture or
        # OMHD (all dealt with later)
        expression = OSMM_Make + " = 'Natural' AND " + OSMM_Group + " NOT LIKE '%water%' AND " + OSMM_Group + " NOT LIKE '%Water%'"
        expression = expression +  " AND OSMM_hab <> 'Roadside: unknown surface' AND OSMM_hab <> 'Track' AND OSMM_hab <> 'Standing water' "
        expression = expression +  " AND PHI IS NOT NULL AND PHI <> '' AND PHI NOT LIKE 'No main%' AND "
        expression = expression +  "PHI NOT LIKE 'Wood-pasture%' AND PHI NOT LIKE 'Open Mosaic%' AND PHI NOT LIKE '%grazing marsh'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "!PHI!")

        # Correction for traditional orchards in large gardens
        MyFunctions.select_and_copy(out_map, Hab_field, "PHI = 'Traditional orchard' AND OSMM_hab = 'Garden'", "'Traditional orchards'")

        # Other corrections / consolidations
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Deciduous woodland'", "'Woodland: broadleaved, semi-natural'")

        expression3 = "(PHI LIKE '%grazing marsh%' AND (" + Hab_field + " LIKE '%grass%' AND " + Hab_field + " NOT LIKE '%scattered%')) OR " \
                      + Hab_field + " LIKE 'Purple moor grass%'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland'")
        expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered scrub'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered scrub'")
        expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: broadleaved'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: broadleaved'")
        expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: mixed'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: mixed'")
        expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: coniferous'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: coniferous'")


        expression = Hab_field + " LIKE '%semi-improved grassland%' AND " + Hab_field + " <> 'Poor semi-improved grassland'"
        MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Semi-natural grassland'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " LIKE '%meadow%'", "'Neutral grassland'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Traditional orchard'", "'Traditional orchards'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " LIKE '%alcareous%'", "'Calcareous grassland'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Grass moorland'", "'Acid grassland'")
        expression4 = " IN ('Lowland heathland', 'Upland heathland', 'Fragmented heath')"
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + expression4, "'Heathland'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Mountain heaths and willow scrub'",
                                    "'Heath with scattered trees: broadleaved'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " IN ('Blanket bog', 'Lowland raised bog')", "'Bog'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Reedbeds'", "'Reedbed'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Coastal saltmarsh'", "'Saltmarsh'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Saline lagoons'", "'Coastal lagoons'")
        MyFunctions.select_and_copy(out_map, Hab_field, Hab_field + " = 'Maritime cliff and slope'", "'Coastal rock'")

        # Copy over OMHD only if the habitat is fairly generic (OMHD dataset covers areas of mixed habitats)
        # Debatable whether 'Quarry or spoil' should be included. Previously only included if inactive, but inspection
        # shows vegetation on many supposedly active sites. Used to include sealed surface but now do not, because this can be redevelopment
        # on brownfield sites
        expression5 = "(OMHD IS NOT NULL AND OMHD <> '') AND (" + Hab_field + " IN ('Arable', 'Agricultural land'," \
                      " 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land', 'Bare ground', 'Landfill: disused'," \
                      "'Quarry or spoil: disused', 'Quarry or spoil'))"
        MyFunctions.select_and_copy(out_map, Hab_field, expression5, "'Open mosaic habitats'")

        # Copy over Wood pasture only if the habitat is fairly generic (WPP dataset covers very large areas of mixed habitats)
        # Do not copy WPP for arable, as that is now fairly accurate (from CROME)
        expression4 = "(WPP IS NOT NULL AND WPP <> '') AND (" + Hab_field + " IN ('Agricultural land', " \
                      "'Improved grassland', 'Natural surface', 'Cultivated/disturbed land') OR " \
                      + Hab_field + " LIKE 'Scattered%' OR " + Hab_field + " LIKE 'Semi-natural grassland%')"
        MyFunctions.select_and_copy(out_map, Hab_field, expression4, "'Parkland and scattered trees: broadleaved'")

        print(''.join(["## Finished on : ", time.ctime()]))

if step == 1:
    print ("Now run Merge_into_Base_Map.py to merge OSMM_CR with PHI, then set step = 2 in this code and re-run to interpret habitats")
exit()