# Deletes surplus feature classes from a geodatabase based on a list of classes to keep and/or a template
# CAUTION - be very careful - best to test by commenting out actual delete stage first!
# -------------------------------------------------------------------------------------------------------
import time
import arcpy
import os

arcpy.CheckOutExtension("Spatial")

# Set up parameters
# Geodatabase(s) to tidy up
# gdbs = [r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"]
# gdbs = [r"D:\cenv0389\Oxon_GIS\OxCamArc\NaturalCapital\NatCapArc_raster.gdb"]
folder = r"M:\urban_development_natural_capital\LADs"
arcpy.env.workspace = folder
# gdbs =  arcpy.ListWorkspaces("*", "FileGDB")
LADs = ["Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
        "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
        "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb",
        "Craven.gdb", "Darlington.gdb", "Doncaster.gdb",
        "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
        "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
        "Lancaster.gdb", "Leeds.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
        "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
        "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
        "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
        "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
        "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
        "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb",
        "Wigan.gdb", "Wirral.gdb", "Wyre.gdb", "York.gdb"]
gdbs = []
for LAD in LADs:
    gdbs.append(os.path.join(folder, LAD.replace(" ", "")))

# Feature classes to keep - the others will be deleted if they match the delete template and do not match the keep template
# keep_fcs = ["Paid_vs_Free_Non_matching"]
# keep_templates = ["Arc", "NatCap", "Water"]
keep_fcs = ["boundary", "OSMM", "PHI", "Designations", "OSGS", "OS_Open_GS", "OSMM_CROME", "OSMM_CROME_PHI",  "OSMM_CR_PHI_ALC",
            "OSMM_CR_PHI_ALC_Desig", "OSMM_CR_PHI_ALC_Desig_GS", "OSMM_CR_PHI_ALC_Desig_GS_PA", "New_snap_clean", "Public_access", "Base_TI"]
keep_templates = ["NatCap"]
# Delete rasters or feature classes?
# type = "raster"
type = "fcs"

# Feature classes to delete
delete_templates = [""]
# delete_templates = ["Halo1km_", "NatCap_Halo_", "Ox_Urban_1k_halo_no", "OP2050", "MRCF"]

# Flag to either test this function first or do the actual deletions.
# Do not set to Delete until you have checked the list of items to delete
# safety_flag = "Check"
safety_flag = "Delete"

print("## Started on : " + time.ctime())

for gdb in gdbs:
    if safety_flag == "Check":
        print("Checking which surplus feature classes to delete from " + gdb + " on " + time.ctime())
    else:
        print("Started deleting surplus feature classes from " + gdb + " on " + time.ctime())
    arcpy.env.workspace = gdb
    delete_fcs = []
    if type == "fcs":
        fcs = arcpy.ListFeatureClasses("*")
    elif type == "raster":
        fcs = arcpy.ListRasters("*")
    for fc in fcs:
        print ("Checking " + fc)
        keep = "Unknown"
        # Check to see if it should be kept. Careful with this loop - have to keep the stages separate like this!
        if fc in keep_fcs:
            print(fc + " is in keep list and will be kept")
            keep = "True"
        else:
            # print(fc + " is not in keep list")
            # Check to see if it matches a keep template
            for keep_template in keep_templates:
                print "Checking against keep template " + keep_template
                if keep == "Unknown":
                    if keep_template in fc:
                        print (fc + " matches keep template " + keep_template + " and will be kept")
                        keep = "Keep"
                    # else:
                        # print(fc + " does not match keep template " + keep_template)

            if keep == "Unknown":
                # Check to see if it matches a delete template
                for delete_template in delete_templates:
                    # print ("Checking delete template " + delete_template)
                    if keep == "Unknown":
                        # print ("Checking delete template " + delete_template)
                        if delete_template in fc:
                            keep = "Delete"
                            delete_fcs.append(fc)
                            print(fc + " matches delete template " + delete_template + " and will be deleted from " + gdb)
                        # else:
                            # print(fc + " does not match delete template " + delete_template)
        if keep == "Unknown":
            print(fc + " is not flagged for keeping or deleting and will be kept")

    if len(delete_fcs) > 0:
        print("*** Deleting surplus feature classes: " + '\n '.join(delete_fcs))
        if safety_flag == "Delete":
            for delete_fc in delete_fcs:
                print("Deleting " + delete_fc + " from " + gdb)
                arcpy.Delete_management(delete_fc)
        else:
            print("Check completed. If you are happy with the list of classes to delete, change the safety flag to Delete.")

    print(''.join(["Completed " + gdb + " on : ", time.ctime()]))
exit()