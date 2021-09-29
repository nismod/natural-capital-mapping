# Copies a feature class from a series of gdbs in one folder to a single gdb
# ---------------------------------------------------------------------------
#
import time, arcpy, os

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True  # Overwrites files

# name of folder where the individual gdbs are stored
# folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
folder = r"M:\urban_development_natural_capital\LADs"
arcpy.env.workspace = folder

# name of gdb to copy the individual feature classes into
# out_gdb = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"
out_gdb = r"M:\urban_development_natural_capital\NatCap_NP.gdb"

# Wildcard template for feature class to copy over
fc_template = "NatCap*"

# Loop through all gdbs in the input folder
# in_gdbs = arcpy.ListFiles("*.gdb")
# done
# "Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
#            "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
#            "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb",
#            "Craven.gdb", "Darlington.gdb", "Doncaster.gdb",  "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
#            "Halton.gdb", "Hambleton.gdb",
#  "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
#            "Lancaster.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
#             "North Lincolnshire.gdb",   "North Tyneside.gdb", "Northumberland.gdb", "Oldham.gdb",
# Erros - repeat some stages "East Riding of Yorkshire.gdb", "Leeds.gdb", "Harrogate.gdb", "North East Lincolnshire.gdb",
in_gdbs = ["Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
           "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
           "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
           "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
           "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wirral.gdb",
           "Wyre.gdb", "York.gdb"]
for gdb in in_gdbs:
    gdb_name = gdb.replace(" ", "")
    print ("Copying from " + gdb_name)
    arcpy.env.workspace = os.path.join(folder,gdb_name)
    in_fc = []
    in_fc = arcpy.ListFeatureClasses(fc_template)
    out_fc = os.path.join(out_gdb, in_fc[0])
    print ("Copying " + in_fc[0] + " to " + out_fc)
    arcpy.CopyFeatures_management(in_fc[0], out_fc)

    print(''.join(["## Finished on : ", time.ctime()]))

exit()