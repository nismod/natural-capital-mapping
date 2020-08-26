#   Fills in the fields in the union of individual designations files that was created
#   by Union_designations.py
# ------------------------------------------------------------------------------------
import time
import arcpy
import MyFunctions
print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# region = "Oxon"
region = "Arc"
# Which parts of the code do we want to run? useful for debugging or updates.
# Flag for bypassing the first part when restarting code after the manual inspection of gaps vs slivers
first_part = False
elim_slivers = True

if region == "Arc":
    Union_gdb = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Union_Designations.gdb"
    road_verge = False
elif region == "Oxon":
    Union_gdb = r"D:\cenv0389\Oxon_GIS\Designations\Union_Designations.gdb"
    road_verge = True

arcpy.env.workspace = Union_gdb
InfoTable = "DesignationFiles"

if first_part:

    # Make a copy of the original file to work on, and repair geometry
    arcpy.CopyFeatures_management("Desig_union", "Desig_union_repair")
    MyFunctions.check_and_repair("Desig_union_repair")

    # Multipart to single part - there are many edge slivers spread over a long length of edge in multiple parts
    print ("Converting to single part")
    arcpy.MultipartToSinglepart_management("Desig_union_repair", "Desig_union_repair_sp")

    # Delete identical shapes, which come either from overlaps in the union or from input dataset errors
    # Ideally you would inspect using Find Identical first, and make sure useful info is not being lost
    # i.e. none of the duplicates have differing attribute info
    # Inspection for Oxon has been carried out and only two polygons with different info were found
    # In both cases the polygon to keep is higher in the table so should be preserved

    arcpy.FindIdentical_management("Desig_union_repair_sp", "FindIdentical", ["Shape"], output_record_option="ONLY_DUPLICATES")
    print("Deleting identical features. These are recorded in FindIdentical table - please check that the deletions are OK.")
    arcpy.CopyFeatures_management("Desig_union_repair_sp", "Desig_union_repair_sp_delid")
    arcpy.DeleteIdentical_management("Desig_union_repair_sp_delid", ["Shape"])

    # Find gaps. Loop through all the input types and build an expression to find those with all FID = -1
    print("Finding gaps")
    cursor = arcpy.SearchCursor(InfoTable)
    i=0
    for row in cursor:
        i=i+1
        ShortName = row.getValue("ShortName")
        # Create expression for selecting rows with all FIDs = -1 as Gaps
        # FIDs are named FID_shortname_input
        if i==1:
            expression = "FID_" + ShortName + "_input_diss_union = -1"
        else:
            expression = expression + " AND FID_" + ShortName + "_input_diss = -1"

    # Select rows with all FIDs = -1 and set type to "Gap"
    arcpy.MakeFeatureLayer_management("Desig_union_repair_sp_delid", "Desig_layer")
    arcpy.SelectLayerByAttribute_management("Desig_layer", where_clause = expression)
    arcpy.CalculateField_management("Desig_layer", "Type", '"Gap"', "PYTHON_9.3")
    arcpy.Delete_management("Desig_layer")

    # Eliminate sliver gaps under 500m2. Tell the user they have the option to improve this step by manual inspection of the larger gaps
    print("Option: you may inspect the Desig_union_repair_sp_delid file. Select Type='sliver'. Inspect all these and delete any that"
          " are real gaps, not slivers. Set 'first_part' to 'False' and restart the code. This will improve the final shapes.")
    expression = "Type = 'Gap' AND Shape_Area > 500 AND Shape_area < 2500"
    MyFunctions.select_and_copy("Desig_union_repair_sp_delid", "Type", expression, "'sliver'")

    exit()

