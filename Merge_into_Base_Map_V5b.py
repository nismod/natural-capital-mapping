## Merges new features into a base map
# -----------------------------------
# Code by Martin Besnier and Alison Smith (Environmental Change Institute, University of Oxford)
# This code is a research tool and has not been rigorously tested for wider use.
# ------------------------------------------------------------------------------
# It merges two polygon datasets together (a base map and a set of new features), while avoiding
# slivers due to boundary mismatch. It identifies polygons in the base map that need to be split
# to match the boundaries of the new features, ignoring minor differences in the boundaries due
# to inaccurate mapping (which would generate slivers). The output is faithful to the base map
# boundaries as far as possible, but minor differences may arise during one of the sliver elimination
# steps.
#
# Enter parameters for workspace, input file names, snap distances etc. in the first section.
# Appropriate snap distances, sliver size and minimum size for splitting polygons will vary
# depending on the datasets, and can be optimised through inspecting the outputs and adjusting
# if necessary. The code is designed to work with OS Mastermap as a base map but could be adapted
# for other base maps. The code expects the base map, input layer and zone boundaries to be in a
# single geodatabase. Existing feature classes with the same name as intermediate files will be
# overwritten if they already exist.
# Supplementary scripts:
# Merge_OSMM_HLU_preprocess.py - pre-processes OS Mastermap and Phase 1 habitat dataset before input
# to this script.
# OSMM_HLU_Interpret.py - takes the output from this script and assigns overall habitat types,
# based on use of OS Mastermap and Phase 1 habitat data.
# ------------------------------------------------------------------------------------------

import time
import arcpy
import os
import MyFunctions
import sys
import traceback

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

# Enter all parameters needed by the code
# ---------------------------------------
# The merge type simply identifies which block of pre-set parameters is selected from those listed below.
# merge_type = "Oxon_OSMM_HLU"
merge_type = "Oxon_Designations"
# merge_type = "CROME_PHI"
# merge_type = "Designations"
# merge_type = "Arc_access"

region = "Oxon"
# region = "Arc"
# region = "NP"
# Special case for LNCP project with LERC data
LNCP_LERC = False

# *** ENTER PARAMETERS HERE. A number of pre-set parameter blocks have been set up for convenience.
# -------------------------------------------------------------------------------------------------
if merge_type == "Oxon_OSMM_HLU":
    # Enter workspace name
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Merge_OSMM_HLU_CR_ALC.gdb"]
    # names for input base map feature class, new features to be merged with base map, and output feature class
    Base_map_name = "OSMM_noLandform"
    New_features = "HLU_preprocessed"
    Output_fc = "OSMM_HLU"
    # short tags (< 8 characters, no spaces) for base map and new features, to be used for naming new fields
    # (to distinguish them from fields added from previous merges).
    base_tag = "OSMM"
    new_tag = "HLU"
    # names of key fields in base map and new features
    base_key = "DescriptiveGroup"
    new_key = "PHASE1HAB"
    # Enter any other fields you want to be included in the Tabulate Intersection tables
    # WARNING Any fields named the same as any of these fields but with a suffix of "_1*" will be deleted as assumed to be duplicates.
    base_TI_fields = ["TOID", "FID", "DescriptiveTerm", "Make"]
    new_TI_fields = ["POLYID", "S41HABITAT"]
    # Enter list of all fields in the base map that need to be kept
    Needed = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make",
              "primary_key", "fid", "versiondate", "theme", "descriptivegroup", "descriptiveterm", "make"]
    # Significant area - polygons will be split if the intersect between base map and new features is larger than this area
    significant_size = 200
    # Distances to snap new feature edges and vertices to base map. If too high, get distortions; if too low get slivers and messy edges
    # Should not be needed if new features exactly match base map features. Currently set up for a two-stage snap as this produces much
    # better results (33,000 out of 86,000 HLU polygons matching OSMM as opposed to about 3,000!)
    snap_env = [[Base_map_name, "VERTEX", "0.5 Meters"], [Base_map_name, "EDGE", "1 Meters"], [Base_map_name, "VERTEX", "1 Meters"]]
elif merge_type == "Oxon_Designations":
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Merge_Designations.gdb"]
    Base_map_name = "OSMM_HLU_CR_ALC"
    New_features = "Designations"
    Output_fc = "OSMM_HLU_CR_ALC_Desig"
    base_tag = "Base"
    new_tag = "Desig"
    base_key = "Interpreted_habitat"
    new_key = "Type"
    base_TI_fields = []
    new_TI_fields = ["Name"]
    Needed = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make",
              "primary_key", "fid", "versiondate", "theme", "descriptivegroup", "descriptiveterm", "make",
              "POLYID", "PHASE1HAB", "S41HABITAT", "S41HAB2",
              "SITEREF", "COPYRIGHT", "VERSION", "OSMM_hab", "HLU_hab", "Interpreted_habitat", "CROME_desc", "CROME_simple", "ALC_GRADE"]
    significant_size = 500
    snap_env = [[Base_map_name, "EDGE", "0.5 Meters"], [Base_map_name, "VERTEX", "0.5 Meters"]]
