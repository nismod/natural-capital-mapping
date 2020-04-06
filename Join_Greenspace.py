# Merges land use map with OS green space and OS open green space layers
# Create OSGS dataset from tiles (this covers all GS including gardens and amenity, but only in urban areas):
# -	Loop through all OSGS tiles
# -	Select all rows except gardens and amenity.
# -	Append to first file
# -	Clip to boundaries
# Join OSGS pri Func to base map on TOID.
# Link to OS Open GS (this covers main GS types e.g. allotments, cemeteries, including both urban and rural, but not gardens etc)
# -	Remove GS already covered by OSGS - clip out by dissolved area of OSGS. This creates slivers where edges do not match.
# -	Tabulate intersection for Open GS with base map and sort by size so that slivers will be ignored
# - Join (to largest polygon) where overlap >50%
# -	Consolidate and interpret the two GS sources and modify habitat where appropriate
# ----------------------------------------------------------------------
import time
import arcpy
import os
import MyFunctions

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

# Choose whether to do this for just Oxon or the Ox-Cam Arc
# region = "Arc"
region = "Oxon"
# Choice of method that has been used to generate the input files - this determines location and names of input files
# method = "LCM_PHI"
method = "HLU"

# Folder containing multiple OS Greenspace shapefile tiles to be joined together
OSGS_folder = r"D:\cenv0389\Oxon_GIS\OxCamArc\OSGS"
OSGS = os.path.join(OSGS_folder, "OS_greenspace.shp")
Open_GS = r"D:\cenv0389\Oxon_GIS\OxCamArc\OS_openGS_Arc.shp"

# Geodatabase containing the base map and where the outputs will go
if region == "Oxon" and method == "HLU":
    work_folder = r"D:\env0389\Oxon_GIS\Oxon_county\NaturalCapital"
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb"]
    Base_map_name = "OSMM_HLU_CR_ALC_Des"
    boundary = "Oxfordshire"
    Hab_field = "Interpreted_habitat"
elif region == "Arc" or (region == "Oxon" and method == "LCM_PHI"):
    work_folder = r"D:\cenv0389\Oxon_GIS\OxCamArc"
    arcpy.env.workspace = work_folder
    if region == "Arc":
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(work_folder, LAD))
    Base_map_name = "OSMM_LCM_PHI_ALC_Desig"
    boundary = "boundary"
    Hab_field = "Interpreted_habitat"

# Which parts of the code do we want to run? For debugging or updating
merge_GS_files = False
clip_GS_files = False
copy_base_map = True
join_OSGS = True
clip_openGS = True
join_openGS =  True
interpret_GS = True

# Loop through all the OSGS tiles in the OSGS folder and merge into a single file
if merge_GS_files:
    print ("Merging all GS files into one")
    arcpy.env.workspace = OSGS_folder
    ifile = 0
    for file in arcpy.ListFiles("*_GreenspaceArea.shp"):
        ifile = ifile + 1
        # Select all rows except gardens (and optionally amenity) - we don't need those
        arcpy.MakeFeatureLayer_management(file, "sel_lyr")
        # expression = "priFunc <> 'Private Garden' AND priFunc <> 'Amenity - Transport' AND priFunc <> 'Amenity - Residential Or Business' " \
        #              "AND secFunc <> 'Private Garden' AND secFunc <> 'Amenity - Transport' AND secFunc <> 'Amenity - Residential Or Business'"
        expression = "priFunc <> 'Private Garden' AND secFunc <> 'Private Garden'"
        arcpy.SelectLayerByAttribute_management("sel_lyr", where_clause=expression)
        if ifile == 1:
            arcpy.CopyFeatures_management("sel_lyr", OSGS)
        else:
            arcpy.Append_management("sel_lyr", OSGS)
            numrows = arcpy.GetCount_management(OSGS)
            print("After merging " + str(ifile) + " files, OSGS file contains " + str(numrows) + " rows")
        arcpy.Delete_management("sel_lyr")

