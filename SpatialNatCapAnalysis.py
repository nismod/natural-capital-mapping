# Analyses natural capital scores within a site boundary, either for the whole site or
# for a series of sub-areas, which could represent different development scenarios
# INPUT:
# 1. (If using sub-areas): dataset containing boundaries of each 'scenario'.
# 2. NatCap scores.
# 3. Line features - PROW, Sustrans routes, hedges, rivers, waterlines
# 4. Point features - ancient trees
# Initially I tried to write the results to an output table then export to excel,
# but could not get that to work (see V1). Now I write to a text file, but export
# the natural capital scores directly to Excel as well (provided that there are
# less than the 60,000 row limit, so no good for whole district or county).
######################################################################################

import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Define input parameters
# -----------------------

region = "Arc"
# region = "Oxon"
# region = "Blenheim"
use_whole_area = False
Run_name = "ATI_"

if region == "Oxon":
    ncdir = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital"
    outdir = ncdir
    ncgdb = os.path.join(ncdir, "Oxon_full.gdb")
    out_gdb = os.path.join(ncdir, "Scenario_analysis.gdb")
    arcpy.env.workspace = ncgdb
    if use_whole_area:
        Scenario_features = "Oxfordshire"
        short_label = False
    else:
        # Scenario_features = "Spatial_strategy_options"
        Scenario_features = "OP2050_haloes"
        short_label = True
    Score_features = ["NatCap_Oxon"]
    hab_field = "Interpreted_habitat"
    ssdir = r"D:\cenv0389\Oxon_GIS\Spreadsheets"
    lines = ["Hedges"]
    data_gdb = ncgdb
    tree_data = os.path.join(data_gdb, "AncientTrees")
elif region == "Arc":
    ncdir = r"D:\cenv0389\Oxon_GIS\OxCamArc\NaturalCapital"
    ncgdb = os.path.join(ncdir, "NaturalCapital.gdb")
    outdir = r"D:\cenv0389\Oxon_GIS\OxCamArc\ATI"
    out_gdb = os.path.join(outdir, "ATI.gdb")
    arcpy.env.workspace = ncgdb
    Scenario_features = "ATI_scenarios"
    Score_features = ["NatCap_Arc_not_Oxon", "NatCap_Oxon"]
    hab_field = "Interpreted_habitat"
    ssdir = r"D:\cenv0389\Oxon_GIS\Spreadsheets"
    lines = []
    data_gdb = ncgdb
    short_label = False
    tree_data = os.path.join(data_gdb, "AncientTrees")
elif region == "Blenheim":
    ncdir = r"D:\cenv0389\Blenheim"
    outdir = ncdir
    ncgdb = os.path.join(ncdir, "Blenheim.gdb")
    out_gdb = os.path.join(ncdir, "Blenheim.gdb")
    arcpy.env.workspace = ncgdb
    Scenario_features = "Blenheim_estate_and_park_boundaries"
    data_gdb = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb"
    # Can either clip out from NatCap_Oxon (set use_whole_area to False) or use existing Estate and Park (e.g. if ground truthed)
    # Score_features = ["NatCap_Oxon"]
    Score_features = ["NatCap_Estate", "NatCap_Park"]
    hab_field = "Interpreted_habitat"
    ssdir = r"D:\cenv0389\Blenheim"
    lines = ["Hedges", "PROW", "Sustrans_offroad", "National_trails_Ox", "OS_rivers_Ox", "zoom_waterlines_Ox_local"]
    short_label = False
    # note: some of the ancient trees are just outside the estate boundary (in a 20m buffer) because the boundary is inaccurately drawn,
    # but they should be included. So you should replace the tree numbers output here with the actual numbers in the input dataset.
    tree_data = os.path.join(ncgdb, "EstateVet_WTAncientTrees")

# What stages of the code do we want to run?
calc_trees = True
calc_lines = False
high_nc_polygons = True
calculate_habitat_areas = True
calculate_scores = True
export_to_excel = True
if use_whole_area:
    intersect_scenarios = False
    clip_scenario_intersections = False
else:
    intersect_scenarios = True   # can still turn off if done already
    # Do we want to clip to the exact boundary of the spatial scenarios (True), or select all polygons that intersect and therefore could
    # in theory be affected by the development (False)? Set this to True even if we are clipping but the stage has already been completed,
    # as it is needed to decide whether the intersection file name ends in "_clip" or not.
    clip_scenario_intersections = True