elif merge_type == "CROME_PHI":
    if region == "Arc" or region == "Oxon":
        folder = r"D:\cenv0389\OxCamArc\LADs"
    elif region == "NP":
        folder = r"M:\urban_development_natural_capital\LADs"
    else:
        print "Region not found"
        exit()
    arcpy.env.workspace = folder
    if region == "Arc":
        # gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        gdbs = []
        gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
        gdbs.append(os.path.join(folder, "Chiltern.gdb"))
        gdbs.append(os.path.join(folder, "SouthOxfordshire.gdb"))
        gdbs.append(os.path.join(folder, "Oxford.gdb"))
        gdbs.append(os.path.join(folder, "Wycombe.gdb"))

    elif region == "NP":
        # CROME_North dataset done: "NewcastleuponTyne.gdb", "NorthTyneside.gdb", "SouthTyneside.gdb",
        #                 "Sunderland.gdb",  "Gateshead.gdb", "Darlington.gdb", "Stockton-on-Tees.gdb", "Hartlepool.gdb",
        #                 "Middlesbrough.gdb", "RedcarandCleveland.gdb", "Allerdale.gdb", "Eden.gdb", "Northumberland.gdb",
        #                 "CountyDurham.gdb", "Carlisle.gdb"
        # CROME_East dataset: done. Add back  "Leeds.gdb" if re-doing .
        # LADs = ["Barnsley.gdb", "Doncaster.gdb", "Rotherham.gdb", "North Lincolnshire.gdb", "North East Lincolnshire.gdb",
        #         "Scarborough.gdb", "Selby.gdb", "Sheffield.gdb", "Wakefield.gdb", "York.gdb", "Richmondshire.gdb",
        #         "Hambleton.gdb", "Harrogate.gdb", "Ryedale.gdb", "East Riding of Yorkshire.gdb"]
        # CROME_North_West dataset done
        # LADs = ["Lancaster.gdb", "Pendle.gdb", "Ribble Valley.gdb", "Wyre.gdb", "Barrow-in-Furness.gdb", "Bradford.gdb", "Copeland.gdb",
        #         "Craven.gdb", "South Lakeland.gdb"]
        # CROME_West dataset Done
        # "Blackburn with Darwen.gdb", "Blackpool.gdb", "Bolton.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb",
        #                 "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Fylde.gdb", "Halton.gdb", "Hyndburn.gdb",
        #                 "Kirklees.gdb", "Knowsley.gdb", "Liverpool.gdb", "Manchester.gdb", "Oldham.gdb", "Preston.gdb", "Rochdale.gdb",
        #                 "Rossendale.gdb","Salford.gdb", "South Ribble.gdb", "Sefton.gdb", "Stockport.gdb", "St Helens.gdb", "Tameside.gdb",
        #                 "Trafford.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wirral.gdb"]
        LADs = ["Copeland.gdb"]
        gdbs = []
        for LAD in LADs:
            LAD_name = LAD.replace(" ", "")
            gdbs.append(os.path.join(folder, LAD_name))

    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))

    Base_map_name = "OSMM_CROME"
    New_features = "PHI"
    Output_fc = "OSMM_CROME_PHI"
    base_tag = "OSMM_CROME"
    new_tag = "PHI"
    base_key = "Interpreted_habitat"
    new_key = "PHI"
    base_TI_fields = ["fid"]
    new_TI_fields = ["WPP", "OMHD"]
    Needed = ["TOID", "DescriptiveGroup", "DescriptiveTerm", "Make",
              "primary_key", "fid", "versiondate", "theme", "descriptivegroup", "descriptiveterm", "make",
              "OSMM_hab", "Interpreted_habitat", "CROME_desc", "CROME_simple"]
    significant_size = 200
    snap_env = [[Base_map_name, "VERTEX", "0.5 Meters"], [Base_map_name, "EDGE", "1 Meters"], [Base_map_name, "VERTEX", "1 Meters"]]