for gdb in gdbs:
    arcpy.env.workspace = gdb
    print (''.join(["### Started processing ", gdb, " on : ", time.ctime()]))
    gdb_name = gdb[:-4]
    if copy_base_map:
        print("    Making copy of base map")
        arcpy.CopyFeatures_management(Base_map_name, Base_map_name + "_GS")
    Base_map = Base_map_name + "_GS"
    print ("    " + Base_map + " has " + str(arcpy.GetCount_management(Base_map_name)) + " rows")

    if clip_GS_files:
        print("    Clipping OSGS for " + gdb_name)
        arcpy.Clip_analysis(OSGS, boundary, "OSGS")
        arcpy.Clip_analysis(Open_GS, boundary, "OS_Open_GS")

    if join_OSGS:
        print("    Joining OSGS data")
        print ("      Adding new fields for OSGS functions")
        MyFunctions.check_and_add_field(Base_map, "OSGS_priFunc", "TEXT", 40)
        MyFunctions.check_and_add_field(Base_map, "OSGS_secFunc", "TEXT", 40)

        # Remove first 4 letters from TOID ('osgb')
        MyFunctions.check_and_add_field("OSGS", "TOID_trim", "TEXT", 20)
        arcpy.CalculateField_management("OSGS", "TOID_trim", "!toid![4:]", "PYTHON_9.3")

        # Now join the field
        print ("      Joining OSGS table to base map")
        arcpy.MakeFeatureLayer_management(Base_map, "join_lyr")
        arcpy.AddJoin_management("join_lyr", "TOID", "OSGS", "TOID_trim")

        # Copy over prifunc and secfunc
        print ("      Copying primary and secondary GS functions to base map")
        arcpy.CalculateField_management("join_lyr", "OSGS_priFunc", "!OSGS.priFunc!", "PYTHON_9.3")
        arcpy.CalculateField_management("join_lyr", "OSGS_secFunc", "!OSGS.secFunc!", "PYTHON_9.3")
        arcpy.RemoveJoin_management("join_lyr", "OSGS")
        arcpy.Delete_management("join_lyr")

    if join_openGS:
        # Now join in the Open GS layer. Unlike OSGS, this includes rural GS - but no TOID.
        # Note - there is a lookup table to match OS openGS to OSMM GS, but only about a quarter of the OS OpenGS codes
        # seem to have a matching TOID in the lookup table. Maybe versions do not match due to OSMM updates?
        print ("    Joining Open GS.")
        print("      Copying OBJECTID for base map")
        MyFunctions.check_and_add_field(Base_map, "BaseID_GS", "LONG", 0)
        arcpy.CalculateField_management(Base_map, "BaseID_GS", "!OBJECTID!", "PYTHON_9.3")

        print("      Copying OBJECTID for Open_GS")
        MyFunctions.check_and_add_field("OS_Open_GS", "GSID", "LONG", 0)
        arcpy.CalculateField_management("OS_Open_GS", "GSID", "!OBJECTID!", "PYTHON_9.3")

        if clip_openGS:
            print("      Clipping out OS open GS not already covered by OSGS (i.e. leaving just rural areas)")
            # First dissolve OSGS to get a simple area for clipping
            arcpy.Dissolve_management("OSGS", "OSGS_dissolve")
            arcpy.Erase_analysis("OS_Open_GS", "OSGS_dissolve", "OS_Open_GS_clip")
            print ("      Deleting slivers")
            MyFunctions.delete_by_size("OS_Open_GS_clip", 20)
            MyFunctions.check_and_repair("OS_Open_GS_clip")

        print("      Calculating percentage of base map features within OpenGS polygons")
        arcpy.TabulateIntersection_analysis(Base_map, ["BaseID_GS", Hab_field, "Shape_Area"],
                                            "OS_Open_GS_clip", "GS_TI", ["GSID", "function", "distName1", "Shape_Area"])

        print("      Sorting TI table by GS size so that smaller features are first in the list (e.g. play space on playing field)")
        arcpy.Sort_management("GS_TI", "GS_TI_sort", [["Shape_Area_1", "ASCENDING"]])

        print ("      Adding fields for open GS function and name")
        MyFunctions.check_and_add_field(Base_map, "OpenGS_func", "TEXT", 40)
        MyFunctions.check_and_add_field(Base_map, "OpenGS_name", "TEXT", 100)

        print ("      Joining GS info for base map polygons that are >50% inside GS polygons")
        arcpy.MakeFeatureLayer_management(Base_map, "join_lyr")
        arcpy.AddJoin_management("join_lyr", "BaseID_GS", "GS_TI_sort", "BaseID_GS", "KEEP_ALL")

        print("      Copying GS function and name")
        arcpy.SelectLayerByAttribute_management("join_lyr", where_clause="GS_TI_sort.PERCENTAGE > 50")
        arcpy.CalculateField_management("join_lyr", Base_map + ".OpenGS_func", "!GS_TI_sort.function!", "PYTHON_9.3")
        arcpy.CalculateField_management("join_lyr", Base_map + ".OpenGS_name", "!GS_TI_sort.distName1!", "PYTHON_9.3")

        # Remove the join
        arcpy.RemoveJoin_management("join_lyr", "GS_TI_sort")
        arcpy.Delete_management("join_lyr")

    if interpret_GS:
        # Consolidate GS definitions from OSGS primary and secondary functions and OS openGS
        print ("    Consolidating GS types")
        MyFunctions.check_and_add_field(Base_map, "GreenSpace", "TEXT", 40)
        arcpy.CalculateField_management(Base_map, "Greenspace", "!OSGS_priFunc!", "PYTHON_9.3")

        # Where OSGS secondary functions exist, replace primary with secondary
        MyFunctions.select_and_copy(Base_map, "GreenSpace", "OSGS_secFunc IS NOT NULL AND OSGS_secFunc <> ''", "!OSGS_secFunc!")
        # Where OS openGS exists, copy it across
        MyFunctions.select_and_copy(Base_map, "GreenSpace", "OpenGS_func IS NOT NULL AND OpenGS_func <>''", "!OpenGS_func!")

        # Modify base map habitats for allotments, playing fields, play spaces etc - but only generic areas (not paths, woods, water etc)
        print("    Interpreting habitats with GS")
        generic_natural = "(Interpreted_habitat IN ('Arable', 'Agricultural land', 'Improved grassland', 'Natural surface', " \
                          "'Amenity grassland', 'Cultivated/disturbed land'))"
        expression = generic_natural + " AND GreenSpace = 'Allotments Or Community Growing Spaces'"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,  "'Allotments, city farm, community garden'")

        expression = generic_natural + " AND GreenSpace IN ('Playing Field', 'Other Sports Facility', 'Play Space', 'Tennis Court', " \
                                       "'Bowling Green')"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression, "'Natural sports facility, recreation ground or playground'")

        expression = generic_natural + " AND (GreenSpace = 'Cemetery' OR GreenSpace = 'Religious Grounds')"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Cemeteries and churchyards'")

        expression = generic_natural + " AND GreenSpace = 'Golf Course'"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Golf course'")

        # Replace 'Natural surface' with 'Amenity grassland' - but not for transport (roadside and railside) as not all of this is usable?
        # Also not for 'arable' or 'improved grassland' because much OSGS 'Amenity' is actually farmland around urban areas
        expression = "Interpreted_habitat = 'Natural surface' AND GreenSpace = 'Amenity - Residential Or Business'"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Amenity grassland'")

        # Correct 'Amenity - Residential Or Business' to 'Amenity - Transport' where Rail occurs in DescriptiveGroup (this is an OSGS error)
        expression = "GreenSpace = 'Amenity - Residential Or Business' AND DescriptiveGroup LIKE '%Rail%'"
        MyFunctions.select_and_copy(Base_map, "GreenSpace", expression, "'Amenity - Transport'")

    print("### Completed " + gdb_name + " on : " + time.ctime())

