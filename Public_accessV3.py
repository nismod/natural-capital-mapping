# Aim is to apply a multiplier to the natural capital scores to reflect the degree of public access
# Challenge is that it is difficult to clip or intersect the complex public access layer with the large and
# detailed OSMM-based base map - it takes days to run and then fails.
# So here we extract a subset of the base map that excludes gardens and manmade features, to cut the processing load.
# Create a public access layer from component datasets and set up a multiplier for recreation
# Intersect the public access layer with the subset and merge back into the base map
# A separate multiplier can then be applied to all gardens to reflect their private value if required
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

# *** Enter parameters
# --------------------
region = "Arc"
# region = "Oxon"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "HLU"

if region == "Oxon" and method == "HLU":
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Public_access.gdb"]
    region_boundary = "Oxfordshire"
    boundary = "Oxfordshire"
    base_map = "OSMM_HLU_CR_ALC_Des_GS"
    area_tag = "Oxon"
    hab_field = "Interpreted_habitat"

elif region == "Arc" or (region == "Oxon" and method == "CROME_PHI"):
    folder = r"D:\cenv0389\OxCamArc\LADs"
    arcpy.env.workspace = folder
    if region == "Arc":
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        # gdbs = []
        # gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
        # gdbs.append(os.path.join(folder, "Chiltern.gdb"))
        # gdbs.append(os.path.join(folder, "SouthOxfordshire.gdb"))
    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
    boundary = "boundary"
    region_boundary = os.path.join(folder, "Arc_outline.shp")
    base_map = "OSMM_CR_PHI_ALC_Desig_GS"
    area_tag = "Arc"
    hab_field = "Interpreted_habitat"
    # Feature classes to keep - the others will be deleted if you select 'tidy_workspace' = true
    keep_fcs = ["boundary", "Designations", "LCM_arable", "LCM_improved_grassland", "OS_Open_GS", "OS_Open_GS_clip", "OSGS",
                "OSMM", "OSMM_CROME", "OSMM_CROME_PHI", "OSMM_CR_PHI_ALC", "OSMM_CR_PHI_ALC_Desig",
                "OSMM_CR_PHI_ALC_Desig_GS", "OSMM_CR_PHI_ALC_Desig_GS_PA", "PHI", "Public_access"]

# Source of public access data and gdb where public access layer will be created
if region == "Oxon":
    data_gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Public_access.gdb"
    des_list = ['CountryPk', 'NT', 'NNR', 'LNR', 'DoorstepGn', 'MillenGn', 'RSPB']
    des_list_expression = "(((CountryPk + NT + NNR + LNR + MillenGn + DoorstepGn + RSPB) = 0) OR " \
                          "(CountryPk IS NULL AND NT IS NULL AND NNR IS NULL AND LNR IS NULL AND MillenGn IS NULL AND DoorstepGn IS NULL" \
                          " AND RSPB IS NULL))"
elif region == "Arc":
    data_gdb = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Public_access.gdb"
    des_list = ['CountryPk', 'NT', 'NNR', 'LNR', 'DoorstepGn', 'MillenGn', 'RSPB']
    des_list_expression = "(((CountryPk + NT + NNR + LNR + MillenGn + DoorstepGn + RSPB) = 0) OR " \
                          "(CountryPk IS NULL AND NT IS NULL AND NNR IS NULL AND LNR IS NULL AND MillenGn IS NULL AND DoorstepGn IS " \
                          "NULL AND RSPB IS NULL))"

# Table containing info for each input layer - user needs to set it up. Note: we also use OS Greenspace, OS Open Greenspace and
# various designations (e.g. nature reserves), but these are already merged into the base map so do not need to be listed in the info table.
InfoTable = os.path.join(data_gdb, "PublicAccessFiles")
AccessTable_name = "AccessMultipliers"
AccessTable = os.path.join(data_gdb, "AccessMultipliers")