elif merge_type == "Designations":
    # Folder containing gdbs to process and names of gdbs to process
    if region == "Arc":
        folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
        arcpy.env.workspace = folder
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        # gdbs = []
        # gdbs.append(os.path.join(folder, "AylesburyVale.gdb"))
    elif region == "NP":
        folder = r"M:\urban_development_natural_capital\LADs"
        arcpy.env.workspace = folder
        # "Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb", "Bolton.gdb",
        #  "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb",  "Carlisle.gdb", "Cheshire East.gdb", "Cheshire West and Chester.gdb",
        #  "Chorley.gdb",  "Copeland.gdb", "County Durham.gdb", "Craven.gdb", "Darlington.gdb",
        # "Doncaster.gdb",  "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb", "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb"
        # "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb", "Lancaster.gdb", "Liverpool.gdb", "Manchester.gdb",
        # "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",  "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb",
        # "North Tyneside.gdb", "Oldham.gdb",
        # "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb", "Richmondshire.gdb",
        # "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb", "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb",
        # "South Lakeland.gdb", "South Ribble.gdb", "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
        # Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wyre.gdb", "York.gdb",

        LADs = [ "Copeland.gdb"]

        gdbs = []
        for LAD in LADs:
            LAD_name = LAD.replace(" ", "")
            gdbs.append(os.path.join(folder, LAD_name))
    elif region == "Oxon":
        folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Natural_capital\LADs"
        gdbs = []
        # *** Not set up yet - so far have just done whole county - see above under option 'Oxon_designations'!!
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
    # Location of input file containing designations
    if region == "Oxon" or region == "Arc":
        New_in = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Union_Designations.gdb\Designations_tidy"
    elif region == "NP":
        New_in = r"M:\urban_development_natural_capital\Data.gdb\Designations_tidy"
    New_features = "Designations"
    if LNCP_LERC:
        Base_map_name = "LERC_ALC"
        Output_fc = "LERC_ALC_Desig"
        Needed = ["Toid", "DescGroup", "DescTerm", "make", "GI_type", "LWS_p", "AccessGI", "LCM_type", "GI_Type_Final",
                  "Accessible", "Ph1code", "Ph1code_1", "Ph1code_12", "HabNmPLUS_1", "HabBroad_1", "Ph1ColBestFit", "HabType2_1",
                  "Interpreted_habitat", "ALC_GRADE"]
    else:
        Base_map_name = "OSMM_CR_PHI_ALC"
        Output_fc = "OSMM_CR_PHI_ALC_Desig"
        Needed = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make",
                  "primary_key", "fid", "versiondate", "theme", "descriptivegroup", "descriptiveterm", "make",
                  "OSMM_hab", "CROME_desc", "CROME_simple", "PHI", "WPP", "OMHD", "Interpreted_habitat", "ALC_GRADE"]
    base_tag = "Base"
    new_tag = "Desig"
    base_key = "Interpreted_habitat"
    new_key = "Type"
    base_TI_fields = []
    new_TI_fields = ["Name"]
    significant_size = 500
    snap_env = [[Base_map_name, "EDGE", "0.5 Meters"], [Base_map_name, "VERTEX", "0.5 Meters"]]

elif merge_type == "Arc_access":
    # Not used: by default, the public access layer is just intersected in Public_access.py instead of being merged properly.
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    arcpy.env.workspace = folder
    gdbs = arcpy.ListWorkspaces("*", "FileGDB")
    Base_map_name = "OSMM_LCM_PHI_ALC_Desig_GS"
    New_in = os.path.join(folder, "Data\Public_access.gdb\Public_Access_noGS")
    New_features = "Access"
    Output_fc = "OSMM_LCM_PHI_ALC_Desig_access_merge"
    base_tag = "Base"
    new_tag = "Access"
    base_key = "Interpreted_Habitat"
    new_key = "PAType"
    base_TI_fields = []
    new_TI_fields = ["PADescription", "PAName", "Source", "AccessType", "AccessMult"]
    Needed = []
    Needed_fields = arcpy.ListFields(os.path.join(folder, "AylesburyVale.gdb", Base_map_name))
    for field in Needed_fields:
        Needed.append (field.name)
    significant_size = 200
    snap_env = [[Base_map_name, "VERTEX", "0.5 Meters"], [Base_map_name, "EDGE", "1 Meters"], [Base_map_name, "VERTEX", "1 Meters"]]
else:
    print("Error - merge type not defined")
    exit()

# CAUTION: Provide the name of the Index fields. This is usually but not always OBJECTID. Check aliases!
if LNCP_LERC:
    BaseIndexID = "OBJECTID_1"
else:
    BaseIndexID = "OBJECTID"
NewIndexID = "OBJECTID"

new_ID = new_tag + "_OBJID"
base_ID = base_tag + "_OBJID"
new_area = new_tag + "_Area"
base_area = base_tag + "_Area"
Relationship_field = base_tag + "_Relationship"

# Enter spatial parameters (designed to work in meters or square meters, but will take whatever spatial reference applies to the
# features)
# Sliver size - polygons below this size are eliminated in some steps. Should not be larger than smallest genuine base map or new polygons.
sliver_size = 1
# Separate threshold for small or linear features such as roads, paths, tracks, verges and rivers
significant_size_sml = 50
# Enter percentage overlaps to determine which polygons are split. Polygons with less overlap than ignore_low or greater than
# ignore_high are not split unless they are greater than the significant_area.
ignore_low = 5
# If overlap > ignore_high, interpret as new features (if new and base conflict) CHECK - is this needed?
ignore_high = 95
# Split base feature with new feature if overlap area <  split_overlap * base map polygon area (e.g. 95% of base map polygon area)
split_overlap = 0.95
# XY tolerance for geoprocessing operations. ArcGIs default is 0.001 meters which is usually suitable for OSMM, but for some reason
# this does not always seem to be used, so we specify it explicitly here. Important for reducing slivers and making spatial joins work.
xy_tol = "0.001 Meters"

# Which sections of code do we want to run? For de-bugging or updating - no point repeating sections already completed.
sp_base = False                # Convert input base map to single part
if merge_type == "Designations" or merge_type == "Arc_access" or merge_type == "Arc_access":
    clip_new = True               # Clip new features to exact boundary of region, usually True unless restarting during debugging
else:
    clip_new = False
