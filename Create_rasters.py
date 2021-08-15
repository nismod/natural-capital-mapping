# Convert a vector file to a set of rasters based on a series of different attributes read from an input table
# -----------------------------------------------------------------------------------------------------------------------

import time, arcpy, os

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Define input parameters
# -----------------------
gdb = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData.gdb"
arcpy.env.workspace = gdb
in_fc = "NatCap_Arc_PaidData"
InfoTable = os.path.join(gdb, "ES_maps")
out_gdb = r"D:\cenv0389\OxCamArc\NatCapArc_raster.gdb"
# Resolution (m)
resolution = 25
# Method
raster_method = "MAXIMUM_COMBINED_AREA"
output_label = "Arc_PaidData_"
output_suffix = "_25m_MCA"

# Raster to use as template
arcpy.env.snapRaster = os.path.join(out_gdb, "Arc_PaidData_MaxRegCult_25m_MCA")

# Get a list of attribute names and labels from InfoTable
attribute_names = []
attributes = arcpy.da.SearchCursor(InfoTable, "Field")
for attribute in attributes:
    attribute_names.append(str(attribute[0]))
label_names = []
labels = arcpy.da.SearchCursor(InfoTable, "Label")
for label in labels:
    label_names.append(str(label[0]))

# Create rasters
i = 0
for attribute_name in attribute_names:
    i = i + 1
    if (attribute_name not in ["Wood", "Fish", "WaterProv", "Carbon", "Pollination", "PestControl"]):
        out_raster = os.path.join(out_gdb, output_label + label_names[i-1] + output_suffix)
        print("Creating raster for " + attribute_name + " from " + in_fc + " to make " + out_raster)
        print("  Started on " + time.ctime())
        arcpy.PolygonToRaster_conversion(in_fc, attribute_name, out_raster, raster_method, "", resolution)
        print("  Finished on " + time.ctime())

exit()