# Do we want to get list of services from a lookup table or hardcoded?
service_lookup = "hardcoded"

# Main code starts here
# ---------------------

if service_lookup == "hardcoded":
    service_list = ["Food", "Food_ALC_norm", "Wood", "Fish", "WaterProv", "Flood", "Erosion", "WaterQual", "Carbon", "AirQuality",
                "Cooling", "Noise", "Pollination", "PestControl", "Rec_access", "Aesthetic_norm", "Education_desig", "Nature_desig",
                "Sense_desig", "Biodiversity"]
elif service_lookup == "info_table":
    InfoTable = "NatCapMaps"
    # Get a list of ecosystem service fields from InfoTable
    service_list = []
    services = arcpy.da.SearchCursor(InfoTable, "Field")
    for service in services:
        service_list.append(str(service[0]))

if calculate_scores:
    outfile1 = Run_name + "Scenario_analysis_scores.txt"
    file1 = os.path.join(outdir, outfile1)
    print ("Opening output file: " + file1)
    f1 = open(file1, "w")

if calc_trees or calc_lines or high_nc_polygons:
    outfile2 = Run_name + "Scenario_analysis_assets.txt"
    file2 = os.path.join(outdir, outfile2)
    print ("Opening output file: " + file2)
    f2 = open(file2, "w")

# Find scenario names as unique values in scenario file.
cursor = arcpy.da.SearchCursor(Scenario_features, "Scenario")
scenarios = sorted({row[0] for row in cursor})
del cursor

i = 0
for scenario in scenarios:
    i = i + 1
    if short_label:
        label = "S" + str(i)
    else:
        label = scenario
    arcpy.MakeFeatureLayer_management(Scenario_features, "scen_lyr")
    expression = "Scenario = " + "'" + scenario + "'"
    arcpy.SelectLayerByAttribute_management("scen_lyr", where_clause= expression)
    if calc_trees or calc_lines or intersect_scenarios:
        print("Processing " + scenario)

    # Calculate number of ancient trees and line features (hedges, paths, rivers etc) in each scenario zone
    if calc_trees:
        arcpy.MakeFeatureLayer_management(tree_data, "tree_lyr")
        arcpy.SelectLayerByLocation_management("tree_lyr", "WITHIN", "scen_lyr")
        num_trees = arcpy.GetCount_management("tree_lyr")
        print ("  There are " + str(num_trees) + " trees in the area covered by " + scenario)
        f2.writelines("\n" + scenario + ", Number of ancient trees, " + str(num_trees))

    if calc_lines:
        for line in lines:
            line_data = os.path.join(data_gdb, line)
            line_scenario = os.path.join(out_gdb, label + "_" + line)
            print("  Calculating " + line + " length")
            arcpy.Intersect_analysis(["scen_lyr", line_data], line_scenario)
            line_list = []
            with arcpy.da.SearchCursor(line_scenario, ["Shape_Length"]) as cursor:
                for row in cursor:
                    line_list.append(row[0])
            line_length = sum(line_list)
            print("  " + line + " length is: " + str(line_length))
            f2.writelines("\n" + scenarios[i - 1] + ", " + line + " length (m), " + str(line_length))

    # Select all polygons from the natural capital layer(s) that intersect each spatial strategy zone and save to a new file
    if intersect_scenarios:
        print("  Intersecting " + scenario)
        for score_feature in Score_features:
            print ("   Score features: " + score_feature)
            arcpy.MakeFeatureLayer_management(os.path.join(data_gdb, score_feature), "score_lyr")
            arcpy.SelectLayerByLocation_management("score_lyr", "INTERSECT", "scen_lyr")
            intersect_fc = os.path.join(out_gdb, label + "_" + score_feature + "_intersect")
            arcpy.CopyFeatures_management("score_lyr", intersect_fc)
            # Optional: clip
            if clip_scenario_intersections:
                print ("   Clipping " + intersect_fc)
                arcpy.Clip_analysis(intersect_fc, "scen_lyr", intersect_fc + "_clip")
                # Note: some scenarios extend beyond the Oxfordshire boundary

    if export_to_excel:
        if use_whole_area:
            export_table = Score_features[i-1]
        else:
            export_table = intersect_fc + "_clip"
        num_rows = arcpy.GetCount_management(export_table)
        print("Number of rows in " + export_table + " is " + str(num_rows))
        if num_rows > 60000:
            # For some reason this line executes even when there are less than 60000 rows..?
            print("Cannot export natural capital score data to Excel because table has over 60,000 rows: there are " + str(num_rows))
        else:
            print("Exporting " + label + " to Excel")
            arcpy.TableToExcel_conversion(export_table, os.path.join(ssdir, "NatCap_" + label + ".xls"))

    arcpy.Delete_management("scen_lyr")