if elim_slivers:
    print("Eliminating sliver gaps")
    arcpy.MakeFeatureLayer_management("Desig_union_repair_sp_delid", "Elim_layer")
    expression = "(Type = 'Gap' AND Shape_Area < 500) OR Type = 'sliver'"
    arcpy.SelectLayerByAttribute_management("Elim_layer", where_clause = expression)
    arcpy.Eliminate_management("Elim_layer","Desig_union_repair_sp_delid_elim")
    arcpy.Delete_management("Elim_layer")

    # Delete remaining (larger) gaps
    print("Deleting large gaps")
    arcpy.CopyFeatures_management("Desig_union_repair_sp_delid_elim","Desig_union_repair_sp_delid_elim_del")
    arcpy.MakeFeatureLayer_management("Desig_union_repair_sp_delid_elim_del", "Del_layer")
    arcpy.SelectLayerByAttribute_management("Del_layer", where_clause = "Type = 'Gap' AND Shape_Area >= 500")
    arcpy.DeleteFeatures_management("Del_layer")
    arcpy.Delete_management("Del_layer")

    # Eliminate non-gap slivers
    print("Eliminating non-gap slivers")
    if road_verge:
        # Eliminate in two stages: do small features (Road verge NR) separately
        arcpy.MakeFeatureLayer_management("Desig_union_repair_sp_delid_elim_del", "Elim_layer2")
        arcpy.SelectLayerByAttribute_management("Elim_layer2", where_clause = "(Shape_Area < 500 AND FID_RVNR_input_diss = -1)")
        arcpy.Eliminate_management("Elim_layer2", "Desig_elim2")
        arcpy.MakeFeatureLayer_management("Desig_elim2", "Elim_layer3")
        arcpy.SelectLayerByAttribute_management("Elim_layer3", where_clause = "(Shape_Area < 50 AND FID_RVNR_input_diss >= 0)")
        arcpy.Eliminate_management("Elim_layer2", "Desig_clean")
    else:
        arcpy.MakeFeatureLayer_management("Desig_union_repair_sp_delid_elim_del", "Elim_layer2")
        arcpy.SelectLayerByAttribute_management("Elim_layer2", where_clause = "Shape_Area < 500")
        arcpy.Eliminate_management("Elim_layer2","Desig_clean")
    arcpy.Delete_management("Elim_layer")

    # Repair geometry again
    arcpy.CopyFeatures_management("Desig_clean", "Designations")
    MyFunctions.check_and_repair("Designations")

# Set fields to appropriate values
# Loop through all the designation types, starting with the lowest priority
print("Filling in the table")
arcpy.Sort_management("DesignationFiles", "DesignationFiles_Sort", [["TableOrder", "ASCENDING"]])
InfoTable="DesignationFiles_Sort"

i=0
cursor = arcpy.SearchCursor(InfoTable)
for row in cursor:
    i=i+1
    ShortName = row.getValue("ShortName")
    DesType = row.getValue("Type")
    FlagName = row.getValue("NewName")
    HabField = row.getValue("HabField")
    DescField = row.getValue("DescField")
    print("Short name is " + ShortName + ", Designation type is " + DesType + ", Flag name is " + FlagName)
    if ShortName == "GB":
        FID_name = "FID_" + ShortName + "_input_diss_union"
    else:
        FID_name = "FID_" + ShortName + "_input_diss"
    print("FID_name is " + FID_name)

    # Set all values in the designation flag field to 0, because NULL prevents adding up later
    arcpy.CalculateField_management("Designations", FlagName, 0, "PYTHON_9.3")

    # Build the expression we will use later to calculate number of designations
    if i == 1:
        expression = "!" + FlagName + "!"
    else:
        expression = expression + " + !" + FlagName + "!"

    # Select polygons covered by each designation type
    arcpy.MakeFeatureLayer_management("Designations", "Sel_layer")
    sel_exp = FID_name + ">=0"
    arcpy.SelectLayerByAttribute_management("Sel_layer", where_clause= sel_exp)

    # Fill in the appropriate designation column with '1' and copy type, name, habitat and description
    # from the appropriate columns
    type_exp = "'" + DesType + "'"
    arcpy.CalculateField_management("Sel_layer", "Type", type_exp, "PYTHON_9.3")
    arcpy.CalculateField_management("Sel_layer", FlagName, 1, "PYTHON_9.3")
    arcpy.CalculateField_management("Sel_layer", "Name", "!" + ShortName + "_name!","PYTHON_9.3")
    if HabField:
        arcpy.CalculateField_management("Sel_layer", "Habitat", "!" + ShortName + "_hab!", "PYTHON_9.3")
    if DescField:
        arcpy.CalculateField_management("Sel_layer", "Description", "!" + ShortName + "_desc!", "PYTHON_9.3")

# Add up the number of designations applying to each polygon
print("Adding up number of designations")
print (expression)
arcpy.CalculateField_management("Designations", "NumDesig", expression, "PYTHON_9.3")
print("Completed. Now export output file 'Designations' to new gdb (MergeDesignations.gdb) for Oxon or to Designations_Tidy for Arc"
      "(hide all the FID fields first as these are not needed) and run Merge_into_Base_Map.py")
exit()
