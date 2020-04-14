#
# Updates natural capital scores for a pre-existing natural capital map by re-calculating average
# and maximum scores
#----------------------------------------------------------------------------------------------

import time, arcpy, os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files
arcpy.env.qualifiedFieldNames = False

gdbs = [r"D:\cenv0389\Blenheim\Blenheim.gdb"]
hab_field = "Interpreted_habitat"

# Matrix = "Matrix.dbf"
# ALC_multipliers = "ALC_multipliers.dbf"
Base_map = "NatCap_Estate"
nature_fields = "!SAC! + !RSPB! + !SSSI! + !NNR! + !LNR! + !LWS! + !Prop_LWS! + !AncientWood! + !RdVergeNR!"
culture_fields = "!LGS! + !MillenGn! + !DoorstepGn! + !NT! + !CountryPk! + !GreenBelt! + !AONB!"
education_fields = nature_fields + "!LGS! +  !CountryPk! + !NT!"

# Multiplier for aesthetic value if area is in an AONB
AONB_multiplier = 1.1
# Normalisation values (max possible scores for designations and food)
Max_des_mult = 1.2
Max_food_mult = 3.03

# Which stages of the script do we want to run? (Useful for debugging or for updating only certain scores)
food_scores = False
aesthetic_scores = False
other_cultural = False
public_access_multiplier = True
calc_averages = True
calc_max = True

for gdb in gdbs:
    arcpy.env.workspace = gdb
    numrows = arcpy.GetCount_management(os.path.join(gdb, Base_map))
    print (''.join(["### Started processing ", gdb, " on ", time.ctime(), ": ", str(numrows), " rows"]))

    NatCap_scores = Base_map

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
        arcpy.CalculateField_management(NatCap_scores,"Aesthetic_AONB", "!Aesthetic!", "PYTHON_9.3")

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
def DesMult(NatureDesig, CultureDesig, EdDesig, GreenSpace, Score, Service):
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
        return Score / 1.2
    elif NumDesig == 1:
        return 1.1 * Score / 1.2
    elif NumDesig == 2:
        return 1.15 * Score / 1.2
    elif NumDesig >=3:
        return 1.2 * Score / 1.2
    else:
        return Score
"""
        print("Calculating education field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !GreenSpace!, !Education!, "Education" )'
        arcpy.CalculateField_management(NatCap_scores, "Education_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating nature field")
        expression = 'DesMult( !NatureDesig! , !CultureDesig!, !EdDesig!, !GreenSpace!, !Nature!, "Nature" )'
        arcpy.CalculateField_management(NatCap_scores,"Nature_desig", expression, "PYTHON_9.3", codeblock)
        print("Calculating sense of place field")
        expression = 'DesMult(!NatureDesig!, !CultureDesig!, !EdDesig!, !GreenSpace!, !SensePlace!, "SensePlace")'
        arcpy.CalculateField_management(NatCap_scores, "Sense_desig", expression, "PYTHON_9.3", codeblock)

    if public_access_multiplier:
        # Add field and multiply by access indicator
        print ("Calculating recreation field with public access multiplier")
        MyFunctions.check_and_add_field(NatCap_scores, "Rec_access", "FLOAT", 0)
        arcpy.CalculateField_management(NatCap_scores, "Rec_access", "!Recreation! * !AccessMult!", "PYTHON_9.3")
        # Set all habitats within path buffers to a score of 7.5 out of 10 (unless sealed surface)
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

    print("## Completed " + gdb + " on " +  time.ctime())

exit()
