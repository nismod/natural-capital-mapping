#
# Merges a set of datasets, optionally adding a 'type' field first
# Special case for merging the final natural capital files from each LAD gdb for the Arc, in order of county (so that it displays smoothly)
#-------------------------------------------------------------------------------------------------------------------------

import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# merge_type = "UDM_scenarios"
merge_type = "Arc_LADs"
# merge_type = "Arc_non_matching"

if merge_type == "Arc_LADs":
    folder = r"D:\cenv0389\OxCamArc"
    arcpy.env.workspace = folder
    # Input file of LADs sorted by display order
    info_table = os.path.join(folder, "Arc_LADs_sort.shp")
    counties_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire", "Oxfordshire", "Peterborough"]
    type_field = "LAD"
    in_gdb_folder = os.path.join(folder,"NatCap_Arc_FreeData")
    out_gdb = os.path.join(folder, "NatCap_Arc_FreeData.gdb")
    type_len = 30
    out_fc = "NatCap_Arc_FreeData"
elif merge_type == "Arc_non_matching":
    # Different case as all feature classes to merge are in a single gdb, which is also the output gdb
    in_gdb = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"
    out_gdb = in_gdb
    type_field = "LAD"
    type_len = 30
    template = "*_non_matching"
    out_fc = "Paid_vs_Free_Non_matching"
    arcpy.env.workspace = in_gdb
elif merge_type == "UDM_scenarios":
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    type_field = "Scenario"
    template = "New*"
    in_gdb = os.path.join(folder, "NaturalCapital\NaturalCapital.gdb")
    arcpy.env.workspace = in_gdb
    out_gdb = in_gdb
    type_len = 30
    out_fc = "UDM_scenarios"

# Do we want to add a field to distinguish the different datasets to be merged?
# Note: For the non-matching datasets, type field isalready included so set add_type_field to false.
add_type_field = True
delete_surplus_fields = False

in_fcs = []

print ("Collating input feature class names")

if merge_type == "Arc_LADs":
    fcs = arcpy.SearchCursor(info_table)
elif merge_type == "UDM_scenarios" or merge_type == "Arc_non_matching":
    fcs = arcpy.ListFeatureClasses(template)

for fc in fcs:
    if merge_type == "Arc_LADs":
        LAD_full_name = fc.getValue("desc_")
        print ("Processing " + LAD_full_name)
        county = fc.getValue("county")
        if county in counties_included:
            LAD_name = LAD_full_name.replace(" ", "")
            in_gdb = os.path.join(folder, in_gdb_folder, LAD_name + ".gdb")
            fc_name = "NatCap_" + LAD_name
            type_name = LAD_full_name
        else:
            fc_name = ""
    elif merge_type == "Arc_non_matching":
        fc_name = fc
        # type name set up by not actually needed as a better version (including spaces in LAD names) is there already
        type_name = fc.split("_")[0]
    elif merge_type == "UDM_scenarios":
        fc_name = fc
        type_name = fc_name

    if fc_name <> "":
        print ("Including " + fc_name)
        in_fc = os.path.join(in_gdb, fc_name)
        if delete_surplus_fields:
            # *** Delete some surplus fields created by the last processing step - check field names
            print("Deleting surplus OBJECTID fields")
            # *** SPECIAL TEMPORARY CASE FOR EA LERC DATA: need to delete OBJECTID but not OBJECTID_1!
            # arcpy.DeleteField_management(in_fc, "OBJECTID")
            # arcpy.DeleteField_management(in_fc, "F22")
            # arcpy.DeleteField_management(in_fc, "F23")
            # arcpy.DeleteField_management(in_fc, "F24")
            # arcpy.DeleteField_management(in_fc, "F25")
            # # arcpy.DeleteField_management(in_fc, "OBJECTID_1")
            # arcpy.DeleteField_management(in_fc, "OBJECTID_12")
            # arcpy.DeleteField_management(in_fc, "OBJECTID_12_13")
            # arcpy.DeleteField_management(in_fc, "OBJECTID_12_13_14")
        if add_type_field:
            print ("  Adding " + type_field + " field")
            MyFunctions.check_and_add_field(in_fc, type_field, "TEXT", type_len)
            arcpy.CalculateField_management(in_fc, type_field, "'" + type_name + "'", "PYTHON_9.3")
        in_fcs.append(in_fc)

print ("Merging " + ', '.join(in_fcs) + " into a single file")
arcpy.Merge_management(in_fcs, os.path.join(out_gdb, out_fc))

print("## Completed merge on " +  time.ctime())

exit()
