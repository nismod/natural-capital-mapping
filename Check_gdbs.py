# Loops through a set of gdbs and checks for errors
# The errors are specific to the process of creating natural capital maps but this code could be modified to check for other errors
#

import time
import arcpy
import os

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

# Choose region
# region = "Arc"
# region = "Oxon"
region = "NP"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "LERC"
# method = "HLU"

# Geodatabases to check
if region == "Oxon" and method == "HLU":
    work_folder = r"D:\env0389\Oxon_GIS\Oxon_county\NaturalCapital"
    gdbs = [r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb"]
    Base_map_name = "OSMM_HLU_CR_ALC_Des"
    boundary = "Oxfordshire"
    Hab_field = "Interpreted_habitat"
elif region == "NP":
    work_folder = r"M:\urban_development_natural_capital"
    gdb_names = ["Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
                 "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb",  "Carlisle.gdb", "Cheshire East.gdb",
                 "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb", "Craven.gdb", "Darlington.gdb",
                 "Doncaster.gdb", "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb", "Halton.gdb",
                 "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
                 "Lancaster.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
                 "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
                 "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
                 "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
                 "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
                 "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb", "Tameside.gdb",
                 "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb",  "West Lancashire.gdb",
                 "Wigan.gdb", "Wirral.gdb", "Wyre.gdb", "York.gdb"]
    gdbs = []
    for gdb_name in gdb_names:
        gdbs.append(os.path.join(r"M:\urban_development_natural_capital\LADs",  gdb_name.replace(" ", "")))
    Base_map_name = "OSMM_CR_PHI_ALC_Desig"
    boundary = "boundary"
    Hab_field = "Interpreted_habitat"
    TOID_field = "fid"
    Base_Index_field = "OBJECTID"
    DescGroup = "descriptivegroup"

Tables_to_check = ["Base_TI", "Base_TI_split", "Base_TI_not_split", "Base_TI_not_split_sort", "CROME_TI", "CROME_TI_sort",
                   "Designations", "GS_TI", "OSGS", "OS_Open_GS"]
failed_gdbs=[]
error_msgs = []
for gdb in gdbs:
    arcpy.env.workspace = gdb
    print "Checking " + gdb
    gdb_failed = False
    for table in Tables_to_check:
        numrows = arcpy.GetCount_management(table)
        print str(numrows) + " rows in " + table
        if numrows == 0:
            # this doesn't seem to work
            gdb_failed = True
            error_msgs.append(gdb + " has zero rows in " + table)
    if gdb_failed:
        failed_gdbs.append(gdb)

print "\n".join(error_msgs)

if len(failed_gdbs) > 0:
    print "Summary list of failed gdbs: "
    print "\n".join(failed_gdbs)
else:
    print "No gdbs failed the error check"
exit()