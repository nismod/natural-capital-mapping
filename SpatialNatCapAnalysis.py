# Spatial natural capital analysis
# --------------------------------
# This is a research tool and has not been tested for wider use
# However it is available for your own use under a Creative Commons License provided that you use the following attribution statement:
# "These results were generated using software developed by Alison Smith, Environmental Change Institute, University of Oxford"
# ----------------------------------------------------------------------------------
# Analyses natural capital assets and ecosystem service scores within a site boundary. Assets include high-scoring areas plus line and
# point features. There are currently four different types of 'high-scoring areas':
# 1. maximum score for regulating and cultural services over 5 out of 10
# 2. maximum score for regulating and cultural services over 7.5 out of 10
# 3. maximum score for regulating and cultural services over 7.5 out of 10 and average score over 5
# 4. areas scoring over 7.5 out of 10 for food production.
# Scores are calculated by adding up the scores for each polygon multiplied by the polygon area.
#
# Select a method:
# 1. Single_area: Export total assets and scores for a single site (however there can still be more than one 'Score_features' input file,
#     e.g. for adjacent areas or multiple versions of the same area)
# 2. Spatial_scenarios: Export for a series of sub-areas ('Scenario_features'), e.g. different development scenarios.
#    Separate clipped feature classes will be created for each scenario and can be exported as Excel files if required (see below).
# 3. Select_attributes: Analyse a series of options based on sub-selecting by attribute. These will not be exported
#    as separate feature classes, to save space and avoid cluttering up the geodatabases. The script will find all the unique values
#    of the specified attribute and select rows matching each value each in turn. Only one input score dataset should be used.
# 4. Score_differences. Analyses the reasons for differences in ecosystem service scores between two datasets. A single dataset containing
#    the differences (storing the difference in scores for each ES in a series of attributes named using the format 'service_diff')
#    should have been previously created using Compare_fcs.py and Differences.py. Differences will be output
#    by selecting each unique value of the 'DetailedReasons' attribute. This records either the habitats in the two comparison datasets
#    ('habitat in dataset 1 vs habitat in dataset 2') or different multipliers (ALC difference, Designation difference or Public access
#    difference). In some cases we need to add the absolute values of the scores, otherwise negative and positive scores would partially
#    cancel out. However where the difference is due to habitat type, the scores for each 'reason for difference' should have a constant
#    sign. This is not necessarily for the multiplier differences, so we add up absolute values for those.
# INPUTS:
# 1. Score_features: Array of input natural capital dataset(s) containing ecosystem service scores for each polygon. There can be
#    more than one, e.g. adjacent areas, or alternative versions of the same area.
# 2. Line features (optional) - PROW, Sustrans routes, hedges, rivers, waterlines
# 3. Point features (optional) - ancient trees
# 4. Scenario_features (if using Spatial_scenarios method): array of dataset(s) containing boundaries of each spatial 'scenario',
#    which must have an attribute called 'Scenario' that lists the names of each spatial scenario.
#
# OUTPUTS: two text files, one for assets and one for scores.
# Writing results to an output table then exporting to excel did not work. Now there is a facility to export the natural capital scores
# directly to Excel as well (provided that there are less than the 60,000 row limit, so no good for whole district or county).
# Currently this does not work - suspect bug with GetCount.
# However the feature classes created for each scenario (if using Spatial_scenarios option) can be manually exported to Excel if required.
##########################################################################################################################

import time, arcpy, os, MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Define input parameters
# -----------------------

# region = "Arc_ATI"
# region = "Arc_EA"
region = "Oxon"
# region = "Blenheim"

# Select method (see header)
# method = "Single_area"
method = "Spatial_scenarios"
# method = "Select_attributes"
# method = "Score_differences"

# Set a name to identify the output files - otherwise previous files will be overwritten
# Run_name = "ATI_"
# Run_name = "OP2050_1kmHalos_"
# Run_name = "EA_Paid_minus_Free_"
# Run_name = "EA_Paid_data"
# Run_name = "Oxon_LADs"
Run_name = "Oxon_LADs"

if region == "Oxon":
    ncdir = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital"
    outdir = ncdir
    ncgdb = os.path.join(ncdir, "Oxon_full.gdb")
    # out_gdb = os.path.join(ncdir, "Scenario_analysis.gdb")
    out_gdb = os.path.join(ncdir, "Oxon_LADs.gdb")
    data_gdb = ncgdb
    if method == "Single_area":
        Scenario_features = os.path.join(ncgdb,"Oxfordshire")
        short_label = False
    else:
        # Scenario_features = os.path.join(out_gdb, "ScenariosDesShort")
        Scenario_features = os.path.join(out_gdb, "Oxon_LADs")
        short_label = False
    # arcpy.env.workspace = out_gdb
    arcpy.env.workspace = ncgdb
    Score_features = ["NatCap_Oxon"]
    hab_field = "Interpreted_habitat"
    ssdir = r"D:\cenv0389\Spreadsheets"
    # lines = [os.path.join(data_gdb, "Hedges")]
    lines = []
    # line_labels = ["Hedges"]
    line_labels = ["Hedges", "PROW", "Sustrans_offroad", "National_trails_Ox", "OS_rivers_Ox", "zoom_waterlines_Ox_local"]
    for line in line_labels:
        lines.append(os.path.join(data_gdb, line))
    tree_data = os.path.join(data_gdb, "AncientTrees")
    tree_label = "AncientTrees"