# Add up scores in each zone for each ecosystem service
i = 0
for scenario in scenarios:
    i = i + 1

    if i == 1:
        if calculate_scores:
            # Write header of service names
            f1.writelines("Services, Area, " + ", ".join(service_list))
        if high_nc_polygons:
            expressions = ["MaxRegCult > 5", "MaxRegCult > 7.5", "MaxRegCult > 7.5 AND Av15WSRegCult >5", "Food_ALC_norm > 7.5"]
            f2.writelines("\nHigh natural capital asset areas (m2): criteria, " + ", ".join(expressions))

    print("Processing " + scenarios[i-1])
    for score_feature in Score_features:
        print("  Processing " + score_feature)

        # Identify the name of the input file
        if short_label:
            label = "S" + str(i)
        else:
            label = scenario
        if use_whole_area:
            sfile = score_feature
        else:
            sfile = os.path.join(out_gdb, label + "_" + score_feature + "_intersect")
            if clip_scenario_intersections:
                sfile = sfile + "_clip"
        print ("    Working with " + sfile)

        if calculate_habitat_areas:
            print ("    Summarising habitats")
            hab_table_name = label + "_" + score_feature + "_habitats"
            hab_table = os.path.join(out_gdb, hab_table_name)
            arcpy.Statistics_analysis(sfile, hab_table, [["Shape_Area", "SUM"]], hab_field)
            print ("    Exporting habitat table to Excel")
            arcpy.TableToExcel_conversion(hab_table, os.path.join(ssdir, hab_table_name + "_" + region + ".xls"))

        if calculate_scores:
            print("    Calculating area")
            area_list = []
            with arcpy.da.SearchCursor(sfile, ["Shape_Area"]) as cursor:
                for row in cursor:
                    area_list.append(row[0])
            # Convert from m2 to ha
            scenario_area = sum(area_list)/10000
            print("    Area is: " + str(scenario_area))
            f1.writelines("\n" + scenarios[i - 1] + " " + score_feature + ", " + str(scenario_area) + ", ")

            # Work out total scores for each ecosystem service
            result_list = []
            for service in service_list:
                # Multiply score by shape area for each row, and add up total
                print("    Service: " + service)
                list = []
                with arcpy.da.SearchCursor(sfile, [service, "Shape_Area"]) as cursor:
                    for row in cursor:
                        list.append(row[0] * row[1])
                # Divide by 10000 because score is per ha but areas are per m2 (added 15/9/2020; previously we did this manually afterwards)
                sumlist = sum(list)/10000
                print(service + " sum is:" + str(sumlist))
                result_list.append(sumlist)

            # Enter results into output table
            print ("    Results for " + scenarios[i-1] + " are " + str(result_list))
            # Create a comma-separated string of values
            result_strings = [str(res) for res in result_list]
            f1.writelines(", ".join(result_strings))

        if high_nc_polygons:
            print("    Identifying high scoring polygons")
            f2.writelines("\n" + scenarios[i - 1] + " " + score_feature)
            for expression in expressions:
                arcpy.MakeFeatureLayer_management(sfile, "nc_lyr")
                arcpy.SelectLayerByAttribute_management("nc_lyr", where_clause=expression)
                list = []
                with arcpy.da.SearchCursor("nc_lyr", ["Shape_Area"]) as cursor:
                    for row in cursor:
                        list.append(row[0])
                sumlist = sum(list)
                print("   " + expression + " area is: " + str(sumlist))
                f2.writelines(", " + str(sumlist))
                arcpy.Delete_management("nc_lyr")

        print("  Finished " + scenarios[i-1] + " at " + time.ctime())

if calculate_scores:
    f1.close()
    print("Scores exported to " + file1 + " at " + time.ctime())
if calc_trees or calc_lines or high_nc_polygons:
    f2.close()
    print("Assets exported to " + file2 + " at " + time.ctime())

exit()
