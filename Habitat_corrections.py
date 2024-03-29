# OSMM_hab has been corrected already, now we need to correct Interpreted_habitat as well
# Temporary habitat corrections following late changes for new habitats in Northern Powerhouse
# But it is complicated because of subsequent changes when PHI and Greenspace were merged in
# This code deals with PHI. then we need to re-run the Greenspace interpretation section.
#
import time, arcpy
import os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

folder = r"M:\urban_development_natural_capital\LADs"
arcpy.env.workspace = folder
# done [,]
LAD_names = ["Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
             "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
             "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb",
             "Craven.gdb", "Darlington.gdb", "Doncaster.gdb", "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
             "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
             "Lancaster.gdb",  "Leeds.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
             "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
             "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
             "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
             "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
             "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
             "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wirral.gdb",
             "Wyre.gdb", "York.gdb"]
gdbs = []
for LAD_name in LAD_names:
    gdbs.append(os.path.join(folder, LAD_name.replace(" ", "")))

# out_map = "OSMM_CR_PHI_ALC_Desig_GS_PA"
out_map = "OSMM_CR_PHI_ALC_Desig_GS"
Hab_field = "Interpreted_habitat_temp"

i = 0
for gdb in gdbs:
    i = i + 1
    arcpy.env.workspace = gdb
    print (''.join(["### Started processing ", gdb, " on : ", time.ctime()]) + " This is number " + str(i) + " out of " + str(len(gdbs)))
    # Copy corrected OSMM_hab over to Interpreted_habitat. Previously did this only for the rows that do not get overridden by PHI
    # or where PHI is corrected later, but this does not work at the moment because I did subsequent incorrect corrections that affected PHI rows!
    # So those rows now commented out, and am re-running Interpret_PHI from Merge_CROME_PHI.py instead
    print "Adding new temp habitat field"
    MyFunctions.check_and_add_field(out_map, Hab_field, "TEXT", 100)
    # arcpy.CalculateField_management(out_map, Hab_field, "!Interpreted_habitat!", "PYTHON_9.3")

    # print "Copying OSMM_hab but not where PHI has been used instead"
    # expression = "(PHI IS NULL OR PHI = '' OR PHI LIKE 'No main%' OR PHI LIKE 'Wood-pasture%' or PHI LIKE 'Open Mosaic%' "
    # expression = expression + " OR PHI LIKE '%grazing marsh')"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression, "!OSMM_hab!")
    print "Copying OSMM_hab to temporary Interpreted_habitat field"
    arcpy.CalculateField_management(out_map, Hab_field, "!OSMM_hab!", "PYTHON_9.3")

    print "Copying CROME interpretation"
    expression = "CROME_desc = 'Grass' AND " + Hab_field + " IN ('Agricultural land')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland'")
    expression = "CROME_simple IN ('Arable', 'Fallow land') AND " + Hab_field + " IN ('Agricultural land')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")

    # print "Adding grazing marsh"
    # expression3 = "PHI LIKE '%grazing marsh%' AND (" + Hab_field + " LIKE '%grass%' AND " + Hab_field + " NOT LIKE '%scattered%')"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland'")
    # expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered scrub'"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered scrub'")
    # expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: broadleaved'"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: broadleaved'")
    # expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: mixed'"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: mixed'")
    # expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: coniferous'"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: coniferous'")
    #
    # print "Adding OMHD"
    # expression5 = "(OMHD IS NOT NULL AND OMHD <> '') AND (" + Hab_field
    # expression5 = expression5 + " IN ('Arable', 'Agricultural land', 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land'," \
    #                               "'Bare ground', 'Landfill: disused', 'Quarry or spoil: disused', 'Quarry or spoil', 'Sealed surface'))"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression5, "'Open mosaic habitats'")
    #
    # print "Adding WPP"
    # expression3 = "(WPP IS NOT NULL AND WPP <> '') AND (" \
    #               + Hab_field + " IN ('Agricultural land', 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land') OR " \
    #               + Hab_field + " LIKE 'Scattered%' OR " + Hab_field + " LIKE 'Semi-natural grassland%')"
    # MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Parkland and scattered trees: broadleaved'")

exit()