elif region == "Arc_ATI":
    ncdir = r"D:\cenv0389\Oxon_GIS\OxCamArc\NaturalCapital"
    ncgdb = os.path.join(ncdir, "NaturalCapital.gdb")
    outdir = r"D:\cenv0389\Oxon_GIS\OxCamArc\ATI"
    out_gdb = os.path.join(outdir, "ATI.gdb")
    arcpy.env.workspace = ncgdb
    Scenario_features = os.path.join(out_gdb,"ATI_scenarios")
    Score_features = ["NatCap_Arc_not_Oxon", "NatCap_Oxon"]
    hab_field = "Interpreted_habitat"
    ssdir = r"D:\cenv0389\Oxon_GIS\Spreadsheets"
    lines = []
    data_gdb = ncgdb
    short_label = False
    tree_data = os.path.join(data_gdb, "AncientTrees")
    tree_label = "AncientTrees"
elif region == "Arc_EA":
    ncdir = r"D:\cenv0389\OxCamArc"
    if method == "Single_area":
        ncgdb = os.path.join(ncdir, "NatCap_Arc_PaidData.gdb")
        Scenario_features = "Arc_outline"
        Score_features = ["NatCap_Arc_PaidData"]
    elif method == "Score_differences":
        ncgdb = os.path.join(ncdir, "Comparison.gdb")
        Score_features = ["Paid_vs_Free_Non_matching"]
        Select_attribute = "DetailedReason"
    outdir = ncdir
    out_gdb = ncgdb
    arcpy.env.workspace = ncgdb
    hab_field = "Interpreted_habitat"
    ssdir = ncdir
    lines = []
    data_gdb = ncgdb
    short_label = False
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
    line_labels = ["Hedges", "PROW", "Sustrans_offroad", "National_trails_Ox", "OS_rivers_Ox", "zoom_waterlines_Ox_local"]
    tree_label = "AncientTrees"

# What stages of the code do we want to run?
first_part = True
second_part = True
high_nc_polygons = True
calculate_scores = True

if method == "Spatial_scenarios":
    intersect_scenarios = True   # usually True but can turn off if done already
    # Do we want to clip to the exact boundary of the spatial scenarios (True), or select all polygons that intersect and therefore could
    # in theory be affected by the development (False)? Set this to True even if we are clipping but the stage has already been completed,
    # as it is needed to decide whether the intersection file name ends in "_clip" or not.
    clip_scenario_intersections = True    # Usually true
    calculate_habitat_areas = True
    calc_trees = True       # Optional
    calc_lines = True       # Optional
    export_to_excel = True  # Optional
    # Find scenario names as unique values in scenario file. This contains outlines of different spatial scenarios and
    # must have an attribute called 'Scenario' which lists the scenario names
    cursor = arcpy.da.SearchCursor(Scenario_features, "Scenario")
    scenarios = sorted({row[0] for row in cursor})
    del cursor
else:
    intersect_scenarios = False
    clip_scenario_intersections = False
    if method == "Single_area":
        calculate_habitat_areas = False  # Optional
        calc_trees = False  # Optional
        calc_lines = False  # Optional
        export_to_excel = False  # optional
        # Scenario_features is the outline of a single area to analyse
        scenarios = [Scenario_features]
    elif method == "Select_attributes" or method == "Score_differences":
        calculate_habitat_areas = False  # Not recommended if large number of attribute values
        calc_trees = False               # Not recommended if large number of attribute values
        calc_lines = False               # Not recommended if large number of attribute values
        export_to_excel = False          # Not recommended if large number of attribute values
        # Scenarios are a list of unique values for the attribute of interest
        attribute_values = [row[0] for row in arcpy.da.SearchCursor(Score_features[0], Select_attribute)]
        scenarios = set(attribute_values)
        print("\n".join(scenarios))

# Do we want to clip out the point features into separate features for each scenario in the output database?
clip_point = True
# Do we want to clip the output files into a single output gdb or into separate (pre-created) gdbs for each scenario?
separate_outgdbs = True
separate_outgdb_suffix = "_Nat_Cap.gdb"

