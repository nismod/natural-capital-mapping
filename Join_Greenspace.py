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

# Choose region
# region = "Arc"
# region = "Oxon"
region = "NP"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "LERC"
# method = "HLU"

# Folder containing multiple OS Greenspace shapefile tiles to be joined together
# OSGS_folder = r"D:\cenv0389\Oxon_GIS\OxCamArc\OSGS"
OSGS_folder = r"M:\urban_development_natural_capital\osmm_greenspace\tiles"
OSGS = r"M:\urban_development_natural_capital\osmm_greenspace\OSGS_Feb2021.gdb\OSMM_GS_NP"

# Open GS input file must be a gdb feature class so that there is a Shape_Area field for sorting
# Open_GS_gdb = r"D:\cenv0389\Oxon_GIS\OxCamArc\OSGS\OS_GS.gdb"
Open_GS_gdb = r"D:\cenv0389\UK_data\OS_OpenGS_2019.gdb"
# OS_openGS_in = os.path.join(Open_GS_gdb, "OS_openGS_Arc_in")
# OS_openGS = "OS_openGS_Arc_union"
OS_openGS_in = os.path.join(Open_GS_gdb, "OS_open_greenspace")
OS_openGS = "OS_openGS_NP"

# Geodatabase containing the base map and where the outputs will go
if region == "Oxon" and method == "HLU":
    work_folder = r"D:\env0389\Oxon_GIS\Oxon_county\NaturalCapital"
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb"]
    Base_map_name = "OSMM_HLU_CR_ALC_Des"
    boundary = "Oxfordshire"
    Hab_field = "Interpreted_habitat"
elif region == "NP":
    work_folder = r"M:\urban_development_natural_capital"
    # gdb_names = ["Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
    #              "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb",  "Carlisle.gdb", "Cheshire East.gdb",
    #              "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb", "Craven.gdb", "Darlington.gdb",
    #              "Doncaster.gdb",  "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb", "Halton.gdb",
    #              "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
    #              "Lancaster.gdb", "Liverpool.gdb",
    #              "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb", "North East Lincolnshire.gdb",
    #              "North Lincolnshire.gdb", "Northumberland.gdb",
    #              "North Tyneside.gdb", "Oldham.gdb", "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
    #              "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
    #              "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
    #              "South Tyneside.gdb",
    #              "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb", "Tameside.gdb",
    #              "Northumberland.gdb", "Trafford.gdb",
    #              "Wakefield.gdb", "Warrington.gdb",  "West Lancashire.gdb",
    #              "Wigan.gdb", "Wirral.gdb", "Wyre.gdb", "York.gdb"]
    gdb_names = [ "Leeds.gdb"]
    gdbs = []
    for gdb_name in gdb_names:
        gdbs.append(os.path.join(r"M:\urban_development_natural_capital\LADs",  gdb_name.replace(" ", "")))
    Base_map_name = "OSMM_CR_PHI_ALC_Desig"
    boundary = "boundary"
    # Flag if you only want to correct some habitat definitions that have been set up in OSMM_hab and then copied to a temporary habitat field
    # using Habitat_corrections.py
    correct_habitats = False
    if correct_habitats:
        Hab_field = "Interpreted_habitat_temp"
    else:
        Hab_field = "Interpreted_habitat"
    TOID_field = "fid"
    Base_Index_field = "OBJECTID"
    DescGroup = "descriptivegroup"
elif region == "Arc" or (region == "Oxon" and method == "CROME_PHI"):
    work_folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
    arcpy.env.workspace = work_folder
    if region == "Arc":
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        # gdbs = []
        # gdbs.append(os.path.join(work_folder, "AylesburyVale.gdb"))
        # gdbs.append(os.path.join(work_folder, "Chiltern.gdb"))
        #
        if method == "LERC":
            Base_map_name = "LERC_ALC_Desig"
            TOID_field = "Toid"
            Base_Index_field = "OBJECTID_1"
            DescGroup = "DescGroup"
        else:
            Base_map_name = "OSMM_CR_PHI_ALC_Desig"
            TOID_field = "TOID"
            Base_Index_field = "OBJECTID"
            DescGroup = "DescriptiveGroup"

    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(work_folder, LAD))
        Base_map_name = "OSMM_CR_PHI_ALC_Desig"
        TOID_field = "TOID"
        Base_Index_field = "OBJECTID"
        DescGroup = "DescriptiveGroup"

    boundary = "boundary"
    Hab_field = "Interpreted_habitat"

OpenGS_Index_field = "OBJECTID"

# Which parts of the code do we want to run? For debugging or updating
merge_GS_files = False
prep_openGS = False
clip_OSGS = False
clip_openGS = False
copy_base_map = False
# Need to trim off "osgb" from beginning of toid? Don't need to do this with most recent version of OSGS
trim_toid = False
join_OSGS = False
clip_openGS2 = False
join_openGS = False
interpret_GS = True

