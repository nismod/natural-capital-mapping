#
# Sets up the table of natural capital scores
# Three starting files are needed:
# 1. Base map of habitats
# 2. Table of Agricultural Land Class multipliers "ALC_multipliers" with grade in "ALC_grade"
# 3. Matrix of scores for each habitat: "Matrix"
# Option to merge all LADs into a single file at the end
#----------------------------------------------------------------------------------------------

import time, arcpy, os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files
arcpy.env.qualifiedFieldNames = False

# region = "Arc"
region = "Oxon"
# region = "Blenheim"
# Choice of method that has been used to generate the input files - this determines location and names of input files
# method = "LCM_PHI"
method = "HLU"

if (region == "Oxon" or region == "Blenheim") and method == "HLU":
    folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital"
    arcpy.env.workspace = os.path.join(folder, "Oxon_full.gdb")
    if region == "Oxon":
        gdbs = [os.path.join(folder, "Oxon_full.gdb")]
        area_name = "Oxon"
        Base_map = "OSMM_HLU_CR_ALC_Des_GS_PA"
        # This is for when we do it by LAD instead, but at the moment we are still processing all the Oxon LADS in a single county dataset
        # folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc\NaturalCapital"
        # arcpy.env.workspace = os.path.join(folder, "NaturalCapital.gdb")
        # gdbs = [os.path.join(folder, "NaturalCapital.gdb")]
    elif region == "Blenheim":
        # This is for ground truthing updates to the Blenheim extract of the Oxon map
        gdbs = [r"D:\cenv0389\Blenheim\Blenheim.gdb"]
        # Nat cap map is expected to be called NatCap_Estate
        area_name = "Estate"
        # To start again from the habitat base map, manually unselect all the score fields (Properties, Fields)
        # then export to base map called Estate_habitats or similar
        Base_map = "Estate_habitats"
    hab_field = "Interpreted_habitat"
    Matrix = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb\Matrix.dbf"
    ALC_multipliers = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb\ALC_multipliers.dbf"
    nature_fields = "!SAC! + !RSPB! + !SSSI! + !NNR! + !LNR! + !LWS! + !Prop_LWS! + !AncientWood! + !RdVergeNR!"
    culture_fields = "!LGS! + !MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    education_fields = nature_fields + " + !LGS! +  !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
    all_des_fields = ["SAC", "RSPB", "SSSI", "NNR", "LNR", "LWS", "Prop_LWS", "AncientWood", "RdVergeNR",
                      "LGS", "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]

elif region == "Arc" or (region == "Oxon" and method == "LCM_PHI"):
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    arcpy.env.workspace = folder
    # LAD gdbs
    if region == "Arc":
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
    hab_field = "Interpreted_habitat"
    del_fields = ["OBJECTID_1", "FID_ALC_di", "Shape_Leng", "ORIG_FID", "Base_Area", "Base_Relationship", "ORIG_FID_1", "Desig_OBJID",
                  "Desig_Area", "Base_Relationship_1", "Desig_OBJID_1", "BaseID_GS", "FID_Natural_features", "FID_Public_access_erase_sp",
                  "ORIG_FID_12"]
    Matrix = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc\Data\Matrix.gdb\Matrix"
    ALC_multipliers = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc\Data\Matrix.gdb\ALC_multipliers"
    Base_map = "OSMM_LCM_PHI_ALC_Desig_GS_access"
    nature_fields = "!SAC! + !SPA! + !Ramsar! + !IBA! + !RSPB! + !SSSI! + !NNR! + !LNR! + !AncientWood!"
    culture_fields = "!MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    education_fields = nature_fields + " + !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"

historic_data = True
# Temporary fix because the extra historical designations have been added manually to Blenheim, so the other designations for these rows
# can be nulls
if region == "Blenheim":
    null_to_zero = True
else:
    null_to_zero = False

# Multiplier for aesthetic value if area is in an AONB
AONB_multiplier = 1.1
Max_des_mult = 1.2
Max_food_mult = 3.03

# Which stages of the script do we want to run? (Useful for debugging or for updating only certain scores)
tidy_fields = False
fix_CROME_and_grazing_marsh = True  # Temporary fix
join_tables = True
food_scores = True
aesthetic_scores = True
other_cultural = True
public_access_multiplier = True
calc_averages = True
calc_max = True


for gdb in gdbs:
    arcpy.env.workspace = gdb
    numrows = arcpy.GetCount_management(os.path.join(gdb, Base_map))
    print (''.join(["### Started processing ", gdb, " on ", time.ctime(), ": ", str(numrows), " rows"]))
    if region == "Arc" or (region == "Oxon" and method == "LCM_PHI"):
        path, file = os.path.split(gdb)
        area_name = file[:-4]
        # Tidy up surplus fields in input table
        if tidy_fields:
            arcpy.DeleteField_management(Base_map, del_fields)

    print ("Area is " + area_name)
    NatCap_scores = "NatCap_" + area_name

    # # This block of code is for debugging - re-starting part way through the loop through LADs, to avoid duplicating what is already done...
    # if area_name == "AylesburyVale":
    #     join_tables = False
    #     food_scores = False
    #     aesthetic_scores = False
    #     aesthetic_scores = False
    #     other_cultural = False
    #     public_access_multiplier = False
    #     calc_averages = False
    #     calc_max = True
    # else:
    #     join_tables = True
    #     food_scores = True
    #     aesthetic_scores = True
    #     aesthetic_scores = True
    #     other_cultural = True
    #     public_access_multiplier = True
    #     calc_averages = False
    #     calc_max = True

    # Temp fix to correct missing CROME data for Arc and then correct flood plain grazing marsh: only set it to Marshy Grassland
    # if it is grassland, not arable, scrub, etc
    if fix_CROME_and_grazing_marsh:
        out_map = Base_map
        # *** Katherine please check file paths ***
        data_gdb = os.path.join(folder, "Data\Data.gdb")
        CROME_data = os.path.join(data_gdb, "CROME_Arc_dissolve")

        # Add in a unique ID for each polygon in the main table, to use for joining later
        print("      Adding CROME data back in. Copying OBJECTID for base map")
        MyFunctions.check_and_add_field(out_map, "BaseID_CROME", "LONG", 0)
        arcpy.CalculateField_management(out_map, "BaseID_CROME", "!OBJECTID!", "PYTHON_9.3")

        # Select agricultural habitats as these are the ones for which we are interested in CROME
        # Don't include arable field margins as they are probably accurately mapped
        # Also don't include ''Natural surface' as this is mainly road verges and amenity grass in urban areas
        print ("Identifying farmland")
        arcpy.MakeFeatureLayer_management(out_map, "ag_lyr")
        expression = hab_field + " IN ('Agricultural land', 'Cultivated/disturbed land', 'Arable', 'Arable and scattered trees'," \
                                 " 'Marshy grassland') OR (" + hab_field + " LIKE 'Improved grassland%')"
        arcpy.SelectLayerByAttribute_management("ag_lyr", where_clause=expression)
        # Calculating percentage of farmland features within CROME polygons. This only intersects the selected (agricultural) polygons
        print("Tabulating intersections")
        # *** Katherine - this is the other way round to your expression but I think this is the correct way?
        # Please check that the case of 'lucode' matches your version of the input CROME data.
        arcpy.TabulateIntersection_analysis("ag_lyr", ["OBJECTID", hab_field, "BaseID_CROME", "Shape_Area"],
                                            CROME_data, "CROME_TI", ["lucode", "Land_Use_Description", "field", "Shape_Area"])

        # Sorting TI table by size so that larger intersections are first in the list
        print("Sorting table with largest intersections first")
        arcpy.Sort_management("CROME_TI", "CROME_TI_sort", [["AREA", "DESCENDING"]])
        # Delete all but the largest intersection. We need to do this, otherwise the join later is not robust - the wrong rows can be
        # copied across even if we think we have selected and joined to the right rows.
        print("Deleting identical (smaller intersection) rows")
        # *** Katherine  - please check that 'OBJECTID_1' is correct. If there are other OBJECTID fields in your datasets that have not yet
        # been 'tiedied up' then this will need to be changed. Check the field aliases not just the apparent field names.
        arcpy.DeleteIdentical_management("CROME_TI_sort", ["OBJECTID_1"])
        arcpy.MakeTableView_management("CROME_TI_sort", "CROME_lyr")
        # Adding fields for CROME data
        MyFunctions.check_and_add_field(out_map, "CROME_desc", "TEXT", 50)
        MyFunctions.check_and_add_field(out_map, "CROME_simple", "TEXT", 30)
        # Join the intersected table to join in the largest intersection to each polygon
        print ("Joining CROME info for base map polygons")
        arcpy.AddJoin_management("ag_lyr", "BaseID_CROME", "CROME_lyr", "BaseID_CROME", "KEEP_ALL")
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
        print ("Fixing grazing marsh")
        expression = "Interpreted_habitat ='Marshy grassland' AND PHI = 'Coastal and floodplain grazing marsh' AND CROME_desc <> 'Grass'"
        MyFunctions.select_and_copy(Base_map, "Interpreted_habitat", expression, "!OSMM_hab!")
        print ("Interpreting CROME")
        # If CROME says grass and interpretation is currently arable, change it. But most 'fallow' land looks more like arable than grass
        # in Google earth, so set that to arable as well (even though CROME simple description is grass).
        expression = "CROME_desc = 'Grass' AND " \
                     + hab_field + " IN ('Agricultural land', 'Arable', 'Cultivated/disturbed land', 'Natural surface')"
        MyFunctions.select_and_copy(out_map, hab_field, expression, "'Improved grassland'")
        # If CROME says arable and habitat is improved grassland or general agricultural, change. But don't change improved grassland
        # with scattered scrub, as inspection shows that is mainly small non-farmed areas that do not fit the CROME hexagons well.
        expression = "CROME_simple IN ('Cereal Crops', 'Leguminous Crops', 'Fallow') AND " + hab_field + \
                     " IN ('Agricultural land', 'Cultivated/disturbed land', 'Improved grassland', 'Natural surface')"
        MyFunctions.select_and_copy(out_map, hab_field, expression, "'Arable'")

        Base_map = out_map
        print ("Finished fixing CROME and grazing marsh")

    # Join base map to scores
    # -----------------------
    if join_tables:
        # Join table to matrix of scores
        print("Joining matrix")
        arcpy.MakeFeatureLayer_management(Base_map, "join_layer")
        arcpy.AddJoin_management("join_layer", hab_field, Matrix, "Habitat")

        # Join table to ALC multipliers
        print("Joining ALC multipliers")
        arcpy.AddJoin_management("join_layer", "ALC_grade", ALC_multipliers, "ALC_grade")

        # Export to new table
        print ("Creating output dataset " + NatCap_scores)
        arcpy.CopyFeatures_management("join_layer", NatCap_scores)
        arcpy.Delete_management("join_layer")

        # If no historic data, add a dummy field for the Scheduled Monument flag which is expected for the
        # cultural multipliers. Should probably delete this later as well.
        if historic_data == False:
            MyFunctions.check_and_add_field(NatCap_scores,"SchMon","Short", 0)
            arcpy.CalculateField_management(NatCap_scores,"SchMon",0,"Python_9.3")

    # Food: apply ALC multiplier
    # --------------------------
    if food_scores:
        # Add new field and copy over basic food score (this is the default for habitats not used for intensive food production)
        print("Setting up food multiplier field")
        MyFunctions.check_and_add_field(NatCap_scores,"FoodxALC", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores,"FoodxALC","!Food!", "PYTHON_9.3")

        # Select intensive food production habitats and multiply food score by ALC multiplier (ignore 'Arable field margins')
        print("Multiplying by ALC multiplier")
        expression = "(" + hab_field + " = 'Arable' OR " + hab_field + " LIKE 'Arable and%' " \
                     "OR " + hab_field + " LIKE 'Cultivated%' OR " + hab_field + " LIKE 'Improved grass%' " \
                     "OR " + hab_field + " LIKE 'Agric%' OR " + hab_field + " ='Orchard') AND ALC_mult IS NOT NULL"
        arcpy.MakeFeatureLayer_management(NatCap_scores, "Intensive_farmland")
        arcpy.SelectLayerByAttribute_management("Intensive_farmland", where_clause=expression)
        arcpy.CalculateField_management("Intensive_farmland", "FoodxALC", "!Food! * !ALC_mult!", "PYTHON_9.3")
        arcpy.Delete_management("Intensive_farmland")

        # Add new field and calculate normalised food score
        print("Calculating normalised food score")
        MyFunctions.check_and_add_field(NatCap_scores,"Food_ALC_norm","Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Food_ALC_norm", "!FoodxALC!  / " + str(Max_food_mult), "PYTHON_9.3")

    # Aesthetic value: apply AONB multiplier
    #--------------------------------------
    if aesthetic_scores:
        # Add new field and populate with aesthetic value score (default for habitats not in AONB)
        print("Setting up new field for adjusted aesthetic value")
        MyFunctions.check_and_add_field(NatCap_scores, "Aesthetic_AONB", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Aesthetic_AONB", "!Aesthetic!", "PYTHON_9.3")

        # Select AONB areas and multiply aesthetic value score by AONB multiplier
        print("Multiplying by AONB multiplier")
        arcpy.MakeFeatureLayer_management(NatCap_scores, "AONB_layer")
        arcpy.SelectLayerByAttribute_management("AONB_layer", where_clause = "AONB = 1")
        arcpy.CalculateField_management("AONB_layer","Aesthetic_AONB", "!Aesthetic! * " + str(AONB_multiplier), "PYTHON_9.3")
        arcpy.Delete_management("AONB_layer")

        # Add new field and calculate normalised aesthetic value score
        print("Calculating normalised aesthetic score")
        MyFunctions.check_and_add_field(NatCap_scores, "Aesthetic_norm", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Aesthetic_norm", "!Aesthetic_AONB! / " + str(AONB_multiplier), "PYTHON_9.3")

    # Education, Interaction with Nature and Sense of Place: apply multiplier based on number of designations
    # -------------------------------------------------------------------------------------------------------
    if other_cultural:
        # Add new fields and populate with number of nature and cultural designations
        # Replace null values with zeros
        if null_to_zero:
            print ("Replacing nulls with zeros in designation indices, before adding")
            for des_field in all_des_fields:
                MyFunctions.select_and_copy(NatCap_scores, des_field, des_field + " IS NULL", 0)
        print("Adding nature, cultural and education designation fields")
        MyFunctions.check_and_add_field(NatCap_scores, "NatureDesig", "SHORT", 0)
        arcpy.CalculateField_management(NatCap_scores, "NatureDesig", nature_fields, "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "CultureDesig", "SHORT", 0)
        arcpy.CalculateField_management(NatCap_scores, "CultureDesig", culture_fields, "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "EdDesig", "SHORT", 0)
        arcpy.CalculateField_management(NatCap_scores, "EdDesig", education_fields, "PYTHON_9.3")

        # Add new fields and populate with adjusted scores
        print("Setting up new fields for adjusted education, interaction with nature and sense of place values")
        MyFunctions.check_and_add_field(NatCap_scores, "Education_desig", "Float", 0)
        MyFunctions.check_and_add_field(NatCap_scores, "Nature_desig", "Float", 0)
        MyFunctions.check_and_add_field(NatCap_scores, "Sense_desig", "Float", 0)

        codeblock = """
def DesMult(NatureDesig, CultureDesig, EdDesig, ScheduledMonument, Habitat, GreenSpace, Score, Service):
    # GreenSpace currently not used (see notes for reasons) but could be in future
    if Service == "SensePlace":
        if NatureDesig is None or NatureDesig == 0:
            if CultureDesig is None or CultureDesig == 0:
                NumDesig = 0
            else:
                NumDesig = CultureDesig
        elif CultureDesig is None or CultureDesig == 0:
            NumDesig = NatureDesig
        else:
            NumDesig = NatureDesig + CultureDesig
    elif Service == "Nature":
        NumDesig = NatureDesig
    elif Service == "Education":
        NumDesig = EdDesig
    else:
        return Score

    if NumDesig is None or NumDesig == 0:
        NewScore = Score / 1.2
    elif NumDesig == 1:
        NewScore = 1.1 * Score / 1.2
    elif NumDesig == 2:
        NewScore = 1.15 * Score / 1.2
    elif NumDesig >=3:
        NewScore = 1.2 * Score / 1.2
    else:
        NewScore = Score

    # Minimum score of 7/10 for scheduled monuments unless arable (min score 3) or sealed surface (Score =0)
    if Service == "SensePlace" or Service == "Education":
        if ScheduledMonument == 1 and Score > 0:
            if Habitat == "Arable":
                if NewScore <3:
                    NewScore = 3
            elif NewScore <7:
                NewScore = 7
 
    return NewScore
"""
        print("Calculating education field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !Education!, ' \
                     '"Education" )'
        arcpy.CalculateField_management(NatCap_scores, "Education_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating nature field")
        expression = 'DesMult( !NatureDesig! , !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !Nature!, "Nature" )'
        arcpy.CalculateField_management(NatCap_scores,"Nature_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating sense of place field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !SchMon!, !Interpreted_habitat!, !GreenSpace!, !SensePlace!, ' \
                     '"SensePlace")'
        arcpy.CalculateField_management(NatCap_scores, "Sense_desig", expression, "PYTHON_9.3", codeblock)

    if public_access_multiplier:
        # Add field and multiply by access indicator
        print ("Calculating recreation field with public access multiplier")
        MyFunctions.check_and_add_field(NatCap_scores, "Rec_access", "FLOAT", 0)
        arcpy.CalculateField_management(NatCap_scores, "Rec_access", "!Recreation! * !AccessMult!", "PYTHON_9.3")
        # Set all habitats within path buffers to an absolute score of 7.5 out of 10 (unless sealed surface)
        MyFunctions.select_and_copy(NatCap_scores, "Rec_access", "AccessType = 'Path' AND Recreation > 0", 7.5)
        # Replace null values with zeros (needed later for calculating scenario impact)
        MyFunctions.select_and_copy(NatCap_scores, "Rec_access", "Rec_access IS NULL", 0)

    if calc_averages:
        print("Calculating averages")
        MyFunctions.check_and_add_field(NatCap_scores, "AvSoilWatReg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvSoilWatReg",
                                        '(!Flood! + !Erosion! + !WaterQual!)/3', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvCAQCoolNs", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvCAQCoolNs",
                                        '(!Carbon! + !AirQuality! + !Cooling! + !Noise!)/4', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av7Reg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av7Reg",
                                        '((!AvSoilWatReg! * 3) + (!AvCAQCoolNs! * 4))/7', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvPollPest", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvPollPest",
                                        '(!Pollination! + !PestControl!)/2', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av9Reg", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av9Reg",
                                        '((!Av7Reg! * 7) + (!AvPollPest! * 2))/ 9', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "AvCultNoRec", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "AvCultNoRec",
                                        '(!Aesthetic_norm! + !Education_desig! + !Nature_desig! + !Sense_desig!)/4', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av5Cult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av5Cult", '(!Rec_access! + (!AvCultNoRec! * 4))/5', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av14RegCult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av14RegCult",
                                        '((!Av9Reg! * 9) + (!Av5Cult!) * 5)/14', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "Av15WSRegCult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "Av15WSRegCult",
                                        '((!Av14RegCult! * 14)+ !WaterProv!)/15', "PYTHON_9.3")

    if calc_max:
        print("Calculating maximum scores")
        MyFunctions.check_and_add_field(NatCap_scores, "MaxRegCult", "FLOAT", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxRegCult",
                                        'max(!Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                        '!Pollination!, !PestControl!, !Aesthetic_norm!, !Education_desig!, !Nature_desig!,'
                                        ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "MaxWSRegCult", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxWSRegCult",
                                        'max(!WaterProv!, !Flood!, !Erosion!, !WaterQual!, !Carbon!, !AirQuality!, !Cooling!, !Noise!, '
                                        '!Pollination!, !PestControl!, !Aesthetic_norm!, !Education_desig!, !Nature_desig!,'
                                        ' !Sense_desig!, !Rec_access!)', "PYTHON_9.3")
        # MaxRegCultFood is the max of all regulating and cultural services or food production
        MyFunctions.check_and_add_field(NatCap_scores, "MaxRegCultFood", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxRegCultFood", 'max(!Food_ALC_norm!, !MaxRegCult!)', "PYTHON_9.3")
        MyFunctions.check_and_add_field(NatCap_scores, "MaxWSRegCultFood", "Float", 0)
        arcpy.CalculateField_management(NatCap_scores, "MaxWSRegCultFood", 'max(!WaterProv!, !MaxRegCultFood!)', "PYTHON_9.3")

    print("## Completed " + gdb + " on " +  time.ctime())

exit()