# Do we want to add up the absolute value of the scores? We need to do this when we are assessing the magnitude of
# differences that could be either positive or negative
if method == "Score_differences":
    abs_values = True
else:
    abs_values = False

# Do we want to get list of services from a lookup table or hardcoded?
service_lookup = "hardcoded"

# Main code starts here
# ---------------------

if service_lookup == "hardcoded":
    if method == "Score_differences":
        service_list = ["Food_ALC_norm", "Wood", "Fish", "WaterProv", "Flood", "Erosion", "WaterQual", "Carbon", "AirQuality",
                    "Cooling", "Noise", "Pollination", "PestControl", "Rec_access", "Aesthetic_norm", "Education_desig", "Nature_desig",
                    "Sense_desig"]
    else:
        service_list = ["Food", "Food_ALC_norm", "Wood", "Fish", "WaterProv", "Flood", "Erosion", "WaterQual", "Carbon", "AirQuality",
                    "Cooling", "Noise", "Pollination", "PestControl", "Rec_access", "Aesthetic_norm", "Education_desig", "Nature_desig",
                    "Sense_desig", "Biodiversity"]
elif service_lookup == "info_table":
    InfoTable = os.path.join(ncdir, "NatCapMaps")
    # Get a list of ecosystem service fields from InfoTable
    service_list = []
    services = arcpy.da.SearchCursor(InfoTable, "Field")
    for service in services:
        service_list.append(str(service[0]))

i = 0
if first_part:
    if calc_trees or calc_lines or high_nc_polygons:
        outfile1 = Run_name + "Scenario_analysis_assets.txt"
        file1 = os.path.join(outdir, outfile1)
        print ("Opening output file: " + file1)
        f1 = open(file1, "w")
    if calc_trees or calc_lines or intersect_scenarios or export_to_excel:
        for scenario in scenarios:
            print("Processing " + scenario)
            if separate_outgdbs:
                out_gdb = os.path.join(outdir, scenario + separate_outgdb_suffix)
            print "output gdb is:" + out_gdb
            i = i + 1
            if short_label:
                label = "S" + str(i)
            else:
                label = scenario

            if method == "Single_area":
                # Scenario_features is the outline of the whole area
                arcpy.MakeFeatureLayer_management(Scenario_features, "scen_lyr")
            elif method == "Spatial_scenarios":
                # Read scenario features from an input file of spatial outlines
                arcpy.MakeFeatureLayer_management(Scenario_features, "scen_lyr")
                expression = "Scenario = " + "'" + scenario + "'"
                arcpy.SelectLayerByAttribute_management("scen_lyr", where_clause= expression)
            elif method == "Select_attributes" or method == "Score_differences":
                # Scenarios are based on selected rows of the input score table
                print("Selecting rows for " + scenario)
                arcpy.MakeFeatureLayer_management(Score_features[0], "scen_lyr")
                expression = Select_attribute + " = '" + scenario + "'"
                arcpy.SelectLayerByAttribute_management("scen_lyr", where_clause= expression)
                print("Rows selected")

            # Calculate number of ancient trees and line features (hedges, paths, rivers etc) in each scenario zone
            if calc_trees:
                arcpy.MakeFeatureLayer_management(tree_data, "tree_lyr")
                arcpy.SelectLayerByLocation_management("tree_lyr", "WITHIN", "scen_lyr")
                if clip_point:
                    out_tree = os.path.join(out_gdb, tree_label + "_" + label)
                    arcpy.CopyFeatures_management("tree_lyr", out_tree)
                num_trees = arcpy.GetCount_management("tree_lyr")
                print ("  There are " + str(num_trees) + " ancient trees in the area covered by " + scenario)
                f1.writelines("\n" + scenario + ", Number of ancient trees, " + str(num_trees))

            if calc_lines:
                j=0
                for line in lines:
                    j= j + 1
                    line_data = os.path.join(data_gdb, line)
                    line_scenario = os.path.join(out_gdb, label + "_" + line_labels[j-1])
                    print("  Calculating " + line + " length")
                    arcpy.Intersect_analysis(["scen_lyr", line_data], line_scenario)

                    line_list = []
                    with arcpy.da.SearchCursor(line_scenario, ["Shape_Length"]) as cursor:
                        for row in cursor:
                            line_list.append(row[0])
                    line_length = sum(line_list)
                    print("  " + line + " length is: " + str(line_length))
                    f1.writelines("\n" + scenario + ", " + line + " length (m), " + str(line_length))

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
                if method != "Spatial_scenarios":
                    export_table = Score_features[i-1]
                else:
                    export_table = intersect_fc + "_clip"
                num_rows = arcpy.GetCount_management(export_table)
                # print("Number of rows in " + export_table + " is " + str(num_rows))
                if num_rows > 60000:
                    # For some reason this line executes even when there are less than 60000 rows..?
                    print("Cannot export natural capital score data to Excel because " + export_table +
                          " has over 60,000 rows: there are " + str(num_rows))
                else:
                    print("Exporting " + label + " to Excel")
                    arcpy.TableToExcel_conversion(export_table, os.path.join(ssdir, "NatCap_" + label + ".xls"))

            arcpy.Delete_management("scen_lyr")

