# Deletes surplus feature classes from a geodatabase based on a list of classes to keep and/or a template
# CAUTION - be very careful - best to test by commenting out actual delete stage first!
# -------------------------------------------------------------------------------------------------------
import time
import arcpy

arcpy.CheckOutExtension("Spatial")

# Set up parameters
# Geodatabase(s) to tidy up
gdbs = [r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"]

# Feature classes to keep - the others will be deleted if they match the delete template and do not match the keep template
keep_fcs = ["Paid_vs_Free_Non_matching"]
keep_templates = ["Arc", "NatCap", "Water"]

# Feature classes to delete
delete_templates = ["_compare", "_PaidVsFree"]

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
    fcs = arcpy.ListFeatureClasses("*")
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
                if keep == "Unknown":
                    if keep_template in fc:
                        print (fc + " matches keep template " + keep_template + " and will be kept")
                        keep = "Keep"
                    else:
                        # print(fc + " does not match keep template " + keep_template)
                        # Check to see if it matches a delete template
                        for delete_template in delete_templates:
                            if keep == "Unknown":
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