# Sets up the correct symbology and layer names for grouped layers for each ecosystem service
# Each group of layers contains one layer for each local authority district
# At the moment, the groups have to be created manually in advance (it is quick to do this by creating one group and then copying)
# and each group must have exactly the same name as the attribute field name for that ecosystem service, e.g. "Rec_access" or "Carbon".
# The natural capital layers initially must end in "_LAD name", e.g. 'NatCap_Aylesbury', with no underscores in the LAD name
# They can then be renamed in the code to include the ES name, e.g. "NatCap_Carbon_Aylesbury"
# Separate symbology layers have to be saved in advance for each ecosystem service, matching the correct attribute and
# named "NatCap_Carbon.lyr" etc, where the ES part of the layer file name is exactly the same as the attribute field name for that service
# --------------------------------------------------------------------------------------------------------------------------

import time, arcpy, os
print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# Define input parameters
# -----------------------

# Workspace and mxd
ncdir = r"D:\cenv0389\OxCamArc"

# Symbology layers
symbology_dir = r"D:\cenv0389\OxCamArc\symbology"
# NC_symbology_file = r"D:\cenv0389\Oxon_GIS\Layer_symbologies\NatCap.lyr"
Hab_symbology_file = r"D:\cenv0389\Oxon_GIS\Layer_symbologies\Interpreted_habitat.lyr"
# NC_symbology = arcpy.mapping.Layer(NC_symbology_file)
Hab_symbology = arcpy.mapping.Layer(Hab_symbology_file)

# The ES list table should contain a list of all the ecosystem service layers to set up, with the name of the score field
# Not currently used, but could be used to allow more meaningful layer names (not having to match the ES attribute field name)
# ES_list = "ES_list"

# Use arccpy.mapping module to retrieve the mxd, data frame and symbology layer objects
# mxd = arcpy.mapping.MapDocument(r"D:\cenv0389\OxCamArc\OxCamArc_FreeData_LADs.mxd")
mxd = arcpy.mapping.MapDocument(r"D:\cenv0389\OxCamArc\OxCamArc_FreeData_LADs.mxd")
print("Map is " + mxd.filePath)
df = arcpy.mapping.ListDataFrames(mxd, "Layers")[0]

Layers = arcpy.mapping.ListLayers(mxd, "*", df)

for lyr in Layers:
    # print("Layer long name is " + lyr.longName)
    if lyr.name == lyr.longName:
        print("Skipping group layer " + lyr.name)
    elif "Habitat base map" in lyr.longName:
        print("Skipping " + lyr.longName)
        # LAD = lyr.longName.split("_")[2]
        # print("Changing symbology for layer: " + lyr.name + " to " + Hab_symbology.name)
        # arcpy.mapping.UpdateLayer(df, lyr, Hab_symbology)
        # lyr.name = "Habitats_" + LAD
        # lyr.description = "Habitat type"
    elif "MaxRegCult" in lyr.longName or "Food high" in lyr.longName or "Fast display" in lyr.longName:
        print("Skipping " + lyr.longName)
        # Skip as these are already set up - code below is commented out but can be used if you want to change the format of the names
        # num_items = len(lyr.longName.split("_"))
        # LAD = lyr.longName.split("_")[num_items-1]
        # lyr.name = "NatCap_FoodHighScores_" + LAD
    # elif "NatCap_" in lyr.name:
    elif "NatCap_Food_ALC" in lyr.name:
        ES = lyr.longName.split("\\")[0]
        num_items = len(lyr.longName.split("_"))
        LAD = lyr.longName.split("_")[num_items-1]
        print("Changing symbology for ES " + ES + " LAD " + LAD + " in " + lyr.longName)
        ES_symbology_file = os.path.join(symbology_dir, "NatCap_" + ES + ".lyr")
        ES_symbology = arcpy.mapping.Layer(ES_symbology_file)
        arcpy.mapping.UpdateLayer(df, lyr, ES_symbology)
        # This bit commented out because there is no way of changing the colours; they default back to the inbuilt colour ramp
        # So I had to set up individual layer files for each of the 18 ecosystem services instead, with the correct field name
        # if lyr.symbologyType == "GRADUATED_COLORS":
            # print("Changing symbology for layer: " + lyr.name)
            # lyr.symbology.valueField = ES
            # lyr.symbology.numClasses = 6
            # After changing the value field, the class break values will change so I need to set them back
            # But this still does not work because the colours change back to the inbuilt colour ramp, not the colours in my saved layer
            # lyr.symbology.classBreakValues = [0.0, 0.0, 1.0, 2.5, 5, 7.5, 10.0]
            # lyr.symbology.classBreakLabels = ["0", "0 to 1", "1.01 to 2.5", "2.51 to 5.0", "5.01 to 7.5", "7.51 to 10.0"]
        lyr.name = "NatCap_" + ES + "_" + LAD
        lyr.description = "Natural Capital scores"
    lyr.credits = "This layer incorporates OS MasterMap data: Crown Copyright and database rights 2020 Ordnance Survey 100025252."
print("Saving map document")
mxd.save()

del Hab_symbology
# del NC_symbology
del ES_symbology
del mxd

exit()