# Add up scores in each zone for each ecosystem service
i = 0
if second_part:

    if calculate_scores:
        outfile2 = Run_name + "Scenario_analysis_scores.txt"
        file2 = os.path.join(outdir, outfile2)
        print ("Opening output file: " + file2)
        f2 = open(file2, "w")
    if high_nc_polygons:
        outfile3 = Run_name + "Scenario_analysis_high_nc_polygons.txt"
        file3 = os.path.join(outdir, outfile3)
        print ("Opening output file: " + file3)
        f3 = open(file3, "w")
    for scenario in scenarios:
        i = i + 1
        print("Scenario " + scenario)
        if separate_outgdbs:
            out_gdb = os.path.join(outdir, scenario + separate_outgdb_suffix)
        print "output gdb is:" + out_gdb

        if i == 1:
            if calculate_scores:
                # Write header of service names
                f2.writelines("Services, Area (ha), " + ", ".join(service_list))
            if high_nc_polygons:
                expressions = ["MaxRegCult > 5", "MaxRegCult > 7.5", "MaxRegCult > 7.5 AND Av15WSRegCult >5", "Food_ALC_norm > 7.5"]
                f3.writelines("\nHigh natural capital asset areas (ha): criteria, " + ", ".join(expressions))

        print("Processing " + scenario)
        for score_feature in Score_features:
            print("  Processing " + score_feature)

            # Identify the name of the input file
            if short_label:
                label = "S" + str(i)
            else:
                label = scenario

            if method == "Single_area":
                sfile = score_feature
            elif method == "Spatial_scenarios":
                sfile = os.path.join(out_gdb, label + "_" + score_feature + "_intersect")
                if clip_scenario_intersections:
                    sfile = sfile + "_clip"
            elif method == "Select_attributes" or method == "Score_differences":
                arcpy.MakeFeatureLayer_management(score_feature, "attr_lyr")
                expression = Select_attribute + " = '" + scenario + "'"
                arcpy.SelectLayerByAttribute_management("attr_lyr", where_clause=expression)
                sfile = "attr_lyr"
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
                f2.writelines("\n" + scenario + " " + score_feature + ", " + str(scenario_area) + ", ")

                # Work out total scores for each ecosystem service
                result_list = []
                for service in service_list:
                    if method == "Score_differences":
                        service = service + "_diff"
                        # Need to sort out absolute values for non-habitat differences - or maybe use abs as standard and post-process later?
                        # Set use of abs as a flag
                    # Multiply score by shape area for each row, and add up total
                    print("    Service: " + service)
                    list = []
                    with arcpy.da.SearchCursor(sfile, [service, "Shape_Area"]) as cursor:
                        for row in cursor:
                            if abs_values:
                                list.append(abs(row[0]) * row[1])
                            else:
                                list.append(row[0] * row[1])
                    # Divide by 10000 because score is per ha but areas are per m2 (added 15/9/2020; previously we did this manually afterwards)
                    sumlist = sum(list)/10000
                    print(service + " sum is:" + str(sumlist))
                    result_list.append(sumlist)

                # Enter results into output table
                print ("    Results for " + scenario + " are " + str(result_list))
                # Create a comma-separated string of values
                result_strings = [str(res) for res in result_list]
                f2.writelines(", ".join(result_strings))

            if high_nc_polygons:
                print("    Identifying high scoring polygons")
                f3.writelines("\n" + scenario + " " + score_feature)
                for expression in expressions:
                    arcpy.MakeFeatureLayer_management(sfile, "nc_lyr")
                    arcpy.SelectLayerByAttribute_management("nc_lyr", where_clause=expression)
                    list = []
                    with arcpy.da.SearchCursor("nc_lyr", ["Shape_Area"]) as cursor:
                        for row in cursor:
                            list.append(row[0])
                    sumlist = sum(list) / 10000
                    print("   " + expression + " area (ha) is: " + str(sumlist))
                    f3.writelines(", " + str(sumlist))
                    arcpy.Delete_management("nc_lyr")

            print("  Finished " + scenario + " at " + time.ctime())

if (calc_trees or calc_lines) and first_part:
    f1.close()
    print("Assets exported to " + file1 + " at " + time.ctime())
if calculate_scores and second_part:
    f2.close()
    print("Scores exported to " + file2 + " at " + time.ctime())
if high_nc_polygons and second_part:
    f3.close()
    print("High nat cap scoring polygons exported to " + file3 + " at " + time.ctime())

exit()
