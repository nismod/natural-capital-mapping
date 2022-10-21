# Habitat corrections for OMHD and PHI in Northern Powerhouse
# Attempts to identify OHMD polygons that have subsequently been redeveloped
# Assumes that if a certain proportion of the polygon now consists of buildings, roads and gardens then it is no longer OHMD
# Then it reclassifies any habitats classified as OHMD within that polygon as the OSMM habitat, ie probably sealed surface or amenity grass.
# Also, reclassifies OSMM 'natural surface' within PHI Deciduous woodland as natural surface.

import time, arcpy
import os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

folder = r"M:\urban_development_natural_capital\LADs"
arcpy.env.workspace = folder
# done "Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
#              "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
#              "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb",
#              "Craven.gdb", "Darlington.gdb", "Doncaster.gdb", "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
#              "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
#              "Lancaster.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
#              "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
#              "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
#              "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
#              "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
#              "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
#              "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wirral.gdb",
#              "Wyre.gdb", "York.gdb"
LAD_names = ["Leeds.gdb"]
gdbs = []
for LAD_name in LAD_names:
    gdbs.append(os.path.join(folder, LAD_name.replace(" ", "")))

out_map = "OSMM_CR_PHI_ALC_Desig_GS_PA"
Hab_field = "Interpreted_habitat_temp"

i = 0
for gdb in gdbs:
    i = i + 1
    arcpy.env.workspace = gdb
    print (''.join(["### Started processing ", gdb, " on : ", time.ctime()]) + " This is number " + str(i) + " out of " + str(len(gdbs)))
    # Copy corrected OSMM_hab over to Interpreted_habitat but only for the rows that do not get overridden by PHI
    # or where PHI is corrected later
    print "Adding new temp habitat field"
    MyFunctions.check_and_add_field(out_map, Hab_field, "TEXT", 100)
    arcpy.CalculateField_management(out_map, Hab_field, "!Interpreted_habitat!", "PYTHON_9.3")

    print "Setting natural surface back to that for PHI woodland"
    expression = "(PHI = 'Deciduous woodland' AND OSMM_hab = 'Natural surface')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "!OSMM_hab!")

    print "Copying CROME interpretation"
    expression = "CROME_desc = 'Grass' AND " + Hab_field + " IN ('Agricultural land')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Improved grassland'")
    expression = "CROME_simple IN ('Arable', 'Fallow land') AND " + Hab_field + " IN ('Agricultural land')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression, "'Arable'")

    print "Adding grazing marsh"
    expression3 = "PHI LIKE '%grazing marsh%' AND (" + Hab_field + " LIKE '%grass%' AND " + Hab_field + " NOT LIKE '%scattered%')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland'")
    expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered scrub'"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered scrub'")
    expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: broadleaved'"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: broadleaved'")
    expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: mixed'"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: mixed'")
    expression3 = "PHI LIKE '%grazing marsh%' AND " + Hab_field + " LIKE '%grassland with scattered trees: coniferous'"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Marshy grassland with scattered trees: coniferous'")

    print "Adding OMHD"
    expression5 = "(OMHD IS NOT NULL AND OMHD <> '') AND (" + Hab_field
    expression5 = expression5 + " IN ('Arable', 'Agricultural land', 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land'," \
                                  " 'Bare ground', 'Landfill: disused', 'Quarry or spoil: disused', 'Quarry or spoil', 'Sealed surface'))"
    MyFunctions.select_and_copy(out_map, Hab_field, expression5, "'Open mosaic habitats'")

    print "Adding WPP"
    expression3 = "(WPP IS NOT NULL AND WPP <> '') AND (" \
                  + Hab_field + " IN ('Agricultural land', 'Improved grassland', 'Natural surface', 'Cultivated/disturbed land') OR " \
                  + Hab_field + " LIKE 'Scattered%' OR " + Hab_field + " LIKE 'Semi-natural grassland%')"
    MyFunctions.select_and_copy(out_map, Hab_field, expression3, "'Parkland and scattered trees: broadleaved'")

exit()