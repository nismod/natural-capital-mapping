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
# region = "Oxon"
# region = "Blenheim"
region = "NP"
# Choice of method that has been used to generate the input files - this determines location and names of input files
method = "CROME_PHI"
# method = "LERC"
# method = "HLU"

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
        Base_map = "Estate_habitats_Zones_Tenancies_Paths"
    hab_field = "Interpreted_habitat"
    Matrix = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb\Matrix.dbf"
    ALC_multipliers = r"D:\cenv0389\Oxon_GIS\Oxon_county\NaturalCapital\Oxon_full.gdb\ALC_multipliers.dbf"
    nature_fields = "!SAC! + !RSPB! + !SSSI! + !NNR! + !LNR! + !LWS! + !Prop_LWS! + !AncientWood! + !RdVergeNR!"
    culture_fields = "!LGS! + !MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    education_fields = nature_fields + " + !LGS! +  !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
    all_des_fields = ["SAC", "RSPB", "SSSI", "NNR", "LNR", "LWS", "Prop_LWS", "AncientWood", "RdVergeNR",
                      "LGS", "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]

elif region == "Arc" or region == "NP" or (region == "Oxon" and method == "CROME_PHI"):
    if method == "LERC":
        folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_PaidData"
        Base_map = "LERC_ALC_Desig_GS_PA"
        # del_fields = ["FeatureCode", "Version", "VersionDate", "CalculatedAreaValue", "PhysicalLevel"]
        del_fields = ["OBJECTID", "OBJECTID_12", "Shape_Length_1", "OBJECTID_12_13", "toid_1"]
    elif method == "CROME_PHI":
        if region == "Arc" or region == "Oxon":
            folder = r"D:\cenv0389\OxCamArc\NatCap_Arc_FreeData"
            del_fields = ["OBJECTID_1", "FID_ALC_di", "Shape_Leng", "ORIG_FID", "Base_Area", "Base_Relationship", "ORIG_FID_1",
                          "Desig_OBJID","Desig_Area", "Base_Relationship_1", "Desig_OBJID_1", "BaseID_GS", "FID_Natural_features",
                          "FID_Public_access_erase_sp", "ORIG_FID_12"]
        elif region == "NP":
            folder = r"M:\urban_development_natural_capital"
            del_fields = ["OBJECTID_1", "FID_ALC_di", "Shape_Leng", "ORIG_FID", "Base_Area", "Base_Relationship", "ORIG_FID_1",
                          "Desig_OBJID","Desig_Area", "Base_Relationship_1", "Desig_OBJID_1", "BaseID_GS", "FID_Natural_features",
                          "FID_Public_access_erase_sp", "ORIG_FID_12"]
        Base_map = "OSMM_CR_PHI_ALC_Desig_GS_PA"

    arcpy.env.workspace = folder
    # LAD gdbs
    if region == "Arc":
        gdbs = []
        gdbs = arcpy.ListWorkspaces("*", "FileGDB")
        # Or comment out previous line and use this format (one row per gdb) if repeating certain gdbs only
        # gdbs.append(os.path.join(folder, "SouthCambridgeshire.gdb"))
        # gdbs.append(os.path.join(folder, "SouthNorthamptonshire.gdb"))
    elif region == "NP":
        # done "Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
        #                 "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
        #                 "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb",
        #        "Copeland.gdb", "County Durham.gdb", "Craven.gdb", "Darlington.gdb", "Doncaster.gdb",
        #                 "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
        #                 "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb",
        #                 "Knowsley.gdb",
        #                 "Lancaster.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
        #                 "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
        #                 "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
        #                 "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb",   "Ryedale.gdb", "Salford.gdb",
        #                 "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb",
        # "South Lakeland.gdb", "South Ribble.gdb",
        # "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
        # "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb",
        # "Wigan.gdb", "Wirral.gdb", "Wyre.gdb", "York.gdb"
        LADs = [ "Leeds.gdb" ]
        gdbs = []
        for gdb_name in LADs:
            gdbs.append(os.path.join(r"M:\urban_development_natural_capital\LADs", gdb_name.replace(" ", "")))
        Matrix = r"M:\urban_development_natural_capital\Data.gdb\Matrix"

    elif region == "Oxon":
        gdbs = []
        LADs = ["Cherwell.gdb", "Oxford.gdb", "SouthOxfordshire.gdb", "ValeofWhiteHorse.gdb", "WestOxfordshire.gdb"]
        for LAD in LADs:
            gdbs.append(os.path.join(folder, LAD))
        Matrix = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Matrix.gdb\Matrix"
    hab_field = "Interpreted_habitat"

    ALC_multipliers = r"D:\cenv0389\Oxon_GIS\OxCamArc\Data\Matrix.gdb\ALC_multipliers"
    nature_fields = "!SAC! + !SPA! + !Ramsar! + !IBA! + !RSPB! + !SSSI! + !NNR! + !LNR! + !AncientWood!"
    culture_fields = "!MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB! + !SchMon! + !WHS! + !HistPkGdn!"
    education_fields = nature_fields + " + !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
    all_des_fields = ["SAC", "SPA", "Ramsar", "IBA", "RSPB", "SSSI", "NNR", "LNR", "AncientWood",
                      "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn"]
    if region == "NP":
        nature_fields = nature_fields + " + !PropRamsar! "
        culture_fields = culture_fields + " + !ConservationArea! + !HeritageCoast! "
        education_fields = nature_fields + " + !CountryPk! + !NT! + !SchMon! + !WHS! + !HistPkGdn!"
        all_des_fields = ["SAC", "SPA", "Ramsar", "PropRamsar", "IBA", "RSPB", "SSSI", "NNR", "LNR", "AncientWood",
                          "MillenGn", "DoorstepGn", "NT", "CountryPk", "GreenBelt", "AONB", "SchMon", "WHS", "HistPkGdn",
                          "ConservationArea", "HeritageCoast"]

historic_data = True
null_to_zero = False    # Only needed if any rows containing designations have some NULL values - should not happen normally
# Special case: set to true for Arc LERC data because LWS is coded as a separate field
if method == "LERC":
    LERC_LWS = True
else:
    LERC_LWS = False

# Multiplier for aesthetic value if area is in an AONB
AONB_multiplier = 1.1
Max_des_mult = 1.2
Max_food_mult = 2.4

# Which stages of the script do we want to run? (Useful for debugging or for updating only certain scores)
tidy_fields = False
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
    if region == "Arc" or region == "NP" or (region == "Oxon" and method == "CROME_PHI"):
        path, file = os.path.split(gdb)
        area_name = file[:-4]
        # Tidy up surplus fields in input table
        if tidy_fields:
            print("Deleting surplus fields ")
            arcpy.DeleteField_management(Base_map, del_fields)

    print ("Area is " + area_name)
    NatCap_scores = "NatCap_" + area_name.replace("-", "")

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
        # Replace null values with zeros - not usually needed as all rows containing designations should not contain nulls
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

        # Special case for LERC LWS - add extra designation if proportion of polygon overlapping LWS site is >0.5
        if LERC_LWS:
            print("Setting up LWS designation score for LERC data")
            MyFunctions.select_and_copy(NatCap_scores, "NatureDesig", "NatureDesig IS NULL", 0)
            MyFunctions.select_and_copy(NatCap_scores, "EdDesig", "EdDesig IS NULL", 0)
            MyFunctions.select_and_copy(NatCap_scores, "NatureDesig","LWS_p >= 0.5", "!NatureDesig! + 1")
            MyFunctions.select_and_copy(NatCap_scores, "EdDesig","LWS_p >= 0.5", "!EdDesig! + 1")

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
