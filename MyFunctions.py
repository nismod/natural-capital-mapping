# Function definitions
# --------------------
# Code by Alison Smith (Environmental Change Institute, University of Oxford)
# These functions are research tools and have not been rigorously tested for wider use.
# -------------------------------------------------------------------------------------
import arcpy
import time

arcpy.env.overwriteOutput = True         # Overwrites files

def check_and_repair(in_file):
    # Check and repair geometry
    print("      Checking and repairing " + in_file)
    out_table = "CheckGeom"
    arcpy.CheckGeometry_management(in_file, out_table)
    num_errors = arcpy.GetCount_management(out_table)[0]
    print("      {} geometry problems found, see {} for details.".format(num_errors, out_table))
    if num_errors > 0:
        arcpy.RepairGeometry_management(in_file)
    return

def delete_fields(in_file, needed_fields, out_file):
    # Delete all fields except those in the 'Needed' list and required fields (Shape length and area, and object ID)
    if out_file == "":
        out_file = in_file
    else:
        arcpy.CopyFeatures_management(in_file, out_file)
    Fields = arcpy.ListFields(out_file)
    fieldNameList = []
    for field in Fields:
        # print("Field " + field.name + " in list: " + (str(field.name in needed_fields)))
        if field.name not in needed_fields and not field.required:
            fieldNameList.append(field.name)
    if len(fieldNameList)>0:
        print ("      Deleting from " + out_file + ": " + ", ".join(fieldNameList))
        arcpy.DeleteField_management(out_file, fieldNameList)
    else:
        print ("      No fields need to be deleted from " + out_file)
    return

def tidy_fields(in_file):
    # Delete un-needed FID and OBJID fields and duplicate fields ending in _1
    Fields = arcpy.ListFields(in_file)
    fieldNameList = []
    for field in Fields:
        if ("FID" in field.name or "OBJID" in field.name or "BaseID" in field.name or "_1" in field.name or "_Relationship" in field.name
            or "_Area" in field.name or field.name == "Shape_Leng") and not field.required:
            fieldNameList.append(field.name)
    print ("      Deleting unnecessary fields in " + in_file + ": " + ', '.join(fieldNameList))
    print("      Started on " + time.ctime() + ". May take several hours for large files. It is much quicker to select needed fields"
                                               " in ArcMap and then export.")
    if len(fieldNameList)>0:
        print ("      Deleting from " + in_file + ": " + ", ".join(fieldNameList))
        arcpy.DeleteField_management(in_file, fieldNameList)
    else:
        print ("      No fields need to be deleted from " + in_file)
    print ("      Finished deleting unnecessary fields in " + in_file + " on " + time.ctime())
    return

def check_and_add_field(in_table, in_field, type, len):
    # Check whether field already exists
    for ifield in arcpy.ListFields(in_table):
        if ifield.name == in_field:
            print ("*** WARNING: " + in_field + " field already exists in " + in_table)
            if ifield.type == "String" and type == "TEXT":
                if ifield.length <> len:
                    print("*** WARNING: the existing text field has a different length to the new field specification.")
                    # arcpy.DeleteField_management(in_table, in_field)
                else:
                    print ("    Duplicate field will be overwritten")
                    return
        elif ifield.name.lower() == in_field.lower():
            print ("*** WARNING: there is a field " + ifield.name + " with different case to " + in_field +
                   ": contents will be transferred via a temporary field, old field will be deleted and new field may be overwritten")
            arcpy.AddField_management(in_table, in_field + "_temp", type, field_length=len)
            arcpy.CalculateField_management(in_table, in_field + "_temp", "!" + ifield.name + "!", "PYTHON_9.3")
            arcpy.DeleteField_management(in_table, in_field)
            arcpy.AddField_management(in_table, in_field, type, field_length=len)
            arcpy.CalculateField_management(in_table, in_field, "!" + in_field + "_temp!", "PYTHON_9.3")
            arcpy.DeleteField_management(in_table, in_field + "_temp")
            return
    # No field with that name exists: create new field
    if type == "TEXT" and len>0:
        arcpy.AddField_management(in_table, in_field, type, field_length=len)
    else:
        arcpy.AddField_management(in_table, in_field, type)
    return

def delete_by_size (in_table, size):
    print("      Deleting slivers under " + str(size) + " from " + in_table)
    arcpy.MakeFeatureLayer_management(in_table, "del_lyr")
    arcpy.SelectLayerByAttribute_management("del_lyr", where_clause="Shape_Area < " + str(size))
    arcpy.DeleteFeatures_management("del_lyr")
    arcpy.Delete_management("del_lyr")
    return

def select_and_copy (in_table, in_field, expression, copy_string):
    arcpy.MakeFeatureLayer_management(in_table, "copy_lyr")
    arcpy.SelectLayerByAttribute_management("copy_lyr", where_clause=expression)
    arcpy.CalculateField_management("copy_lyr", in_field, copy_string, "PYTHON_9.3")
    arcpy.Delete_management("copy_lyr")
    return