exit()

# Spare code - this approach didn't work
# GSfunctions = ["Playing Field", "Public Park Or Garden", "Religious Grounds", "Golf Course", "Other Sports Facility",
#                    "Allotments Or Community Growing Spaces", "Bowling Green", "Cemetery", "Tennis Court", "Play Space"]
# for GSfunction in GSfunctions:
#     # The order of functions ensures that the more specific function (e.g. play area, tennis courts) appears last and
#     # therefore over-writes more generic functions (e.g. public park; playing fields) where there are multiple layers
#     print ("Selecting polygons with centroids within OS open GS layer for " + GSfunction)
#     arcpy.MakeFeatureLayer_management(Open_GS + "_clip", "func_lyr")
#     arcpy.SelectLayerByAttribute_management("func_lyr", where_clause="function = '" + GSfunction + "'")
#     arcpy.MakeFeatureLayer_management(Base_map, "sel_lyr")
#     arcpy.SelectLayerByLocation_management("sel_lyr", "HAVE_THEIR_CENTER_IN", "func_lyr")
# print("Spatial join to get GS names")
# # Caution: this is a one to many join being treated (by default) as a one to one join. Ideally would sort first.
# arcpy.SpatialJoin_analysis(Base_map, Open_GS + "_clip", Base_map + "_GS", match_option="HAVE_THEIR_CENTER_IN")
# arcpy.CalculateField_management(Base_map + "_GS", "OpenGS_name", "!distName1!", "PYTHON_9.3")
