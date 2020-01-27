# Pre-processes OSMM and HLU (Phase 1 habitat) layers prior to calling 'Merge_into_Base_Map.py'.
# -----------------------------------
# Code by Martin Besnier and Alison Smith (Environmental Change Institute, University of Oxford)
# This code is a research tool and has not been rigorously tested for wider use.
# ------------------------------------------------------------------------------
# Optional initial step to clip input files to the exact boundary shape.
# If this step is used, input files must be named HLU_in and OSMM_in, and boundary file
# Oxfordshire should be included in the gdb. Otherwise they should be HLU and OSMM
# ------------------------------------------------------------------------------------------------------------

import time, arcpy
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Set parameters and workspace here
# ---------------------------------
gdb = "C:\Users\cenv0389\Documents\Oxon_GIS\Oxon_county\Merge_OSMM_HLU2.gdb"
arcpy.env.workspace = gdb
OSMM = "OSMM"
HLU = "HLU"
boundary = "Oxfordshire"
# Fields that you want to keep (the rest will get deleted)
OSMM_Needed = ["TOID", "Theme", "DescriptiveGroup", "DescriptiveTerm", "Make"]
HLU_Needed = ["POLY_ID", "PHASE1HABI", "BAP_HABITA", "BAP_HABI00", "SITEREF", "COPYRIGHT", "VERSION"]

# What stages of the code do we want to run? Useful for debugging or updates
clip_to_boundary = False
delete_not_needed_fields = True
delete_and_erase = True
elim_HLU_slivers = True
check = True

# Main code
# ----------
print(''.join(["## Started analysing ", gdb, " on : ", time.ctime()]))

# Optional step: clip input files. Or this could be done before.
if clip_to_boundary:
    print("Clipping " + HLU)
    arcpy.Clip_analysis(HLU + "_in", boundary, HLU)
    print("## Finished clipping " + HLU + "on : " + time.ctime())
    print("Clipping " + OSMM)
    arcpy.Clip_analysis(OSMM + "_in", boundary, OSMM)
    print(''.join(["## Finished clipping OSMM on : ", time.ctime()]))

if delete_not_needed_fields:
    print("Deleting un-necessary fields")
    MyFunctions.delete_fields("OSMM", "OSMM_Needed", "OSMM_delfields")
    MyFunctions.delete_fields("HLU", "HLU_Needed", "HLU_delfields")
    OSMM = "OSMM_delfields"
    HLU = "HLU_delfields"

if delete_and_erase:
    ###  Deleting overlapping "landform" features in OSMM
    print("   Deleting overlapping 'Landform' and 'Pylon' from OSMM")
    arcpy.CopyFeatures_management(OSMM, "OSMM_noLandform")
    arcpy.MakeFeatureLayer_management("OSMM_noLandform", "OSMM_layer")
    expression = "DescriptiveGroup LIKE '%Landform%' OR DescriptiveTerm IN ('Cliff','Slope','Pylon')"
    arcpy.SelectLayerByAttribute_management("OSMM_layer", where_clause=expression)
    arcpy.DeleteFeatures_management("OSMM_layer")
    arcpy.Delete_management("OSMM_layer")

    # Delete HLU water features so we don't get remnants later.
    print("   Deleting HLU water")
    arcpy.CopyFeatures_management(HLU, "HLU_noWater")
    arcpy.MakeFeatureLayer_management("HLU_noWater", "HLU_layer")
    arcpy.SelectLayerByAttribute_management("HLU_layer", where_clause="PHASE1HABI LIKE '%ater%'")
    arcpy.DeleteFeatures_management("HLU_layer")
    arcpy.Delete_management("HLU_layer")

    ###  Erasing buildings, roads and paths from HLU
    print("   Erasing buildings, roads and paths from HLU")
    arcpy.MakeFeatureLayer_management("OSMM_noLandform", "OSMM_layer2")
    # Alison: removed deletion of 'Roadside' as it was removing semi-natural grass verges. Manmade pavements will be removed anyway.
    arcpy.SelectLayerByAttribute_management("OSMM_layer2", where_clause="Make = 'Manmade' OR DescriptiveTerm = 'Track' OR Theme = 'Water'")
    arcpy.Erase_analysis("HLU_noWater", "OSMM_layer2", "HLU_Manerase")
    arcpy.Delete_management("OSMM_layer2")

    ##  Correcting HLU overlaps and sliver gaps because the original data contains many overlapping features.
    print("   Correcting HLU overlaps")

    # Arcpy crashes on the instruction below: it seems you cannot union a layer with itself and keep gaps?
    # Do this manually instead and then restart
    try:
        arcpy.Union_analysis([["HLU_Manerase",1]], "HLU_Manerase_union", "ALL", 0, "NO_GAPS")
    except:
        print("Please do a manual union of HLU_Manerase with itself, keeping gaps. This crashed in Arcpy")
        exit()

if elim_HLU_slivers:
    # Eliminate and then delete slivers (just deleting creates gaps).
    arcpy.MultipartToSinglepart_management("HLU_Manerase_union", "HLU_Manerase_union_sp")
    print("   Eliminating HLU slivers")
    arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp", "HLU_elim_layer")
    arcpy.SelectLayerByAttribute_management("HLU_elim_layer", where_clause="(Shape_Area <1)")
    arcpy.Eliminate_management("HLU_elim_layer", "HLU_Manerase_union_sp_elim")

    print("   Deleting remaining standalone slivers")
    arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim", "HLU_Manerase_union_sp_elim_del")
    arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp_elim_del", "HLU_del_layer")
    arcpy.SelectLayerByAttribute_management("HLU_del_layer", where_clause="Shape_Area < 1")
    arcpy.DeleteFeatures_management("HLU_del_layer")

    print("   Deleting larger gaps")
    arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_del", "HLU_Manerase_union_sp_elim_del2")
    arcpy.MakeFeatureLayer_management("HLU_Manerase_union_sp_elim_del2", "HLU_del_gap_layer")
    arcpy.SelectLayerByAttribute_management("HLU_del_gap_layer", where_clause="(FID_HLU_Manerase=-1)")
    arcpy.DeleteFeatures_management("HLU_del_gap_layer")

    print("   Deleting identical HLU polygons")
    arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_del2", "HLU_Manerase_union_sp_elim_delid")
    arcpy.DeleteIdentical_management("HLU_Manerase_union_sp_elim_delid", ["Shape"])

if check:
    arcpy.CopyFeatures_management("HLU_Manerase_union_sp_elim_delid", "HLU_preprocessed")
    MyFunctions.check_and_repair("HLU_preprocessed")

print(''.join(["## Completed on : ", time.ctime()]))

# Now use Merge_into_Base_map.py

exit()