# Buffer distance for paths
buffer_distance = "50 Meters"
# Need to dissolve all paths into a single buffer area if networks are complex, otherwise the process may crash
dissolve_paths = True

# Which stages of the process do we want to run? Useful for debugging or updates
create_access_layer = False
clip_region = False
buffer_paths = True
merge_paths = True
clip_PA_into_LAD_gdb = False    # Do not use this if the public access layer is made in the same gdb
extract_relevant_polygons = True
intersect_access = True
sp_and_repair = True
interpret_access = True
correct = True
tidy_fields = True
if method == "CROME_PHI":
    tidy_workspace = True # DO NOT USE THIS FOR OXON HLU method!! It is not set up yet.
else:
    tidy_workspace = False

# *** End of parameter entry
# --------------------------

if create_access_layer:
    # Create public access layer by merging multiple input files, reading info from a table
    # Linear features (paths, cycle routes) are converted to a 50m buffer zone
    # Set up Type, Description and Name field for each file, reading info from InfoTable, and populate by copying existing relevant fields

    arcpy.env.workspace = data_gdb
    InAreas = []
    InPaths = []
    ipath = 0

    # First loop through to find max length for Name and Description fields
    max_NameLen = 0
    max_DescLen = 0
    cursor = arcpy.SearchCursor(InfoTable)
    for row in cursor:
        if dissolve_paths == False or (dissolve_paths == True and row.getValue("Path") == 0):
            DescLen = row.getValue("DescLength")
            if DescLen > max_DescLen:
                max_DescLen = DescLen
            NameLen = row.getValue("NameLength")
            if NameLen > max_NameLen:
                max_NameLen = NameLen

    # Deal with paths first.
    # If we are dissolving paths, merge all the path input line files first
    if dissolve_paths:
        if merge_paths:
            cursor = arcpy.SearchCursor(InfoTable)
            for row in cursor:
                if row.getValue("Path") == 1:
                    in_file = row.getValue("Filename")
                    if clip_region:
                        print("Clipping " + in_file)
                        arcpy.Clip_analysis(in_file, region_boundary, in_file + "_" + area_tag)
                    if area_tag <> "":
                        in_file = in_file + "_" + area_tag
                    InPaths.append(in_file)
            arcpy.Merge_management(InPaths, "Paths_merge")
            print("Buffering and dissolving merged paths")
            arcpy.Buffer_analysis("Paths_merge", "Paths_merge_buffer", buffer_distance, dissolve_option="ALL")
            # Add PAType
            print("Adding Type field")
            MyFunctions.check_and_add_field("Paths_merge_buffer", "PAType", "TEXT", 50)
            arcpy.CalculateField_management("Paths_merge_buffer", "PAType", "'Path'", "PYTHON_9.3")
            arcpy.MultipartToSinglepart_management("Paths_merge_buffer", "Paths_merge_buffer_sp")

    # Now loop through the other areas (and paths if keeping separate) to set up the Type, Description and Name fields
    cursor = arcpy.SearchCursor(InfoTable)
    for row in cursor:
        exit_flag = False
        in_file = row.getValue("Filename")
        ShortName = row.getValue("ShortName")
        print("Processing " + ShortName)
        Type = row.getValue("Type")
        Path = row.getValue("Path")
        NameField = row.getValue("NameField")
        DescField = row.getValue("DescField")

        if Path == 1:
            if dissolve_paths:
                exit_flag = True
            else:
                exit_flag = False
        if exit_flag == False:
            if clip_region:
                print("Clipping " + in_file)
                arcpy.Clip_analysis(in_file, region_boundary, in_file + "_" + area_tag)
            if area_tag <> "":
                in_file = in_file + "_" + area_tag
                if Path == 1:
                    if buffer_paths:
                        print("Buffering " + in_file)
                        arcpy.Buffer_analysis(in_file, in_file + "_buffer", buffer_distance, dissolve_option="NONE")
                    in_file = in_file + "_buffer"
                # MyFunctions.check_and_repair(in_file)

            print("Adding Type field")
            MyFunctions.check_and_add_field(in_file, "PAType", "TEXT", 50)
            arcpy.CalculateField_management(in_file, "PAType", "'" + Type + "'", "PYTHON_9.3")

            if DescField:
                if max_DescLen <= 40:
                    max_DescLen = 40
                print("Adding Description field")
                MyFunctions.check_and_add_field(in_file, "PADescription", "TEXT", max_DescLen)
                arcpy.CalculateField_management(in_file, "PADescription", "!" + DescField + "!", "PYTHON_9.3")

            if NameField:
                print("Adding Name field")
                MyFunctions.check_and_add_field(in_file, "PAName", "TEXT", max_NameLen)
                arcpy.CalculateField_management(in_file, "PAName", "!" + NameField + "!", "PYTHON_9.3")

            # Delete fields that are not needed
            needed_fields = ["PAType", "PADescription", "PAName"]
            MyFunctions.delete_fields(in_file, needed_fields, in_file + "_input")

            if Path:
                # If this is not the first path dataset, erase it from the others and then append. This way we should avoid overlaps,
                # provided that paths have been dissolved (as delete_identical method may not work for very large and complex layers
                # with lots of overlaps).
                if ipath == 1:
                    arcpy.CopyFeatures_management(in_file + "_input", "Access_paths_merge_1")
                elif ipath > 1:
                    print ("Erasing " + in_file + "_input from merged paths")
                    try:
                        arcpy.Erase_analysis("Access_paths_merge_" + str(ipath-1), in_file + "_input", "Access_paths_merge_" + str(ipath))
                    except:
                        print("Erase failed - please try manually in ArcMap and then comment out this section and restart")
                        exit()
                    print ("Appending " + in_file + "_input to merged paths")
                    arcpy.Append_management(["Access_paths_merge_1" + str(ipath)], in_file + "_input", "NO_TEST")
            else:
                # Check for any duplicate polygons
                arcpy.FindIdentical_management(in_file + "_input", "Identical_" + in_file, ["Shape"], output_record_option="ONLY_DUPLICATES")
                numrows = arcpy.GetCount_management("Identical_" + in_file)
                if numrows>0:
                    print ("Warning - " + str(numrows) + " duplicate polygons found in " + in_file +
                           "_input. All but one of each shape will be deleted.")
                    arcpy.DeleteIdentical_management(in_file + "_input", ["Shape"])
                InAreas.append(in_file + "_input")

    print("Merging areas: " + ', '.join(InAreas))
    arcpy.Merge_management(InAreas, "Access_areas_merge")

    # Need to convert merged paths to single part otherwise it crashes
    print ("Converting merged paths to single part")
    if not dissolve_paths:
        arcpy.MultipartToSinglepart_management("Access_paths_merge_" + str(ipath), "Paths_merge_buffer_sp")
    MyFunctions.check_and_repair("Paths_merge_buffer_sp")

    # Erase any paths that are within the accessible areas or private (military) areas, to reduce the complexity of the merged shapes
    print ("Erasing paths within areas")
    arcpy.Merge_management(["Access_areas_merge", "OSM_military"], "Access_areas_to_erase")
    try:
        arcpy.Erase_analysis("Paths_merge_buffer_sp", "Access_areas_to_erase", "Access_paths_erase")
    except:
        print("Erase failed but will probably work manually in ArcGIS. Please try this and then restart, commenting out previous steps")
        exit()

    print ("Merging paths and areas")
    arcpy.Merge_management(["Access_areas_merge", "Access_paths_erase"], "Access_merge")
    print("After merge there are " + str(arcpy.GetCount_management("Access_merge")) + " rows")

    print ("Dissolving - retaining type, name and description")
    arcpy.Dissolve_management("Access_merge", "Access_merge_diss", ["PAType", "PADescription", "PAName"], multi_part="SINGLE_PART")
    print ("Unioning as first step to removing overlaps")
    try:
        arcpy.Union_analysis([["Access_merge_diss", 1]], "Access_merge_union", "NO_FID")
    except:
        print ("Union failed. Please do manually then comment out preceding steps and restart.")
        exit()
    print("After union there are " + str(arcpy.GetCount_management("Access_merge_union")) + " rows")

    # If description is blank, fill in with Type
    print ("Filling in missing Descriptions")
    arcpy.MakeFeatureLayer_management("Access_merge_union", "join_lyr")
    arcpy.SelectLayerByAttribute_management("join_lyr", where_clause="PADescription IS NULL OR PADescription = ''")
    arcpy.CalculateField_management("join_lyr", "PADescription", "!PAType!", "PYTHON_9.3")
    arcpy.Delete_management("join_lyr")

    # Set up Access multiplier based on Type and Description (join to Access table then copy over source, type and multiplier)
    print ("Joining to access multiplier")
    MyFunctions.check_and_add_field("Access_merge_union", "Source", "TEXT", 30)
    MyFunctions.check_and_add_field("Access_merge_union", "AccessType", "TEXT", 30)
    MyFunctions.check_and_add_field("Access_merge_union", "AccessMult", "FLOAT", 0)
    arcpy.MakeFeatureLayer_management("Access_merge_union", "join_lyr2")
    print ("Adding join")
    arcpy.AddJoin_management("join_lyr2", "PADescription", AccessTable, "Description", "KEEP_ALL")
    print("Copying source field")
    arcpy.CalculateField_management("join_lyr2", "Access_merge_union.Source", "!" + AccessTable_name + ".Source!", "PYTHON_9.3")
    print ("Copying access type")
    arcpy.CalculateField_management("join_lyr2", "Access_merge_union.AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
    print ("Copying access multiplier")
    arcpy.CalculateField_management("join_lyr2", "Access_merge_union.AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
    arcpy.RemoveJoin_management("join_lyr2", AccessTable_name)
    arcpy.Delete_management("join_lyr2")

    print("Sorting " + str(arcpy.GetCount_management("Access_merge_union")) + " rows")
    # Sort by access multiplier (descending) so highest multipliers are at the top
    arcpy.Sort_management("Access_merge_union", "Access_merge_union_sort", [["AccessMult", "DESCENDING"]])

    # Delete identical polygons to remove overlaps but leave the highest access score. For complex path networks this may fail, so
    # dissolve paths and then do this step only for areas, not paths
    print ("Deleting overlapping polygons, keeping the one with the highest access score")
    arcpy.MakeFeatureLayer_management("Access_merge_union_sort", "del_lyr")
    if dissolve_paths:
        arcpy.SelectLayerByAttribute_management("del_lyr", where_clause="AccessType <> 'Path'")
    arcpy.DeleteIdentical_management("del_lyr", ["Shape"])
    print("After deleting identical polygons there are " + str(arcpy.GetCount_management("Access_merge_union_sort")) + " rows")
    arcpy.Delete_management("del_lyr")

    print ("Dissolving")
    dissolve_fields = ["PAType", "PADescription", "PAName", "Source", "AccessType", "AccessMult"]
    arcpy.Dissolve_management("Access_merge_union_sort","Access_merge_union_sort_diss", dissolve_field=dissolve_fields)
    print("After dissolving there are " + str(arcpy.GetCount_management("Access_merge_union_sort_diss")) + " rows")
    arcpy.MultipartToSinglepart_management("Access_merge_union_sort_diss", "Public_access")
    print("After converting to single part there are " + str(arcpy.GetCount_management("Public_access")) + " rows")

    MyFunctions.check_and_repair("Public_access")

for gdb in gdbs:
    arcpy.env.workspace = gdb
    numrows = arcpy.GetCount_management(os.path.join(gdb, base_map))
    print (''.join(["### Started processing ", gdb, " on ", time.ctime(), ": ", str(numrows), " rows"]))

    # code block for debugging if you have to restart part way through the loop through areas.....
    # if "Aylesbury" in gdb:
    #     extract_relevant_polygons = False
    #     clip_PA_into_LAD_gdb = False
    #     remove_manmade_gardens = False
    #     intersect_access = False
    #     sp_and_repair = False
    #     interpret_access = True
    # else:
    #     extract_relevant_polygons = True
    #     clip_PA_into_LAD_gdb = True
    #     remove_manmade_gardens = True
    #     intersect_access = True
    #     sp_and_repair = True
    #     interpret_access = True

    if clip_PA_into_LAD_gdb:
        # Use this to clip the master copy of the public access layer into each LAD gdb.
        print("    Clipping public access layer")
        PA_layer = os.path.join(data_gdb, "Public_access")
        arcpy.Clip_analysis(PA_layer, boundary, "Public_access")

    if extract_relevant_polygons:
        # Select base map polygons that are not 'Manmade' or 'Garden', green space or designated as accessible types, and export to new file
        print ("    Extracting polygons that are not gardens or manmade and have no relevant greenspace or designation attributes")
        arcpy.MakeFeatureLayer_management(base_map, "sel_lyr")
        # There was an error here: Amenity grassland had an underscore between the words so would not have been excluded as intended.
        # Fixed on 1/10/2020. This will have affected all the work done for Blenheim and EA Arc, and updated Oxon map sent to
        # Nick and Mel end Sept 2020. Not clear how much difference it makes; possibly none? Because it simply added either Open or Path
        # to amenity grassland not in Greenspace (rather than leaving it out), which is later over-ridden to Open for all amenity grassland.
        expression = hab_field + " NOT IN ('Garden', 'Amenity grassland') AND Make <> 'Manmade' AND " \
                                 "(GreenSpace IS NULL OR GreenSpace = '') AND " + des_list_expression
        arcpy.SelectLayerByAttribute_management("sel_lyr", where_clause=expression)
        arcpy.CopyFeatures_management("sel_lyr", "Natural_features")
        arcpy.Delete_management("sel_lyr")

    if intersect_access:
        print ("    Erasing and deleting existing greenspace from access layer, to reduce slivers")
        arcpy.MakeFeatureLayer_management("Public_access", "del_lyr")
        expression = "PADescription = 'country_park' OR PADescription = 'millennium_green' OR PADescription = 'doorstep_green'"
        arcpy.SelectLayerByAttribute_management("del_lyr", where_clause=expression)
        arcpy.DeleteFeatures_management("del_lyr")
        arcpy.Delete_management("del_lyr")

        arcpy.MakeFeatureLayer_management(base_map, "sel_lyr2")
        expression = "GreenSpace IS NOT NULL AND GreenSpace <> ''"
        arcpy.SelectLayerByAttribute_management("sel_lyr2", where_clause=expression)
        arcpy.Erase_analysis("Public_access", "sel_lyr2", "Public_access_erase", cluster_tolerance="0.001 Meters")
        print ("    Deleting slivers")
        arcpy.MultipartToSinglepart_management("Public_access_erase", "Public_access_erase_sp")
        MyFunctions.delete_by_size("Public_access_erase_sp", 20)

        print("    Intersect started on " +  time.ctime() )
        arcpy.Intersect_analysis(["Natural_features", "Public_access_erase_sp"], base_map + "_isect")
        print("    Intersect completed on " +  time.ctime())

        print ("    Erasing and merging back in")
        arcpy.Erase_analysis(base_map, base_map + "_isect", base_map + "_isect_erase", cluster_tolerance="0.001 Meters" )
        arcpy.Merge_management([base_map + "_isect_erase", base_map + "_isect"], base_map + "_merge")
        print("    Merge completed on : " +  time.ctime())

    if sp_and_repair:
        # Sort by shape so it displays faster
        print("    Converting to single part and sorting")
        arcpy.MultipartToSinglepart_management(base_map + "_merge", base_map + "_merge_sp")
        arcpy.Sort_management(base_map + "_merge_sp", base_map + "_PA", [["SHAPE", "ASCENDING"]], "PEANO")
        print ("    Rows have increased from " + str(numrows) + " to " + str(arcpy.GetCount_management(base_map + "_PA")))

        # Check and repair geometry
        MyFunctions.check_and_repair(base_map + "_PA")

    if interpret_access:
        print("    Interpreting accessibility")
        # Add interpretation for the remaining types of green space
        # Amenity grassland - from habitat and/or OSGS 'Amenity - residential and business' - assume all is accessible.
        # Hopefully OSGS amenity excludes most amenity associated with large rural houses but keeps urban green spaces that are usually
        # accessible by all. Road verges and 'Amenity - transport' currently excluded as they include roundabouts / motorway embankments.
        arcpy.MakeFeatureLayer_management(base_map + "_PA", "amenity_lyr")
        expression = hab_field + " = 'Amenity grassland' AND (PAType IS NULL OR PAType = '' OR AccessType = 'Path') " \
                     "AND DescriptiveGroup NOT LIKE '%Rail%'"
        arcpy.SelectLayerByAttribute_management("amenity_lyr", where_clause=expression)
        arcpy.CalculateField_management("amenity_lyr", "PAType", "'Amenity grassland'", "PYTHON_9.3")
        arcpy.CalculateField_management("amenity_lyr", "PADescription", "'Amenity grassland'", "PYTHON_9.3")
        arcpy.CalculateField_management("amenity_lyr", "Source", "'Amenity grassland'", "PYTHON_9.3")
        arcpy.CalculateField_management("amenity_lyr", "AccessType", "'Open'", "PYTHON_9.3")
        arcpy.CalculateField_management("amenity_lyr", "AccessMult", 1.0, "PYTHON_9.3")

        # Designated sites, e.g. country parks, millennium and doorstep greens, local and national nature reserves
        for designation in des_list:
            arcpy.MakeFeatureLayer_management(base_map + "_PA", "des_lyr")
            arcpy.SelectLayerByAttribute_management("des_lyr", where_clause=designation + " = 1")
            numrows = arcpy.GetCount_management("des_lyr")
            print ("      Designation: " + designation + " Rows: " + str(numrows))
            if numrows >0:
                arcpy.CalculateField_management("des_lyr", "PAType", "'" + designation + "'", "PYTHON_9.3")
                # Special case for National Trust where description states degree of access
                if designation == "NT":
                    arcpy.CalculateField_management("des_lyr", "PADescription", "!NT_desc!", "PYTHON_9.3")
                else:
                    arcpy.CalculateField_management("des_lyr", "PADescription", "'" + designation + "'", "PYTHON_9.3")

                arcpy.AddJoin_management("des_lyr", "PADescription", AccessTable, "Description", "KEEP_ALL")
                arcpy.CalculateField_management("des_lyr", "Source", "'Designations'", "PYTHON_9.3")
                arcpy.CalculateField_management("des_lyr", "AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
                arcpy.CalculateField_management("des_lyr", "AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
                arcpy.RemoveJoin_management("des_lyr", AccessTable_name)
            arcpy.Delete_management("des_lyr")

        # Green spaces (from OS green space and OS open green space) - correct for Rail in OSGS Amenity residential
        # Exclude National Trust as that has better information on access, so we don't want to overwrite it
        arcpy.MakeFeatureLayer_management(base_map + "_PA", "sel_lyr4")
        expression = "GreenSpace IS NOT NULL AND GreenSpace <> '' AND DescriptiveGroup NOT LIKE '%Rail%' AND (NT IS NULL OR NT = 0)"
        arcpy.SelectLayerByAttribute_management("sel_lyr4", where_clause=expression)
        if arcpy.GetCount_management("sel_lyr4") > 0:
            arcpy.CalculateField_management("sel_lyr4", "PAType", "!GreenSpace!", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "PADescription", "!GreenSpace!", "PYTHON_9.3")
            arcpy.AddJoin_management("sel_lyr4", "PADescription", AccessTable, "Description", "KEEP_ALL")
            arcpy.CalculateField_management("sel_lyr4", "Source", "'GreenSpace'", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
            arcpy.CalculateField_management("sel_lyr4", "AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
            arcpy.RemoveJoin_management("sel_lyr4", AccessTable_name)
        arcpy.Delete_management("sel_lyr4")

        # Correction for school grounds from OSGS because playing fields were omitted (this will omit non-urban schools not in OSGS)
        arcpy.MakeFeatureLayer_management(base_map + "_PA", "school_lyr")
        arcpy.SelectLayerByAttribute_management("school_lyr", where_clause="OSGS_priFunc = 'School Grounds'")
        if arcpy.GetCount_management("school_lyr") > 0:
            arcpy.CalculateField_management("school_lyr", "PAType", "'School Grounds'", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "PADescription", "'School Grounds'", "PYTHON_9.3")
            arcpy.AddJoin_management("school_lyr", "PADescription", AccessTable, "Description", "KEEP_ALL")
            arcpy.CalculateField_management("school_lyr", "Source", "'OSGS'", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "AccessType", "!" + AccessTable_name + ".AccessType!", "PYTHON_9.3")
            arcpy.CalculateField_management("school_lyr", "AccessMult", "!" + AccessTable_name + ".AccessMult!", "PYTHON_9.3")
            arcpy.RemoveJoin_management("school_lyr", AccessTable_name)
        arcpy.Delete_management("school_lyr")

    # if correct:
    #     # Green spaces (from OS green space and OS open green space) - correct for Rail in OSGS Amenity residential
    #     arcpy.MakeFeatureLayer_management(base_map + "_PA", "sel_lyr4")
    #     expression = "GreenSpace IS NOT NULL AND GreenSpace <> '' AND DescriptiveGroup LIKE '%Rail%'"
    #     arcpy.SelectLayerByAttribute_management("sel_lyr4", where_clause=expression)
    #     if arcpy.GetCount_management("sel_lyr4") > 0:
    #         arcpy.CalculateField_management("sel_lyr4", "GreenSpace", "'Amenity - Transport'", "PYTHON_9.3")
    #         arcpy.CalculateField_management("sel_lyr4", "PAType", "''", "PYTHON_9.3")
    #         arcpy.CalculateField_management("sel_lyr4", "PADescription", "''", "PYTHON_9.3")
    #         arcpy.CalculateField_management("sel_lyr4", "Source", "''", "PYTHON_9.3")
    #         arcpy.CalculateField_management("sel_lyr4", "AccessType", "''", "PYTHON_9.3")
    #         arcpy.CalculateField_management("sel_lyr4", "AccessMult", 0, "PYTHON_9.3")
    #     arcpy.Delete_management("sel_lyr4")

    if tidy_fields:
        MyFunctions.tidy_fields(base_map + "_PA")

    if tidy_workspace and (method == "CROME_PHI"):   # Not set up yet for Oxon gdb used for HLU method
        fcs = arcpy.ListFeatureClasses("*")
        delete_fcs = []
        for fc in fcs:
            if fc not in keep_fcs and "NatCap_" not in fc:
                delete_fcs.append (fc)
                # print("Deleting " + fc + " from " + gdb)
                if len(delete_fcs) > 0:
                    arcpy.Delete_management (fc)
        if len(delete_fcs) > 0:
            print("   Deleted intermediate feature classes: " + ', '.join(delete_fcs))

    print(''.join(["Completed " + gdb + " on : ", time.ctime()]))
exit()