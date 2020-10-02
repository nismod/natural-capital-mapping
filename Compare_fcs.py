# Compares two datasets
# Starts with two individual feature classes: designed to work for two versions of OxCam Arc natural capital map
# Option to split them into smaller feature classes (e.g. per LAD) if they are too large for Identity
# Then runs Identity for fcs from one gdb vs an equivalent fc from the other gdb
# Adds a Compare attribute for each field to be compared and sets to 1 for a match or 0 for no match.
# Adds an overall compare attribute
# Exports non-matching polygons to a new dataset
# Option to merge all the non-matching polygons into a single large dataset
# Exports summary statistics for area of each type of mis-match
# ---------------------------------------------------------------------------------------------------
#
import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True  # Overwrites files

# Main dataset, assume already split into manageable chunks e.g. LADs
main_gdb = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData_LADs.gdb"
# Dataset to be compared against the main one. Should contain only the comparison fields.
compare_fc = r"D:\cenv0389\OxCamArc\NatCap_Arc_FreeData.gdb\NatCap_Arc_FreeData_compare"
split_boundaries = os.path.join(main_gdb, "Arc_LADs")
# Wildcard template for input main feature classes
fc_template = "NatCap*"
# Suffix for split comparison features
in_compare_suffix = "_FreeData_compare"
# Suffix for new comparison feature classes
out_suffix = "_PaidVsFree"

# List of fields to compare: these should include all the fields that directly affect the ES scores (note: AONB currently omitted)
comp_fields = ["Interpreted_habitat", "ALC_GRADE", "NatureDesig", "CultureDesig", "EdDesig", "AccessMult"]
comp_fields_short = ["Hab", "ALC", "NatDes", "CultDes", "EdDes", "Access"]
# CAUTION: the suffix of the new field that will be created during the Identity operation depends on how many copies of the
# field are present. Check field aliases and case carefully. At present, there are two copies of ALC grade so that will have a suffix of _12.
comp_fields_new = ["Interpreted_habitat_1", "ALC_GRADE_12", "NatureDesig_1", "CultureDesig_1", "EdDesig_1", "AccessMult_1"]
comp_fields_replace_null_with = ["", "Non Agricultural", 0, 0, 0, 0, 0]
NumCompFields = len(comp_fields)

arcpy.env.workspace = main_gdb

# Which stages do we want to run?
split_compare_fc = False
replace_nulls = False
id_non_matching = False

if split_compare_fc:
    # Split large input comparison dataset into smaller units (LADs)
    LADs = arcpy.SearchCursor(split_boundaries)
    LAD_names = []
    for LAD in LADs:
        LAD_full_name = LAD.getValue("desc_")
        LAD_name = LAD_full_name.replace(" ", "")
        LAD_names.append(LAD_name)
        split_fc = os.path.join(main_gdb, LAD_name + in_compare_suffix)
        print ("Clipping " + compare_fc + " into " + split_fc)
        arcpy.MakeFeatureLayer_management(split_boundaries, "LAD_lyr")
        arcpy.SelectLayerByAttribute_management("LAD_lyr", where_clause="desc_ = '" + LAD_full_name + "'")
        arcpy.Clip_analysis(compare_fc, "LAD_lyr", split_fc)
        MyFunctions.check_and_repair(split_fc)
        print("Finished splitting " + LAD_name + " at " + time.ctime())

# Loop through all fcs in the main gdb that match the template