# Loop through all the OSGS tiles in the OSGS folder and merge into a single file
if merge_GS_files:
    print ("Merging all GS files into one")
    arcpy.env.workspace = OSGS_folder
    ifile = 0
    print (str(len(arcpy.ListFiles("*_GreenspaceArea.shp"))) + " OSMM greenspace files in directory to be merged")
    for file in arcpy.ListFiles("*_GreenspaceArea.shp"):
        ifile = ifile + 1
        # Select all rows except gardens - we don't need those
        arcpy.MakeFeatureLayer_management(file, "sel_lyr")
        expression = "priFunc <> 'Private Garden' AND secFunc <> 'Private Garden'"
        arcpy.SelectLayerByAttribute_management("sel_lyr", where_clause=expression)
        if ifile == 1:
            arcpy.CopyFeatures_management("sel_lyr", OSGS)
        else:
            arcpy.Append_management("sel_lyr", OSGS)
            numrows = arcpy.GetCount_management(OSGS)
            print("After merging " + str(ifile) + " files, OSGS file contains " + str(numrows) + " rows")
        arcpy.Delete_management("sel_lyr")

if prep_openGS:
    # Prepare Open GS by removing overlapping polygons so that the smaller polygon is retained (e.g. tennis court or bowling green
    # within a park
    arcpy.env.workspace = Open_GS_gdb
    print("    Sorting and unioning open GS to remove overlaps")
    # Sort so that smaller polygons are at the top, then union and delete overlapping polygons
    arcpy.Sort_management(OS_openGS_in, "OS_Open_GS_sort", [["Shape_Area", "ASCENDING"]])
    arcpy.Union_analysis([["OS_Open_GS_sort", 1]], OS_openGS, "ALL")
    arcpy.DeleteIdentical_management(OS_openGS, ["Shape"])

