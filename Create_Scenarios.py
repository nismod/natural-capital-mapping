# Creates a series of polygon outlines representing spatial scenarios, by clipping out a series of constraints
# Designed to create housing development zone scenarios
# Reads constraint layer names from a table
# Erases each constraint from the starting layer, converts to single part, removes areas less than threshold size,
# dissolves again, adds a label
# At the end, merges all constraint layers into a single scenario file, designed for input to Spatial Strategy Analysis.py
# Starting layer should already contain text field called Scenario for labels
# -----------------------------------------------------------------------------------------------------------------------

import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Define input parameters
# -----------------------
gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Scenario_analysis.gdb"
arcpy.env.workspace = gdb
start_layer = "Halo1km"
start_label = "Halo1km"
# Threshold size: polygons smaller than this will be deleted
threshold_size = 500
InfoTable = os.path.join(gdb, "OP2050ScenariosDes")
output = "ScenariosDes"

# Get a list of constraint layer names and short labels from InfoTable
constraint_names = []
constraints = arcpy.da.SearchCursor(InfoTable, "Name")
for constraint in constraints:
    constraint_names.append(str(constraint[0]))
constraint_labels = []
labels = arcpy.da.SearchCursor(InfoTable, "Label")
for label in labels:
    constraint_labels.append(str(label[0]))

# Successively erase constraints, beginning with start layer
i = 0
new_layer = ""
new_label = start_label + "_no"
merge_layers = []
for constraint_name in constraint_names:
    i = i + 1
    if i == 1:
        in_layer = start_layer
        out_layer = start_layer + "_no" + constraint_labels[i-1]
    else:
        in_layer = new_layer
        out_layer = in_layer[:-8] + constraint_labels[i-1]
    print("Erasing " + constraint_name + " from " + in_layer + " to make " + out_layer)
    arcpy.Erase_analysis(in_layer, constraint_name, out_layer)
    # Add new scenario label
    new_label = new_label + constraint_labels[i-1]
    print("Label is " + new_label)
    arcpy.CalculateField_management(out_layer, "Scenario", "'" + new_label + "'", "PYTHON_9.3")

    # Convert to single part
    arcpy.MultipartToSinglepart_management(out_layer, out_layer + "_sp")
    # Delete fragments smaller than viable threshold size
    arcpy.MakeFeatureLayer_management(out_layer + "_sp", "del_lyr", "Shape_Area < " + str(threshold_size))
    arcpy.DeleteFeatures_management ("del_lyr")
    arcpy.Delete_management("del_lyr")
    # Dissolve again
    arcpy.Dissolve_management(out_layer + "_sp", out_layer + "_sp_diss", "Scenario")
    new_layer = out_layer + "_sp_diss"
    merge_layers.append(new_layer)

print("Merging into single scenario file:" + "\n".join(merge_layers))
arcpy.CopyFeatures_management(start_layer, output)
arcpy.Append_management(merge_layers, output, "NO_TEST")

print("Finished on " + time.ctime())

exit()