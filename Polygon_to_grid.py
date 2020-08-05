# Populate a polygon grid of cells with the average area-weighted values from an attribute in a polygon dataset
# Input grid polygons must have a unique ID field of consecutive integers - not OBJECTID or FID
# as that will change when the intermediate selections are made.
# For large datasets, put all inputs in the same geodatabase and delete unnecessary fields.
# The new score field will be added to the input grid. If you want to keep the original unchanged, copy to a
# new input file.
# -------------------------------------------------------------------------------------------------------------

import time
import arcpy
import MyFunctions
# import os - not currently needed

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

region = "Oxon"

if region == "Arc":
    arcpy.env.workspace = r"D:\cenv0389\Oxon_GIS\OxCamArc\NaturalCapital\Arc_high_nat_cap.gdb"
    input_grid = "Dwellings_100m"
    input_poly = "NatCap_Arc_maxregcultfood"
    # Name of index field
    ID_name = "CELL_ID"
    # Start value of index field
    ID_start = 0
elif region == "Oxon":
    arcpy.env.workspace = r"D:\cenv0389\Oxon_GIS\Oxon_county\Dwellings.gdb"
    input_grid = "Dwellings_100m_Oxon_MaxRegCultFood_area_weighted"
    input_poly = "NatCap_Oxon_MaxRegCultFood"
    # Name of index field
    ID_name = "CELL_ID"
    # Start value of index field
    ID_start = 1

in_field = "MaxRegCultFood"
# Field name max 10
out_field = "MaxScore"
# Number of cells to process in each iteration
ichunk = 10000

# If the grid is very large, break into chunks
numrows = arcpy.GetCount_management(input_grid)
iter = int(numrows[0])/ichunk + 1
print ("There are " + str(numrows) + " grid cells which will be divided into " + str(iter) + " iterations")

# Add field to contain area-weighted values
MyFunctions.check_and_add_field(input_grid, out_field, "FLOAT", 0)
for i in range(0, iter):

    # Select a chunk of grid cells
    start_row = ID_start + (i * ichunk)
    end_row = start_row + ichunk
    expression = ID_name + " >= " + str(start_row) + " and " + ID_name + " < " + str(end_row)
    arcpy.MakeFeatureLayer_management(input_grid, "grid_lyr", where_clause=expression)
    arcpy.CopyFeatures_management("grid_lyr", "grid_chunk")
    arcpy.Delete_management("grid_lyr")
    print ("Processing chunk " + str(i) + " of " + str( iter) + ": grid cells " + str(start_row) + " to " + str(end_row-1))

    # Intersect the grid chunk and the polygon data
    arcpy.MakeFeatureLayer_management(input_poly, "poly_lyr")
    arcpy.SelectLayerByLocation_management("poly_lyr", "INTERSECT", "grid_chunk")
    arcpy.Intersect_analysis(["grid_chunk", "poly_lyr"], "poly_chunk")

    # Calculate area-weighted score in each polygon
    print("Calculating area-weighted scores per polygon")
    MyFunctions.check_and_add_field("poly_chunk", "Area_value", "FLOAT", 0)
    arcpy.CalculateField_management("poly_chunk", "Area_value", "!" + in_field + "! * !Shape_Area!", "PYTHON_9.3")

    # Aggregate area-weighted scores for each grid cell and store in table
    print("Aggregating scores")
    arcpy.Statistics_analysis("poly_chunk", "Stats", [["Area_value", "SUM"]], ID_name)
    # Copy scores from statistics table to original grid dataset
    arcpy.MakeFeatureLayer_management(input_grid, "join_lyr")
    arcpy.AddJoin_management("join_lyr", ID_name, "Stats", ID_name)
    expression = input_grid + "." + ID_name + " >= " + str(start_row) + " and " + input_grid + "." + ID_name + " < " + str(end_row)
    arcpy.SelectLayerByAttribute_management("join_lyr", where_clause=expression)
    expression = "!Stats" + ".SUM_Area_value! / !" + input_grid + ".Shape_Area!"
    arcpy.CalculateField_management("join_lyr", input_grid + "." + out_field, expression, "PYTHON_9.3")
    arcpy.RemoveJoin_management("join_lyr", "Stats")
    arcpy.Delete_management("join_lyr")

    print(''.join(["Finished iteration " + str(i) + " on : ", time.ctime()]))

exit()