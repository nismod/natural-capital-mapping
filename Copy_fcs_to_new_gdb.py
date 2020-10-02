# Copies a feature class from a series of gdbs in one folder to a single gdb
# ---------------------------------------------------------------------------
#
import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True  # Overwrites files

# name of folder where the individual gdbs are stored
folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
arcpy.env.workspace = folder

# name of gdb to copy the individual feature classes into
out_gdb = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"

# Wildcard template for feature class to copy over
fc_template = "NatCap*"

# Loop through all gdbs in the input folder
in_gdbs = arcpy.ListFiles("*.gdb")
for gdb in in_gdbs:
    print ("Copying from " + gdb)
    arcpy.env.workspace = os.path.join(folder,gdb)
    in_fc = []
    in_fc = arcpy.ListFeatureClasses(fc_template)
    out_fc = os.path.join(out_gdb, in_fc[0])
    print ("Copying " + in_fc[0] + " to " + out_fc)
    arcpy.CopyFeatures_management(in_fc[0], out_fc)

    print(''.join(["## Finished on : ", time.ctime()]))

exit()