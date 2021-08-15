# Creates a set of new attributes to hold the differences in scores between two versions of a natural capital dataset
# that have been intersected.
# The input file is the output of Compare_fcs.py after merging to create a single PaidVsFree_non_matching file
#-------------------------------------------------------------------------------------------------------------------------

import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

in_data = r"D:\cenv0389\OxCamArc\Comparison.gdb\Paid_vs_Free_Non_matching"

services = ["Food_ALC_norm", "Wood", "Fish", "WaterProv", "Flood", "Erosion", "WaterQual", "Carbon", "AirQuality", "Cooling",
            "Noise", "Pollination", "PestControl", "Rec_access", "Aesthetic_norm", "Education_desig", "Nature_desig", "Sense_desig"]

for service in services:
    print("Adding field to contain differences for " + service)
    MyFunctions.check_and_add_field(in_data, service + "_diff", "Float", "")
    print("Calculating differences for " + service)
    arcpy.CalculateField_management(in_data, service + "_diff", "!" + service + "! - !" + service + "_1!", "PYTHON_9.3" )

exit()