i = 0
for gdb in gdbs:
    i = i + 1
    arcpy.env.workspace = gdb
    print (''.join(["### Started processing ", gdb, " on : ", time.ctime()]) + " This is number " + str(i) + " out of " + str(len(gdbs)))
    gdb_name = gdb[:-4]
    if copy_base_map:
        print("    Making copy of base map")
        arcpy.CopyFeatures_management(Base_map_name, Base_map_name + "_GS")
    Base_map = Base_map_name + "_GS"
    if correct_habitats:
        Base_map = Base_map_name + "_GS_PA"
    print ("    " + Base_map + " has " + str(arcpy.GetCount_management(Base_map_name)) + " rows")

    if clip_OSGS:
        print("    Clipping OSGS for " + gdb_name)
        arcpy.Clip_analysis(OSGS, boundary, "OSGS")
        print (str(arcpy.GetCount_management("OSGS")) + " rows in OSGS")
    if clip_openGS:
        print("    Clipping OS open GS for " + gdb_name)
        arcpy.Clip_analysis(os.path.join(Open_GS_gdb, OS_openGS), boundary, "OS_Open_GS")
        print (str(arcpy.GetCount_management("OS_Open_GS")) + " rows in OS Open_GS")

    if join_OSGS:
        print("    Joining OSGS data")
        print ("      Adding new fields for OSGS functions")
        MyFunctions.check_and_add_field(Base_map, "OSGS_priFunc", "TEXT", 40)
        MyFunctions.check_and_add_field(Base_map, "OSGS_secFunc", "TEXT", 40)

        # Remove first 4 letters from TOID ('osgb') in OSGS layer
        if trim_toid:
            MyFunctions.check_and_add_field("OSGS", "TOID_trim", "TEXT", 20)
            arcpy.CalculateField_management("OSGS", "TOID_trim", "!toid![4:]", "PYTHON_9.3")
            join_field = "TOID_trim"
        else:
            join_field = "toid"

        # Now join the field
        print ("      Joining OSGS table to base map")
        arcpy.MakeFeatureLayer_management(Base_map, "join_lyr")
        arcpy.AddJoin_management("join_lyr", TOID_field, "OSGS", join_field)

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
        print("      Copying Index field for base map")
        MyFunctions.check_and_add_field(Base_map, "BaseID_GS", "LONG", 0)
        arcpy.CalculateField_management(Base_map, "BaseID_GS", "!" + Base_Index_field + "!", "PYTHON_9.3")

        print("      Copying OBJECTID for Open_GS")
        MyFunctions.check_and_add_field("OS_Open_GS", "GSID", "LONG", 0)
        arcpy.CalculateField_management("OS_Open_GS", "GSID", "!" + OpenGS_Index_field + "!", "PYTHON_9.3")

        if clip_openGS2:
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
        # Delete all the rows with overlap less than 50%. Doing this with a temporary selection does not seem to work,
        # as the wrong rows get joined.
        arcpy.MakeTableView_management("GS_TI", "TI_lyr")
        arcpy.SelectLayerByAttribute_management("TI_lyr", where_clause="PERCENTAGE < 50")
        arcpy.DeleteRows_management("TI_lyr")
        arcpy.Delete_management("TI_lyr")

        print ("      Adding fields for open GS function and name")
        MyFunctions.check_and_add_field(Base_map, "OpenGS_func", "TEXT", 40)
        MyFunctions.check_and_add_field(Base_map, "OpenGS_name", "TEXT", 100)

        # Note: this does not seem to work, i.e. the table is sorted OK but then the wrong rows get copied over.
        # So I switched to the alternative approach of deleting all the rows we don't want as above.
        # It should be impossible to have more than one row with an overlap over 50%
        # print("      Sorting TI table by overlap size so that larger overlaps are first in the list")
        # arcpy.Sort_management("GS_TI", "GS_TI_sort", [["AREA", "DESCENDING"]])

        print ("      Joining GS info for base map polygons that are >50% inside GS polygons")
        arcpy.MakeFeatureLayer_management(Base_map, "join_lyr")
        arcpy.AddJoin_management("join_lyr", "BaseID_GS", "GS_TI", "BaseID_GS", "KEEP_ALL")

        print("      Copying GS function and name")
        arcpy.CalculateField_management("join_lyr", Base_map + ".OpenGS_func", "!GS_TI.function!", "PYTHON_9.3")
        arcpy.CalculateField_management("join_lyr", Base_map + ".OpenGS_name", "!GS_TI.distName1!", "PYTHON_9.3")

        # Remove the join
        arcpy.RemoveJoin_management("join_lyr", "GS_TI")
        arcpy.Delete_management("join_lyr")

    if interpret_GS:
        # Consolidate GS definitions from OSGS primary and secondary functions and OS openGS
        if not correct_habitats:
            print ("    Consolidating GS types")
            MyFunctions.check_and_add_field(Base_map, "GreenSpace", "TEXT", 40)
            arcpy.CalculateField_management(Base_map, "Greenspace", "!OSGS_priFunc!", "PYTHON_9.3")

            # Where OSGS secondary functions exist, replace primary with secondary
            MyFunctions.select_and_copy(Base_map, "GreenSpace", "OSGS_secFunc IS NOT NULL AND OSGS_secFunc <> ''", "!OSGS_secFunc!")
            # Where OS openGS exists, copy it across
            MyFunctions.select_and_copy(Base_map, "GreenSpace", "OpenGS_func IS NOT NULL AND OpenGS_func <>''", "!OpenGS_func!")

        # Modify base map habitats for allotments, playing fields, play spaces etc - but only generic areas (not paths, woods, water etc)
        print("    Interpreting habitats with GS")
        generic_natural = "(" + Hab_field + " IN ('Agricultural land', 'Natural surface', 'Amenity grassland', 'Cultivated/disturbed land')"
        generic_natural = generic_natural + " OR " + Hab_field + " LIKE 'Arable%' OR " + Hab_field + " LIKE 'Improved grass%'"
        # Two alternative 'generic natural' definitions, with or without parkland with scattered trees (which is a generic PHI definition)
        # which we want to keep separate for golf courses, cemeteries or religious grounds but not for other types of green space,
        # i.e. there can be patches of parkland with scattered trees within a golf course or cemetery but not within a tennis court, etc.
        # However sometimes this rule does not hold, e.g. there could be a churchyard or cemetery within a large area
        # identified as parkland from PHI. We can't distinguish which is correct.
        generic_natural_1 = generic_natural + ")"
        generic_natural_2 = generic_natural + " OR " + Hab_field + " LIKE 'Parkland%')"
        expression = generic_natural_2 + " AND GreenSpace = 'Allotments Or Community Growing Spaces'"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,  "'Allotments, city farm, community garden'")

        expression = generic_natural_2 + " AND GreenSpace IN ('Playing Field', 'Other Sports Facility', 'Play Space', 'Tennis Court', " \
                                         "'Bowling Green')"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression, "'Natural sports facility, recreation ground or playground'")

        expression = generic_natural_1 + " AND (GreenSpace = 'Cemetery' OR GreenSpace = 'Religious Grounds')"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Cemeteries and churchyards'")

        expression = generic_natural_1 + " AND GreenSpace = 'Golf Course'"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Golf course'")

        # Correct 'Amenity - Residential Or Business' to 'Amenity - Transport' where Rail occurs in DescriptiveGroup (this is an OSGS error)
        expression = "GreenSpace = 'Amenity - Residential Or Business' AND " + DescGroup + " LIKE '%Rail%'"
        MyFunctions.select_and_copy(Base_map, "GreenSpace", expression, "'Amenity - Transport'")

        # Replace 'Natural surface' with 'Amenity grassland' - but not for transport (roadside and railside) as not all of this is usable.
        # Also not for 'arable' or 'improved grassland' because some OSGS 'Amenity' is actually farmland around urban areas
        expression = Hab_field + " = 'Natural surface' AND GreenSpace IN ('Amenity - Residential Or Business', 'Public Park Or Garden')"
        MyFunctions.select_and_copy(Base_map, Hab_field, expression,"'Amenity grassland'")

        # We do not copy over Amenity - Transport because that should be already identified as Road verge from OSMM

    print("### Completed " + gdb_name + " on : " + time.ctime())

exit()