snap_new_features = False      # No need to snap if input features are consistent with base map geometry
tabulate_intersections = True
make_joint_shapes = True
repair_before_elim = True    # This may not be needed
join_new_attributes = True

# Main code
# -------------------------
i = 0
failed_gdbs = []
error_messages = []
for gdb in gdbs:
    arcpy.env.workspace = gdb
    Base_map = Base_map_name
    i = i + 1
    print (''.join(["## Started processing ", gdb, " which is number " + str(i) + " out of " + str(len(gdbs)) + " on : ", time.ctime()]))

    # Temporary correction
    # MyFunctions.select_and_copy(Base_map, "Interpreted_habitat", "Interpreted_habitat = 'Saline lagoons'", "'Coastal lagoons'")
    # # This one added at a later stage, also added to JoinGreenspace to pick up early gdbs (before County Durham)
    # MyFunctions.select_and_copy(Base_map, "Interpreted_habitat", "descriptiveterm IS NULL AND descriptivegroup = 'Tidal Water'",
    #                             "'Saltwater'")
    if sp_base:
        numrows = arcpy.GetCount_management(Base_map)
        print("   Converting base map to single part. " + str(numrows) + " features present initially.")
        arcpy.MultipartToSinglepart_management(Base_map, Base_map + "_sp")
        numrows = arcpy.GetCount_management(Base_map + "_sp")
        print("   " + str(numrows) + " features present after conversion of " + Base_map + " to single part.")
    # If this step is omitted during debugging, the code later on needs to know that Base_map now = Base_map_sp
    Base_map = Base_map + "_sp"

    if clip_new:
        # Clip new features to match the area boundary
        print ("   Clipping new features")
        numrows = arcpy.GetCount_management(New_in)
        print("   " + str(numrows) + " features present in new feature input file")
        numrows = arcpy.GetCount_management("boundary")
        print("   " + str(numrows) + " features present in boundary file")
        arcpy.Clip_analysis(New_in, "boundary", New_features)

    try:
        msgs = ""
        pymsgs = ""
        # Snapping and cleaning new features to match base map features when similar. Takes about 10 hours for Oxon OSMM.
        # ------------------------------------------------------------------------------------------------------------
        if snap_new_features:
            # Snapping new features to be closer to base map
            # Start of section that needs to be commented out if you need to snap manually in ArcMAP
            print("   Snapping new features to fit base map features better. New feature rows: " + str(arcpy.GetCount_management(New_features)))
            print("     Creating snap layer")
            arcpy.CopyFeatures_management(New_features, "New_snap")
            arcpy.MakeFeatureLayer_management("New_snap", "Snap_layer")
            # Only snap features that are not already identical
            arcpy.SelectLayerByLocation_management("Snap_layer", "are_identical_to", Base_map, invert_spatial_relationship="INVERT")

            # Optional densify currently disabled - makes snap take much longer.
            # print("   Densifying new features")
            # arcpy.Densify_edit("Snap_layer", "DISTANCE", "1")

            print("     Snapping - takes about 15 mins for OSMM-PHI for a LAD, 12 hours for OSMM-Phase 1 habitats in Oxfordshire, "
                  "70 minutes for merging in Oxfordshire designations")
            arcpy.Snap_edit("Snap_layer", snap_env)
            arcpy.Delete_management("Snap_layer")
            # End of section that needs to be commented out if you have to snap manually in ArcMAP

            print(''.join(["   ## Snapping completed on : ", time.ctime()]))

            # Correcting slivers and overlaps after the snap. Overlaps occur because we only snap non-identical features. Could change this?
            print("   Correcting overlaps after snapping")
            MyFunctions.check_and_repair("New_snap")
            print("   Unioning. If this fails with an exit code, read the comments in the script for help.")
            # Have had mysterious problem here (error 999999, Table not found, Topology error, Duplicate segment) or
            # 'Process finished with exit code -1073741819 (0xC0000005)' even when the process has worked correctly before with the same data!
            # Sometimes it will work in ArcMap instead (try not entering a numerical rank or cluster tolerance)
            # If the designation data and base map polygons have not changed, you can set 'snap_new_features' to false and omit
            # this part of the code. Sometimes it then crashes at Tabulate Intersection as well but this can be done manually in ArcMap.
            union_failed = True
            arcpy.Union_analysis([["New_snap", 1]], "New_snap_union", "NO_FID", cluster_tolerance=xy_tol)
            union_failed = False
            arcpy.MultipartToSinglepart_management("New_snap_union", "New_snap_union_sp")

            print("      Deleting identical polygons after snap and union")
            arcpy.CopyFeatures_management("New_snap_union_sp", "New_snap_union_sp_delid")
            arcpy.DeleteIdentical_management("New_snap_union_sp_delid", ["Shape"])

            print("      Eliminating slivers after snap and union")
            arcpy.MakeFeatureLayer_management("New_snap_union_sp_delid", "Elim_layer")
            arcpy.SelectLayerByAttribute_management("Elim_layer", where_clause="Shape_Area < " + str(sliver_size) )
            arcpy.Eliminate_management("Elim_layer", "New_snap_union_sp_delid_elim")
            arcpy.Delete_management("Elim_layer")

            print("      Deleting remaining standalone slivers")
            arcpy.CopyFeatures_management("New_snap_union_sp_delid_elim", "New_snap_union_sp_delid_elim_del")
            arcpy.MakeFeatureLayer_management("New_snap_union_sp_delid_elim_del", "Del_layer")
            arcpy.SelectLayerByAttribute_management("Del_layer", where_clause="Shape_Area < " + str(sliver_size) )
            arcpy.DeleteFeatures_management("Del_layer")
            arcpy.Delete_management("Del_layer")
            arcpy.CopyFeatures_management("New_snap_union_sp_delid_elim_del", "New_snap_clean")
            MyFunctions.check_and_repair("New_snap_clean")

        # Deciding which polygons to split, to incorporate new feature boundaries
        # -----------------------------------------------------------------------
        if tabulate_intersections == True:

            # Save ObjectID to separate field as this will be used later (also area, just for info). Check first to see if new fields already added.
            print "   ## Tabulating intersections"
            print("      Saving new feature Index IDs and areas")
            MyFunctions.check_and_add_field("New_snap_clean", new_ID, "LONG", 0)
            arcpy.CalculateField_management("New_snap_clean", new_ID, "!" + NewIndexID + "!", "PYTHON_9.3")

            MyFunctions.check_and_add_field("New_snap_clean", new_area, "FLOAT", 0)
            arcpy.CalculateField_management("New_snap_clean", new_area, '!Shape_Area!', "PYTHON_9.3")

            print("      Saving base map Index IDs and areas")
            MyFunctions.check_and_add_field(Base_map, base_ID, "LONG", 0)
            arcpy.CalculateField_management(Base_map, base_ID, "!" + BaseIndexID + "!", "PYTHON_9.3")

            MyFunctions.check_and_add_field(Base_map, base_area, "FLOAT", 0)
            arcpy.CalculateField_management(Base_map, base_area, '!Shape_Area!', "PYTHON_9.3")

            print("      Calculating percentage areas of new features within each base map polygon")
            arcpy.TabulateIntersection_analysis(Base_map, [base_ID, base_key, base_TI_fields, base_area],
                                                "New_snap_clean", "Base_TI", [new_ID, new_key, new_TI_fields, new_area],
                                                xy_tolerance=xy_tol)

            # Decide which polygons to split, based on the percentage of overlap and the absolute area of the overlap
            # Also decide whether the polygon should be interpreted as new feature or base map attributes, in cases where they conflict.
            print("      Interpreting overlaps and deciding which polygons to split")

            # Add Relationship field to identify which polygons to split, which to add new feature information to, and which to retain unchanged
            MyFunctions.check_and_add_field("Base_TI", Relationship_field, "TEXT", 0)

            codeblock = """
def relationship(overlap_area, percent_overlap, ignore_low, ignore_high, significant_size):
    if percent_overlap < ignore_low and overlap_area < significant_size:     # ignore small overlaps
        return "Base"
    elif percent_overlap < ignore_high:  # most overlaps - split the polygon to match the boundary of new features
        return "Split"
    else:
        return "New"                     # very high overlaps - whole polygon is assigned new feature characteristics
"""
            expression = "relationship(!AREA!, !PERCENTAGE!, " + ', '.join([str(ignore_low), str(ignore_high), str(significant_size)]) + ")"
            arcpy.CalculateField_management("Base_TI", Relationship_field, expression, "PYTHON_9.3", codeblock)

            print(''.join(["   ## Interpretation of overlaps completed on : ", time.ctime()]))

        # Combining geometry to create joint shapes, splitting base map polygons where necessary to reflect new features
        # --------------------------------------------------------------------------------------------------------------
        if make_joint_shapes == True:
            print("   ## Combining geometry")

            # Make different versions of the TI table, which we will use for the different joins
            print("      Separating split and unsplit polygons from TI table")
            # Need to copy to a new table, otherwise the join is not robust - it is one to many so can join to a non-split row, even with selection
            arcpy.CopyRows_management("Base_TI", "Base_TI_not_split")
            arcpy.MakeTableView_management("Base_TI_not_split", "Base_TI_split_lyr")
            arcpy.SelectLayerByAttribute_management("Base_TI_split_lyr", where_clause= Relationship_field + " =  'Split'")
            arcpy.CopyRows_management("Base_TI_split_lyr","Base_TI_split")
            arcpy.DeleteRows_management("Base_TI_split_lyr")
            arcpy.Delete_management("Base_TI_split_lyr")

            # Sort the non-split TI table by size, and then delete identical base map IDs so that only the largest intersection is left.
            # This should avoid problems with one-to-many joins accidentally joining slivers instead of the main new feature later.
            # These are un-split polygons so we only want data from one new feature (the largest intersection) per base map ID.
            # Need to use relationship (base or new / split) to distinguish slivers from new features that occupy almost the whole polygon
            print("      Sorting un-split TI table by size so that polygons join to the correct feature")
            arcpy.Sort_management("Base_TI_not_split", "Base_TI_not_split_sort", [["AREA", "DESCENDING"]])
            arcpy.DeleteIdentical_management("Base_TI_not_split_sort",[base_ID])

            print("      Creating joint spatial layer")
            arcpy.CopyFeatures_management(Base_map, "Joint_spatial")

            # Add new fields for the attributes we want to join
            print ("      Adding relationship field")
            MyFunctions.check_and_add_field("Joint_spatial", Relationship_field, "TEXT", 10)

            # Identify which polygons should be split, by joining to the TI table rows marked 'split'.
            print("      Making split polygon layer")
            arcpy.MakeFeatureLayer_management("Joint_spatial","join_lyr")
            # CAUTION: This is a one to many join. Each base map polygon can be overlapped by more than one new feature polygon.
            # Done as Add Join because much quicker than Join Field
            arcpy.AddJoin_management("join_lyr",base_ID, "Base_TI_split", base_ID, "KEEP_ALL")
            # Copy across the interpretation field. Only the first row that matches will be copied across.
            # This is OK to work out whether the base map polygon needs to be split or not, but the ID cannot be used.
            print("      Copying relationship for polygons to be split")
            arcpy.CalculateField_management("join_lyr", "Joint_spatial." + Relationship_field,
                                            "!Base_TI_split." + Relationship_field + "!","PYTHON_9.3")

            # Remove the join
            arcpy.RemoveJoin_management("join_lyr", "Base_TI_split")
            arcpy.Delete_management("join_lyr")

            print("      First join completed (base map)")

            arcpy.CopyFeatures_management("New_snap_clean", "New_snap_clean_spatial")
            # CAUTION: This is a one to many join. Done as join field because there are not so many new features, so does not take too long.
            arcpy.JoinField_management("New_snap_clean_spatial", new_ID, "Base_TI_split", new_ID, [Relationship_field])
            print("      Second join completed (new features)")

            print("      Clipping")
            arcpy.MakeFeatureLayer_management("Joint_spatial", "Joint_lyr")
            arcpy.SelectLayerByAttribute_management("Joint_lyr", where_clause=Relationship_field + " = 'Split'")
            arcpy.MakeFeatureLayer_management("New_snap_clean_spatial", "clip_lyr")
            arcpy.Clip_analysis("clip_lyr", "Joint_lyr", "Joint_spatial_clip", cluster_tolerance=xy_tol)
            arcpy.Delete_management("clip_lyr")

            print("      Unioning clipped new features with the base map polygons that they split")
            arcpy.Union_analysis([["Joint_lyr", 1], ["Joint_spatial_clip", 1]], "Joint_spatial_clip_union", "NO_FID",
                                 cluster_tolerance=xy_tol)
            arcpy.Delete_management("Joint_lyr")

            # CAUTION: There are now two copies of the Relationship field - one from the one from the unioned base map with all rows 'split'
            # and one from the clipped new features, with some polygons marked 'split' and some either null or blank.

            # Some of the split polygons may have a large part that was tagged 'new' (because the overlap percentage was very high
            # but there were also smaller parts of the same polygon that were tagged for splitting because they exceeded the significant size).
            # So we now want to match the non-split parts of these polygons (joined in via the Union) with the correct
            # ID from the TI table, so that attributes can be transferred later. We do this by sorting both the TI tables and
            # the unioned clip file by size, so that the split polygon parts are matched with the intersections of the same size.
            arcpy.Sort_management("Joint_spatial_clip_union", "Joint_spatial_clip_union_sort", [["Shape_Area", "DESCENDING"]])
            arcpy.MakeFeatureLayer_management("Joint_spatial_clip_union_sort", "join_lyr2")
            arcpy.AddJoin_management("join_lyr2", base_ID, "Base_TI_not_split_sort", base_ID, "KEEP_ALL")
            expression = "Joint_spatial_clip_union_sort." + new_key + " IS NULL OR Joint_spatial_clip_union_sort." + new_key + " = ''"
            arcpy.SelectLayerByAttribute_management("join_lyr2", where_clause=expression)

            # Copy the new feature ID across
            arcpy.CalculateField_management("join_lyr2", "Joint_spatial_clip_union_sort." + new_ID,
                                            "!Base_TI_not_split_sort." + new_ID + "!", "PYTHON_9.3")

            # Remove the join
            arcpy.RemoveJoin_management("join_lyr2", "Base_TI_not_split_sort")
            arcpy.Delete_management("join_lyr2")

            print(''.join(["   ## New polygon file created on : ", time.ctime()]))

            print("   Cleaning clipped shapes")
            arcpy.CopyFeatures_management("Joint_spatial_clip_union","Joint_spatial_clip_union_delid")
            arcpy.DeleteIdentical_management("Joint_spatial_clip_union_delid", ["Shape"])
            arcpy.MultipartToSinglepart_management("Joint_spatial_clip_union_delid", "Joint_spatial_clip_union_delid_sp")

            # Eliminate slivers. Note: this may lose integrity of original base map boundaries, e.g. losing genuine small OSMM polygons.
            # But cannot just delete, or will get odd slivers in middle of new features with no attribute data.
            # For OSMM base map, need to restrict this to 1m2, but that also restricts the size of the standalone sliver deletion below,
            # which ideally would be larger (say 5m2).
            if repair_before_elim:
                MyFunctions.check_and_repair("Joint_spatial_clip_union_delid_sp")
            print("      Eliminating spatial clip slivers. Note: this may lose integrity of original base map boundaries.")
            arcpy.MakeFeatureLayer_management("Joint_spatial_clip_union_delid_sp", "Elim_layer")
            arcpy.SelectLayerByAttribute_management("Elim_layer", where_clause="Shape_Area < " + str(sliver_size))
            arcpy.Eliminate_management("Elim_layer","Joint_spatial_clip_union_delid_sp_elim")
            arcpy.Delete_management("Elim_layer")

            print("      Deleting standalone clip slivers")
            arcpy.CopyFeatures_management("Joint_spatial_clip_union_delid_sp_elim", "Joint_spatial_clip_union_clean")
            arcpy.MakeFeatureLayer_management("Joint_spatial_clip_union_clean", "Del_layer")
            arcpy.SelectLayerByAttribute_management("Del_layer", where_clause="Shape_Area < " + str(sliver_size))
            arcpy.DeleteFeatures_management("Del_layer")
            arcpy.Delete_management("Del_layer")

            # Create a tag to identify the unioned parts of the split polygons that are not within the new features. This is needed later.
            arcpy.MakeFeatureLayer_management("Joint_spatial_clip_union_clean", "tag_lyr")
            arcpy.SelectLayerByAttribute_management("tag_lyr", where_clause=new_ID + " IS NULL OR " + new_ID + " = 0")
            arcpy.CalculateField_management("tag_lyr", Relationship_field, "'Not new'", "PYTHON_9.3")

            print(''.join(["   ## New polygon file cleaned on : ", time.ctime()]))

            print("   Creating Joint layer with base map polygons split where needed")
            # Merge the clipped new features (unioned with the split base map polygons) with the base map with the new shapes erased.
            # This produces new internal boundaries for polygons that need to be split.
            arcpy.Erase_analysis(Base_map, "Joint_spatial_clip_union_clean", "Joint_spatial_erase", cluster_tolerance=xy_tol)
            arcpy.Merge_management(["Joint_spatial_erase", "Joint_spatial_clip_union_clean"], "Joint_spatial_merge")

            arcpy.CopyFeatures_management("Joint_spatial_merge", "Joint_spatial_merge_repair")
            MyFunctions.check_and_repair("Joint_spatial_merge_repair")

            print("   Converting to single part")
            arcpy.MultipartToSinglepart_management("Joint_spatial_merge_repair","Joint_spatial_merge_repair_sp")

            print(''.join(["   ## Joint geometry file created on : ", time.ctime()]))

        # Join new attributes to new joint shapes.
        # -------------------------------------------
        if join_new_attributes == True:
            # We retain the base map attributes in the clipped and merged shapes, but now need to add in new feature attributes
            # from the non-split shapes via a table join.
            print("   Transferring attribute data from new features to joint layer, for non-split polygons")

            # Make a copy of the output joint file to work with, sorted by size. The rows to be joined will be extracted from this layer
            # and joined to the new features, then merged back in. ** This line was commented out, maybe from previous debugging.
            arcpy.Sort_management("Joint_spatial_merge_repair_sp", "Joint_sort", [["Shape_Area", "DESCENDING"]])

            # Get missing new feature IDs for the polygons that have not been split, i.e. the rows with an entry
            # in the TI tables that have not already had a new feature ID transferred. Need to join to largest intersect area, to avoid slivers.

            print("      Joining Joint layer to interpretation table (Base_TI)")
            # This is a one to many join - each base polygon could be overlapped by more than one new feature polygon, but as these polygons
            # were not marked for splitting, we want to use the ID of the largest intersection (just ignoring slivers) so we have sorted by size.
            arcpy.MakeFeatureLayer_management("Joint_sort", "join_lyr5")
            arcpy.AddJoin_management("join_lyr5", base_ID, "Base_TI_not_split_sort", base_ID)

            # Have to do this in two stages, because Relationship <> 'Not new' excludes NULLs.
            expression = "(Joint_sort." + new_ID + " IS NULL OR Joint_sort." + new_ID + \
                         " = 0) AND Base_TI_not_split_sort." + base_ID + " IS NOT NULL"
            arcpy.SelectLayerByAttribute_management("join_lyr5", where_clause=expression)

            # Copy the new feature ID across.
            numrows = arcpy.GetCount_management("join_lyr5")
            print("      Copying new feature ID for " + str(numrows) + " un-split polygons")
            arcpy.CalculateField_management("join_lyr5", "Joint_sort." + new_ID, "!Base_TI_not_split_sort." + new_ID + "!", "PYTHON_9.3")

            # Remove the join
            arcpy.RemoveJoin_management("join_lyr5", "Base_TI_not_split_sort")
            arcpy.Delete_management("join_lyr5")

            # Delete New Id for the rows marked 'not new', i.e. the parts of split polygons that are not in new features
            arcpy.MakeFeatureLayer_management("Joint_sort", "not_new_lyr")
            expression = Relationship_field + " = 'Not new'"
            arcpy.SelectLayerByAttribute_management("not_new_lyr", where_clause=expression)
            numrows = arcpy.GetCount_management("not_new_lyr")
            print("      Deleting new feature ID for " + str(numrows) + " parts of split base map polygons that are not in new features")
            arcpy.CalculateField_management("not_new_lyr", new_ID, 0, "PYTHON_9.3")
            arcpy.Delete_management("not_new_lyr")

            # Get the missing Relationship field for the non_split features
            arcpy.MakeFeatureLayer_management("Joint_sort", "join_lyr6")
            arcpy.AddJoin_management("join_lyr6", base_ID, "Base_TI_not_split_sort", base_ID)
            expression = "(Joint_sort." + new_ID + " IS NOT NULL AND Joint_sort." + new_ID + " <> 0) AND Base_TI_not_split_sort." \
                         + base_ID + " IS NOT NULL"
            arcpy.SelectLayerByAttribute_management("join_lyr6", where_clause=expression)
            numrows = arcpy.GetCount_management("join_lyr6")

            print ("      Copying Relationship for " + str(numrows) + " polygons where new feature ID exists")
            arcpy.CalculateField_management("join_lyr6", "Joint_sort." + Relationship_field,
                                            "!Base_TI_not_split_sort." + Relationship_field + "!", "PYTHON_9.3")
            # Remove the join
            arcpy.RemoveJoin_management("join_lyr6", "Base_TI_not_split_sort")
            arcpy.Delete_management("join_lyr6")

            print("   Selecting rows with missing new attributes")
            arcpy.CopyFeatures_management("Joint_sort", "Joint_sort_OK")
            arcpy.MakeFeatureLayer_management("Joint_sort_OK", "join_lyr9")
            # Select rows where new feature ID exists but the new feature key does not exist. And select only relationship 'New' or 'Split'
            # i.e. ignore those marked 'Base'. Ideally would check to make sure new_key is a string first, otherwise change last part to " <> 0"
            expression = "((" + new_ID + " IS NOT NULL AND " + new_ID + " <> 0) AND (" + Relationship_field + " = 'New' OR "
            expression = expression + Relationship_field + " = 'Split') AND (" + new_key + " IS NULL OR " + new_key + " = ''))"
            arcpy.SelectLayerByAttribute_management("join_lyr9", where_clause=expression)

            numrows = arcpy.GetCount_management("join_lyr9")
            print("   Exporting " + str(numrows) + " new feature rows that still need to be joined to attributes")
            arcpy.CopyFeatures_management("join_lyr9","Joint_to_join")
            print("   Deleting exported features from main dataset")
            arcpy.DeleteFeatures_management("join_lyr9")
            arcpy.Delete_management("join_lyr9")

            print("   Deleting existing new feature attribute fields from features to be joined")
            # Extend the list of fields to keep, to  retain the new interpretation fields
            Needed.extend([base_ID, new_ID, base_area, Relationship_field])
            MyFunctions.delete_fields("Joint_to_join", Needed, "Joint_to_join_delfields")

            print("   Joining to new attributes")
            arcpy.MakeFeatureLayer_management("Joint_to_join_delfields","join_lyr10")
            arcpy.AddJoin_management("join_lyr10", new_ID, "New_snap_clean", new_ID)
            arcpy.CopyFeatures_management("join_lyr10", "Joint_to_join_joined")
            arcpy.Delete_management("join_lyr10")

            # Merge back with main dataset
            numrows = arcpy.GetCount_management("Joint_to_join_joined")
            print ("   Merging " + str(numrows) + " joined rows back into main dataset")
            arcpy.Merge_management(["Joint_sort_OK", "Joint_to_join_joined"], "Joint_done")
            print "   Sorting geographically to improve display speed"
            arcpy.Sort_management("Joint_done", Output_fc, [["SHAPE", "ASCENDING"]], "PEANO")

        print("## Completed " + gdb + " on " + time.ctime() + ". Merged feature class name is " + Output_fc + ", rows: "
              + str(arcpy.GetCount_management(Output_fc)))

    # Error handling: record error messages for this gdb and continue with the next one. Most errors are caused by loss of connection
    # to the server and can be sorted out by restarting the code from an appropriate point
    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        # Return tool error messages for use with a script tool
        arcpy.AddError(msgs)
        # Print tool error messages for use in Python
        print(msgs)

        failed_gdbs.append(gdb)
        error_messages.append(gdb + " failed.\n" + msgs + "\n")
        # if union_failed:
        #     union_msg = "Union failed. Try to do it manually in ArcMap (try omitting rank and cluster tolerance), " \
        #                 "then comment out the previous steps and restart the code."
        #     print union_msg
        #     error_messages.append(union_msg)

    except:
        failed_gdbs.append(gdb)
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]

        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

        # Return Python error messages for use in script tool or Python window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

        # Print Python error messages for use in Python / Python window
        print(pymsg)
        print(msgs)
        failed_gdbs.append(gdb)
        error_messages.append(gdb + " failed.\n" + pymsg + "\n" + msgs + "\n")

    if len(failed_gdbs) >0:
        print "Failed so far: " + '\n'.join(failed_gdbs)
        print "\n".join(error_messages)

exit()