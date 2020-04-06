# Starts from base map (derived from OS Mastermap and other layers) and adds in
# Rural Payments Agency CROME Crop map data (input must be dissolved by land use code and joined to description
# and simplified description.
# Adds crop type from CROME map only for agricultural land. This is probably better data then LCM and is freely available.
# Arable crops and improved grassland categories are added - the rest are ignored.
# Short-rotation coppice could be added but the two 'SRC' polygons in Oxfordshire look dubious, so this is also ignored.
# -----------------------------------------------------------------------------------------------------------------

import time
import arcpy
import os
import MyFunctions

arcpy.CheckOutExtension("Spatial")

print(''.join(["## Started on : ", time.ctime()]))

arcpy.env.overwriteOutput = True         # Overwrites files
arcpy.env.qualifiedFieldNames = False    # Joined fields will be exported without the join table name
arcpy.env.XYTolerance = "0.001 Meters"

region = "Oxon"
# region = "Arc"

method = "HLU"
# method = "LCM_PHI"

if region == "Oxon" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data"
    CROME_data = os.path.join(folder, "Merge_OSMM_HLU_ALC.gdb\CROME_Oxon_dissolve")
    Hab_field = "Interpreted_habitat"
    out_gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data\Merge_OSMM_HLU_ALC.gdb"
    arcpy.env.workspace = out_gdb
    out_map = "OSMM_HLU_CROME"

# Which stages of the code do we want to run?
merge_CROME = True
interpret_CROME = True

if merge_CROME:
    # Create a feature layer copy of the main table
    arcpy.MakeFeatureLayer_management(out_map, "ag_lyr")
    # Add in a unique ID for each polygon in the main table, to use for joining later
    print("      Copying OBJECTID for base map")
    MyFunctions.check_and_add_field("ag_lyr", "BaseID", "LONG", 0)
    arcpy.CalculateField_management("ag_lyr", "BaseID", "!OBJECTID!", "PYTHON_9.3")
    # Select agricultural habitats as these are the ones for which we are interested in CROME
    # Don't include arable field margins as they are probably accurately mapped
    # Also don't include ''Natural surface' as this is mainly road verges and amenity grass in urban areas
    print ("Identifying farmland")
    expression = Hab_field + " IN ('Agricultural land', 'Cultivated/disturbed land', 'Arable', " \
                             "'Arable and scattered trees', 'Improved grassland', 'Improved grassland and scattered scrub')"
    arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause = expression)
    # Calculating percentage of farmland features within CROME polygons
    # This only intersects the selected (agricultural) polygons
    print("Tabulating intersections")
    arcpy.TabulateIntersection_analysis("ag_lyr", ["OBJECTID", Hab_field, "BaseID", "Shape_Area"],
                                        CROME_data, "CROME_TI", ["LUCODE", "Land_Use_Description", "field", "Shape_Area"])
    # Sorting TI table by size so that larger intersections are first in the list
    print("Sorting table with largest intersections first")
    arcpy.Sort_management("CROME_TI", "CROME_TI_sort", [["AREA", "DESCENDING"]])
    # Delete all but the largest intersection. We need to do this, otherwise the join later is not robust - the wrong rows can be
    # copied across even if we think we have selected and joined to the right rows.
    print("Deleting identical (smaller intersection) rows")
    arcpy.DeleteIdentical_management("CROME_TI_sort", ["OBJECTID_1"])
    arcpy.MakeTableView_management("CROME_TI_sort", "CROME_lyr")
    # Adding fields for CROME data
    MyFunctions.check_and_add_field(out_map, "CROME_desc", "TEXT", 50)
    MyFunctions.check_and_add_field(out_map, "CROME_simple", "TEXT", 30)
    # Join the intersected table to join in the largest intersection to each polygon
    print ("Joining CROME info for base map polygons")
    arcpy.AddJoin_management("ag_lyr", "BaseID", "CROME_lyr", "BaseID", "KEEP_ALL")
    # Select only agricultural CROME polygons and intersections where there is >30% overlap
    # Data will only be copied for the selected polygons
    expression = "field IN ('Cereal Crops', 'Leguminous Crops', 'Grassland', 'Energy Crop', 'Trees') AND PERCENTAGE > 30"
    arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause=expression)
    # Copy data from ag_lyr which is now joined with CROME into the main layer
    print("Copying CROME data")
    arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_desc", "!CROME_TI_sort.Land_Use_Description!", "PYTHON_9.3")
    print("Finished copying CROME desc")
    arcpy.CalculateField_management("ag_lyr", out_map + ".CROME_simple", "!CROME_TI_sort.field!", "PYTHON_9.3")
    print("Finished copying CROME simple")

    # Remove the join
    arcpy.RemoveJoin_management("ag_lyr", "CROME_TI_sort")
    arcpy.Delete_management("ag_lyr")
    arcpy.Delete_management("CROME_lyr")
    print("Finished merging CROME")

if interpret_CROME:
    print ("Interpreting")
    # If CROME says grass and interpretation is currently arable, change it. But most 'fallow' land looks more like arable than grass
    # in Google earth, so set that to arable as well (even though CROME simple description is grass).
    expression = "CROME_desc = 'Grass' AND " \
                 + Hab_field + " IN ('Agricultural land', 'Arable', 'Cultivated/disturbed land', 'Natural surface')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland'")
    # If CROME says 'arable and scattered trees' is grass, change to 'Improved grassland and scattered trees'
    # (in fact there are no polygons like this).
    expression = "CROME_desc = 'Grass' AND " +  Hab_field + " = 'Arable and scattered trees'"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland and scattered trees'")
    # If CROME says arable and habitat is improved grassland or general agricultural, change. But don't change improved grassland
    # with scattered scrub, as inspection shows that is mainly small non-farmed areas that do not fit the CROME hexagons well.
    expression = "CROME_simple IN ('Cereal Crops', 'Leguminous Crops', 'Fallow') AND " + Hab_field + \
                 " IN ('Agricultural land', 'Cultivated/disturbed land', 'Improved grassland', 'Natural surface')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")
    # Examination for Oxon shows only two single CROME polygons for SRC, both look like mis-classifications so ignore
    # Similarly, ignore for now the Nursery trees and Perennial crops or isolated trees categories in CROME as they look dodgy, some look
    # like grassland and some like arable though some could actually be correct.

print(''.join(["## Finished on : ", time.ctime()]))

exit()