in_fcs = arcpy.ListFeatureClasses(fc_template)
for fc in in_fcs:
    LAD_name = fc[7:]
    print ("LAD name is " + LAD_name)
    if id_non_matching:
        print ("Running Identity on " + fc)
        arcpy.Identity_analysis(fc, LAD_name + in_compare_suffix, LAD_name + out_suffix, "NO_FID")

        if replace_nulls:
            # Get rid of NULLs which mess up the comparison
            print ("Getting rid of nulls")
            i = 0
            for comp_field in comp_fields:
                i = i + 1
                # print("Replacing NULLS in " + comp_field + " with " + str(comp_fields_replace_null_with[i-1]))
                # Test whether the field is a string: if so, add quote delimiters
                if isinstance(comp_fields_replace_null_with[i-1], str):
                    expression = "'" + comp_fields_replace_null_with[i-1] + "'"
                else:
                    expression = comp_fields_replace_null_with[i-1]
                MyFunctions.select_and_copy(LAD_name + out_suffix, comp_field, comp_field + " IS NULL", expression)
            i = 0
            for comp_field_new in comp_fields_new:
                i = i + 1
                # print("Replacing NULLS in " + comp_field_new + " with " + str(comp_fields_replace_null_with[i-1]))
                # Test whether the field is a string: if so, add quote delimiters
                if isinstance(comp_fields_replace_null_with[i-1], str):
                    expression = "'" + comp_fields_replace_null_with[i-1] + "'"
                else:
                    expression = comp_fields_replace_null_with[i-1]
                MyFunctions.select_and_copy(LAD_name + out_suffix, comp_field_new, comp_field_new + " IS NULL", expression)

        # Add and populate comparison fields
        i = 0
        comp_expression = ""
        print("Adding comparison fields")
        for comp_field_short in comp_fields_short:
            i = i + 1
            MyFunctions.check_and_add_field(LAD_name + out_suffix, comp_field_short + "_comp", "SHORT", "")
            # Populate with zeros initially so we don't get problems trying to ad up NULLS later
            arcpy.CalculateField_management(LAD_name + out_suffix, comp_field_short + "_comp", 0, "PYTHON_9.3")
            # Now set matching rows to 1
            expression = comp_fields[i - 1] + " = " + comp_fields_new[i - 1]
            MyFunctions.select_and_copy(LAD_name + out_suffix, comp_field_short + "_comp", expression, 1)
            # Add this field to the expression for the overall comparison to use later
            if i>1:
                comp_expression = comp_expression + " + "
            comp_expression = comp_expression + comp_field_short + "_comp"

        # Correction for sports and recreation grounds, as there is a known difference in the names because Katherine
        # used a shorter version to fit the shorter field she created in the LERC dataset
        expression = "Interpreted_habitat = 'Natural sports facility, recreation or playground' " \
                     "AND Interpreted_habitat_1 = 'Natural sports facility, recreation ground or playground'"
        MyFunctions.select_and_copy(LAD_name + out_suffix, "Hab_comp", expression, 1)

        # Add and populate overall comparison field
        comp_expression = comp_expression + " = " + str(NumCompFields)
        print ("Overall comparison expression is " + comp_expression)
        MyFunctions.check_and_add_field(LAD_name + out_suffix, "CompareAll", "SHORT", "")
        MyFunctions.select_and_copy(LAD_name + out_suffix, "CompareAll", comp_expression, 1)

        # Select and export non-matching polygons
        print("Exporting non-matching polygons")
        arcpy.MakeFeatureLayer_management(LAD_name + out_suffix, "Non_matching_lyr", where_clause="CompareAll IS NULL OR CompareAll = 0")
        arcpy.CopyFeatures_management("Non_matching_lyr", LAD_name + out_suffix + "_non_matching")
        print("Finished comparison for " + LAD_name + " at " + time.ctime())

    # Identify common reasons for non-matching polygons
    non_match_fc = LAD_name + out_suffix + "_non_matching"

    # Add simplified habitat fields
    print("Adding simplified habitat fields")
    MyFunctions.check_and_add_field(non_match_fc, "SimplePaid", "TEXT", 50)
    MyFunctions.check_and_add_field(non_match_fc, "SimpleFree", "TEXT", 50)
    arcpy.MakeFeatureLayer_management(non_match_fc, "lyr")
    arcpy.AddJoin_management("lyr", "Interpreted_habitat", "Matrix", "Habitat", "KEEP_ALL")
    arcpy.CalculateField_management("lyr","SimplePaid","!Matrix.SimpleHab!", "PYTHON_9.3")
    arcpy.RemoveJoin_management("lyr", "Matrix")
    arcpy.AddJoin_management("lyr", "Interpreted_habitat_1", "Matrix", "Habitat", "KEEP_ALL")
    arcpy.CalculateField_management("lyr","SimpleFree","!Matrix.SimpleHab!", "PYTHON_9.3")
    arcpy.RemoveJoin_management("lyr", "Matrix")
    arcpy.Delete_management("lyr")

    # Add reason fields and populate reasons
    print("Identifying reasons for non-matching polygons")
    MyFunctions.check_and_add_field(non_match_fc, "DetailedReason", "TEXT", 120)
    MyFunctions.check_and_add_field(non_match_fc, "SimpleReason", "TEXT", 100)
    # Mis-matched habitats
    expression = "Hab_comp = 0"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "!SimplePaid!" + "' vs '" + "!SimpleFree!")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "!Interpreted_habitat!" + "' vs '" + "!Interpreted_habitat_1!")
    # Mis-matched ALC grades
    expression = "Hab_comp = 1 AND ALC_comp = 0"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "'ALC mismatch'")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "'ALC mismatch'")
    # Temporary corrections...
    expression = "DetailedReason = 'ALC mis-match' AND ALC_GRADE = 'Not agricultural' AND ALC_GRADE_12 = 'Non Agricultural'"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "'False ALC mismatch'")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "'False ALC mismatch'")
    expression = "DetailedReason = 'ALC mis-match' AND ALC_GRADE = 'Non Agricultural' AND ALC_GRADE_12 = 'Not agricultural'"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "'False ALC mismatch'")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "'False ALC mismatch'")
    # Mis-matched Access
    expression = "DetailedReason IS NULL AND AccessMult <> AccessMult_1"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "'Access mismatch'")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "'Access mismatch'")
    # The rest must be due to mis-matched designations
    expression = "DetailedReason IS NULL"
    MyFunctions.select_and_copy(non_match_fc, "SimpleReason", expression, "'Designation mismatch'")
    MyFunctions.select_and_copy(non_match_fc, "DetailedReason", expression, "'Designation mismatch'")

    print(''.join(["## Finished on : ", time.ctime()]))

exit()