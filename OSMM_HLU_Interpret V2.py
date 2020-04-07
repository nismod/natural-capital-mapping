# INTERPRETING HABITAT TYPE
# -----------------------------------
# Code by Martin Besnier and Alison Smith (Environmental Change Institute, University of Oxford)
# This code is a research tool and has not been rigorously tested for wider use.
# ------------------------------------------------------------------------------
# Processes a merged OSMM and habitat file (OR just OSMM) to assign the correct habitat type
#
# Expects input file to have the following fields:
# - DescriptiveGroup, DescriptiveTerm, Make
# - Phase 1 habitat and BAP habitat (field names specified as input parameters)
# -----------------------------------------------------------------------------------------------

import time, arcpy
import os
import MyFunctions

print(''.join(["## Started on : ", time.ctime()]))

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True  # Overwrites files

# *** Enter parameters here
# -------------------------
# region = "Arc"
region = "Oxon"
# region = "Blenheim"

# method = "LCM_PHI"
method = "HLU"

if region == "Blenheim" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"D:\cenv0389\Blenheim"
    gdbs = [os.path.join(folder, "Blenheim.gdb")]
    in_file_name = "Estate_NatCap"
    Hab_field = "PHASE1HAB"
    BAP_field = "S41HABITAT"
    # Which stages of the code do we want to run? Useful for debugging or updating.
    simplify_OSMM = True
    simplify_HLU = False
    select_HLU_or_OSMM = True
    interpret_BAP = True
elif region == "Oxon" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data"
    gdbs = [os.path.join(folder, "Merge_OSMM_HLU_ALC.gdb")]
 #   LAD_table = os.path.join(folder, "Data.gdb", "Oxon_LADs")
    in_file_name = "OSMM_HLU_CROME"
    Hab_field = "PHASE1HAB"
    BAP_field = "S41HABITAT"
    # Which stages of the code do we want to run? Useful for debugging or updating.
    simplify_OSMM = True
    simplify_HLU = False
    select_HLU_or_OSMM = True
    interpret_BAP = True

elif method == "LCM_PHI":
    folder = r"C:\Users\cenv0389\Documents\Oxon_GIS\OxCamArc"
    arcpy.env.workspace = folder
    gdbs = arcpy.ListWorkspaces("*", "FileGDB")
    LAD_table = os.path.join(folder, "Data\Data.gdb", "Arc_LADs")
    in_file_name = "OSMM"   # Legacy issue - Arc LAD gdbs currently only have OSMM_LCM. Need to recreate OSMM only files.
    Hab_field = "Interpreted_Habitat"
    if region == "Arc":
        LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire"]
    elif region == "Oxon":
        LADs_included = ["Oxfordshire"]
    else:
        print("ERROR: Invalid region")
        exit()
    # We only want to run simplify_OSMM.
    simplify_OSMM = True
    simplify_HLU = False
    select_HLU_or_OSMM = False
    interpret_BAP = False

else:
    print("ERROR: you cannot combine region " + region + " with method " + method)
    exit()

# If OSMM is "undefined" this usually means the area is under development or scheduled for development. Choose whether to map as
# "undefined" or as the current / original habitat pre-development
undefined_or_original = "original"

# Check the county from the table of LADs, to identify the list of LADs to process
LADs = []
if region == "Oxon":
    LADs = ["Oxfordshire"]
elif region == "Arc":
    for LAD in arcpy.SearchCursor(LAD_table):
        if LAD.getValue("county") in LADs_included:
            LADs.append(LAD.getValue("desc_").replace(" ", ""))
elif region == "Blenheim":
    LADs = ["Blenheim"]

print("LADs to process: " + "\n ".join(LADs))

for gdb in gdbs:
#    if (os.path.split(gdb)[1])[:-4] in LADs:
        arcpy.env.workspace = gdb
        print(''.join(["## Started interpreting habitats for ", gdb, " ", in_file_name, " on : ", time.ctime()]))
        in_file = os.path.join(folder, gdb, in_file_name)
    
        # Simplify the OSMM habitats
        # --------------------------
        if simplify_OSMM:
            print("Simplifying OSMM habitats")
            MyFunctions.check_and_add_field(in_file, "OSMM_hab", "TEXT", 100)
    
            codeblock = """
def Simplify_OSMM(OSMM_Group, OSMM_Term, OSMM_Make):

    if OSMM_Make == "Manmade":
        if OSMM_Group[:8] == "Building" or OSMM_Group == "Glasshouse":
            return "Building"
        elif OSMM_Group[:4] == "Rail" and (OSMM_Term is None or OSMM_Term == ""):
            return "Rail"
        elif OSMM_Group == "Road Or Track":
            if OSMM_Term is None:
               return "Road"
            elif OSMM_Term in ["Track","Traffic Calming"]:
               return "Road"
        elif "Path" in OSMM_Group:
            return "Path - manmade"
        elif OSMM_Term is None or OSMM_Term == "":
            if OSMM_Group == "Roadside":
                return "Roadside - manmade"
            else:
                return "Sealed surface"
        elif OSMM_Term == "Electricity Sub Station":
            return "Building"
        elif "bridge" in OSMM_Term.lower():   #Bridge or footbridge
            return "Bridge"
        elif OSMM_Term in ["Swimming Pool","Fountain","Weir"]:
            return OSMM_Term.capitalize()
        elif OSMM_Term in ["Mill Leat","Mine Leat","Lock","Conduit"]:
            return "Canal"
        elif "Landfill" in OSMM_Term:
            return "Landfill"
        elif  "Mineral Workings" in OSMM_Term or "Spoil" in OSMM_Term or "Slag" in OSMM_Term:
            return "Quarry or spoil"
        else:
            return "Sealed surface"

    elif OSMM_Make == "Multiple":
        return "Garden"

    elif OSMM_Make == "Natural":

        if OSMM_Term is None or OSMM_Term == "":     # Need this test before we start comparing OSMM_Term, otherwise it crashes
            if "Roadside" in OSMM_Group:
                return "Road island / verge"
            elif "water" in OSMM_Group.lower():
                return "Water"
            else:
                return "Natural surface"
            
        elif "water" in OSMM_Group.lower() or "Leat" in OSMM_Term:
            if OSMM_Term in ["Canal","Canal Feeder"]:
                return "Canal"
            elif OSMM_Term in ["Reservoir","Drain"]:
                return OSMM_Term.capitalize()
            elif OSMM_Term in ["Static Water","Collects","Mill Leat","Mine Leat"]:
                return "Standing water"
            elif OSMM_Term in ["Watercourse","Waterfall","Ford","Spring"]:
                return "Running water"
            elif "Trees" in OSMM_Term:
                return "Wet woodland"
            elif "Reeds" in OSMM_Term:
                return "Reedbed"
            else:
                return "Water"
        
        elif OSMM_Term == "Agricultural Land":
            return "Agricultural land"    # Unknown farmland

        elif OSMM_Term == "Track":
            return "Track"
        elif OSMM_Term in ["Bridge","Footbridge"]:
            return "Bridge - natural"

        elif "Trees" in OSMM_Term or "Coppice Or Osiers" in OSMM_Term:
            if "Nonconiferous" in OSMM_Term or "Coppice Or Osiers" in OSMM_Term:
                if "Coniferous" in OSMM_Term:
                    wood = "mixed"
                else:
                    wood = "broadleaved"
            else:
                wood = "coniferous"

            if "cattered" in OSMM_Term or "Grass" in OSMM_Term or "Heath" in OSMM_Term or "Marsh" in OSMM_Term:
                if "Rough Grassland" in OSMM_Term:
                    return ("Parkland and scattered trees: " + wood)
                elif "Heath" in OSMM_Term:
                    return ("Heath with scattered trees: " + wood)
                elif "Marsh" in OSMM_Term:
                    return ("Marsh with scattered trees: " + wood)
                else:
                    return ("Scattered trees: " + wood)
            else:
                return ("Woodland: " + wood)

        elif "Scrub" in OSMM_Term:
            if "cattered" in OSMM_Term or "Grass" in OSMM_Term:
                if "Rough Grassland" in OSMM_Term:
                    return ("Semi-natural grassland and scattered scrub")
                else:
                    return "Scattered scrub"
            else:
                return "Dense scrub"

        elif "Orchard" in OSMM_Term:
            return "Orchard"
        elif "Heath" in OSMM_Term:
            return "Heathland"
        elif "Marsh" in OSMM_Term:
            return "Fen, marsh and swamp"
        elif OSMM_Term == "Saltmarsh":
            return "Saltmarsh"
        elif OSMM_Term == "Mud":
            return "Mudflats"
        elif OSMM_Term == "Rock":
            return "Inland rock"
        elif "Grass" in OSMM_Term:
            return "Semi-natural grassland"
        elif  ("Mineral" in OSMM_Term or "Spoil" in OSMM_Term or "Slag" in OSMM_Term) and "Inactive" in OSMM_Term:
            return "Quarry or spoil: disused"

        else:
            return OSMM_Term.capitalize()

    else:
        if OSMM_Group == "Roadside":
            return "Roadside: unknown surface"
        else:
            return "Undefined"
"""
            arcpy.CalculateField_management(in_file, "OSMM_hab", "Simplify_OSMM(!DescriptiveGroup!, !DescriptiveTerm!, !Make!)",
                                            "PYTHON_9.3", codeblock)

        # Simplify the HLU habitats
        #--------------------------
        if simplify_HLU:
            print("Simplifying HLU habitats")
            MyFunctions.check_and_add_field(in_file, "HLU_hab", "TEXT", 100)

            codeblock = """
def Simplify_HLU(HLU_Hab):

    if HLU_Hab is None or HLU_Hab.strip() == "":
        return ""
    else:
        HLU_Hab = HLU_Hab.lower()

    # 'Cultivated/disturbed land - ' categories: simplify to just 'Arable', 'Amenity grassland' etc
    if "amenity" in HLU_Hab:
        return "Amenity grassland"
    elif "ephemeral" in HLU_Hab:
        return "Ephemeral vegetation"
    elif "arable" in HLU_Hab:
        if "scattered" in HLU_Hab and "trees" in HLU_Hab:
            return "Arable and scattered trees"
        else:
            return "Arable"

    elif "felled" in HLU_Hab and "woodland" in HLU_Hab:
        return "Felled woodland"
    elif "scrub" in HLU_Hab:
        if "scattered" in HLU_Hab:
            if "neutral grassland" in HLU_Hab:
                return "Neutral grassland and scattered scrub"
            else:
                return "Scattered scrub"
        else:
            return "Dense scrub"
    elif "herb and fern" in HLU_Hab:
        return "Tall herb and fern"
    elif "heath" in HLU_Hab:
        return "Heathland"
    elif "refuse" in HLU_Hab or "landfill" in HLU_Hab:
        return "Landfill"
    elif "spoil" in HLU_Hab or "quarry" in HLU_Hab:
        return "Quarry or spoil"
    elif "fen" in HLU_Hab:
        return "Lowland fens"
    elif "marsh" in HLU_Hab:
        return "Marshy grassland"
    elif "marginal" in HLU_Hab:
        return "Aquatic marginal vegetation"
    elif "open mosaic" in HLU_Hab:
        return "Open mosaic habitats"
    else:
        return HLU_Hab.capitalize()
"""
            arcpy.CalculateField_management(in_file, "HLU_hab", "Simplify_HLU(!" + Hab_field + "!)", "PYTHON_9.3", codeblock)

        # Choose whether to use OSMM or HLU
        # ----------------------------------
        if select_HLU_or_OSMM:
            print("Selecting or combining HLU and OSMM habitats")
            MyFunctions.check_and_add_field(in_file, "Interpreted_habitat", "TEXT", 100)

            codeblock = """
def Interpret_hab(HLU_hab, OSMM_hab, OSMM_Make, OSMM_area, HLU_area, undefined_or_original):

    if HLU_hab is None or HLU_hab.strip() == "" or HLU_hab == "Built-up areas":
        return OSMM_hab.capitalize()
    elif OSMM_hab == "Roadside: unknown surface":
        return HLU_hab.capitalize()
    elif OSMM_hab == "Undefined":
        if undefined_or_original == "undefined":
            return "Undefined"
        else:
            # Unclassified / undefined is usually sites under development, but this returns original habitat
            return HLU_hab.capitalize()
    else:
        HLU_hab = HLU_hab.lower()
        OSMM_hab = OSMM_hab.lower()

    # OSMM manmade, gardens and water always take priority over HLU
    if OSMM_Make == "Manmade" or OSMM_hab in ["garden","standing water","running water","canal","reservoir","drain","wet woodland","reedbed"]:
        return OSMM_hab.capitalize()

    # HLU takes priority over non-specific OSMM habitats 
    if OSMM_hab in ["agricultural land", "natural surface"]:
        return HLU_hab.capitalize()

    # Where HLU says grass but OSMM says trees or scrub, classify as trees / scrub encroaching onto grass
    if "trees" in OSMM_hab:
        if "mixed" in OSMM_hab:
            wood = "mixed"
        elif "broadleaved" in OSMM_hab:
            wood = "broadleaved"
        elif "coniferous" in OSMM_hab:
            wood = "coniferous"
    seminatural_grass = False
    if "acid" in HLU_hab or "neutral" in HLU_hab or "calcareous" in HLU_hab or "marsh" in HLU_hab or "poor" in HLU_hab:
        seminatural_grass = True
    if "trees" in OSMM_hab and "grassland" in HLU_hab and "scattered" not in HLU_hab:
        if "scattered" in OSMM_hab:
            if seminatural_grass:
                return ("Parkland and scattered trees: " + wood)
            else:
                return ("Scattered trees: " + wood)
        else:
            if seminatural_grass == True:
                return ("Woodland: " + wood + " on semi-natural grassland")
            else:
                return ("Woodland: " + wood)

    if "scrub" in OSMM_hab and "grassland" in HLU_hab and "scattered" not in HLU_hab:
        if "scattered" in OSMM_hab:
            if "amenity" in HLU_hab:
                return "Amenity grassland and scattered scrub"
            elif "improved" in HLU_hab and "semi" not in HLU_hab:
                return "Improved grassland and scattered scrub"
            elif seminatural_grass == True:
                return "Semi-natural grassland and scattered scrub"
        else:
            if seminatural_grass == True:
                return "Scrub on semi-natural grassland"
            else:
                return "Dense scrub"

    # Where HLU says woodland and OSMM says trees or scattered trees, use HLU definition unless HLU is unknown woodland
    if "trees" in OSMM_hab and ("woodland" in HLU_hab or "orchard" in HLU_hab):
        if "unknown" in HLU_hab:
            return OSMM_hab.capitalize()   # if unknown woodland in HLU, use OSMM definition
        else:
            return HLU_hab.capitalize()
    
    if "semi-natural grassland" in OSMM_hab and ("amenity" in HLU_hab or "arable" in HLU_hab):   # OSMM rough grass trumps arable /amenity
        return "Semi-natural grassland"

    # All other habitats (woodland, semi-nat grass, orchard, marsh, heath, etc) - both OSMM and HLU are 'distinctive' so either 
    # could be correct. Use OSMM if it is considerably smaller than HLU (an 'island' or ride within larger HLU polygon), otherwise use HLU
    if OSMM_area < HLU_area * 0.6:
        return OSMM_hab.capitalize()
    else:
        return HLU_hab.capitalize()
 """
            arcpy.CalculateField_management(in_file, "Interpreted_habitat",
                                            "Interpret_hab(!HLU_hab!, !OSMM_hab!, !Make!, !OSMM_Area!, !HLU_Area!, '" + undefined_or_original + "')",
                                            "PYTHON_9.3", codeblock)

        if interpret_BAP:
            print(''.join(["## BAP interpretation started on : ", time.ctime()]))

            codeblock = """
def interpretBAP(Hab, BAP):
    if BAP:
        BAP = BAP.lower()
        if BAP in ["none","not assessed yet",""," "]:
            return Hab
        elif Hab == "Garden":    # Gardens usually mean the original BAP has been developed, except for Trad orchards in large gardens
            if BAP == "traditional orchards":
                return BAP.capitalize()
            else:
                return Hab
        elif "possible priority grassland" in BAP:
            if Hab in ["Natural surface", "Improved grassland"]:
                return "Semi-natural grassland"
            elif Hab == "Scattered scrub":
                return "Semi-natural grassland and scattered scrub"
            elif Hab == "Dense scrub":
                return "Scrub on semi-natural grassland"
            elif Hab == "Scattered trees: broadleaved":
                return "Parkland and scattered trees: broadleaved"
            elif Hab == "Scattered trees: mixed":
                return "Parkland and scattered trees: mixed"
            elif Hab == "Scattered trees: coniferous":
                return "Parkland and scattered trees: coniferous"
            else:
                return Hab
        elif "possible priority fen" in BAP:
            if Hab == "Natural surface":
                return "Lowland fens"
            else:
                return Hab
        elif "reedbed" in BAP:
            return "Reedbed"
        elif "open mosaic habitat" in BAP:
            return "Open mosaic habitats"

        elif "purple moor grass" in BAP or "grazing marsh" in BAP:
            return "Marshy grassland"
        elif "deciduous" in BAP or "beech and yew" in BAP:
            return "Woodland: broadleaved, semi-natural"
        elif "acid grass" in BAP:
            return "Acid grassland"
        elif "meadow" in BAP:
            return "Neutral grassland"
        elif "calcareous" in BAP:
            return "Calcareous grassland"
        elif "heathland" in BAP:
            return "Heathland"
        elif "wood pasture" in BAP:
            return "Parkland and scattered trees: broadleaved"
        else:
            return BAP.capitalize()
    else:
        return Hab
"""
            arcpy.CalculateField_management(in_file, "Interpreted_habitat",
                                            "interpretBAP( !Interpreted_habitat! , !" + BAP_field + "!)", "PYTHON_9.3", codeblock)

print(''.join(["## Completed on : ", time.ctime()]))
exit()
