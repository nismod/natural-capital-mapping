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
# region = "NP"

# method = "CROME_PHI"
method = "HLU"
# method = "OSMM_only"

if region == "Oxon" and method == "HLU":
    # Operate in the Oxon_county folder
    folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data"
    gdbs = [os.path.join(folder, "Merge_OSMM_HLU_CR_ALC.gdb")]
    # LAD_table = os.path.join(folder, "Data.gdb", "Oxon_LADs")
    in_file_name = "OSMM_HLU"
    Hab_field = "Interpreted_habitat"

    # *** Late habitat corrections ***
    # in_file_name = "OSMM_HLU_CR_ALC"
    # Hab_field = "Interpreted_habitat_temp"

    in_hab_field = "PHASE1HAB"   # Zach - change
    BAP_field = "S41HABITAT"      # change
    # Which stages of the code do we want to run? Useful for debugging or updating.
    delete_landform = True
    add_OSMM_hab = True
    simplify_OSMM = True
    simplify_HLU = True
    select_HLU_or_OSMM = True
    interpret_BAP = True

elif method == "CROME_PHI":
    folder = r"D:\cenv0389\OxCamArc\LADs"
    arcpy.env.workspace = folder
    gdbs = arcpy.ListWorkspaces("*", "FileGDB")
    LAD_table = r"D:\cenv0389\OxCamArc\Arc_LADs_sort.shp"
    in_file_name = "OSMM"
    Hab_field = "Interpreted_habitat"
    if region == "Arc":
        LADs_included = ["Bedfordshire", "Buckinghamshire", "Cambridgeshire", "Northamptonshire", "Oxfordshire", "Peterborough"]
    elif region == "Oxon":
        LADs_included = ["Oxfordshire"]
    else:
        print("ERROR: Invalid region")
        exit()
    # We only want to run delete_landform and simplify_OSMM.
    delete_landform = True
    add_OSMM_hab = False
    simplify_OSMM = True
    simplify_HLU = False
    select_HLU_or_OSMM = False
    interpret_BAP = False

elif method == "OSMM_only":
    if region == "Oxon":
        folder = r"D:\cenv0389\Oxon_GIS\Oxon_county\Data"
        gdbs = ["OSMM_Aug2020.gdb"]
        in_file_name = "OSMM_Oxon_Aug2020_clip"
        Hab_field = "Interpreted_habitat"
        LADs_included = ["Oxfordshire"]
    elif region == "NP":
        folder = r"M:\urban_development_natural_capital\LADs"
        arcpy.env.workspace = folder
        LAD_names = ["Allerdale.gdb", "Barnsley.gdb", "Barrow-in-Furness.gdb", "Blackburn with Darwen.gdb", "Blackpool.gdb",
                     "Bolton.gdb", "Bradford.gdb", "Burnley.gdb", "Bury.gdb", "Calderdale.gdb", "Carlisle.gdb",
                     "Cheshire East.gdb", "Cheshire West and Chester.gdb", "Chorley.gdb", "Copeland.gdb", "County Durham.gdb",
                     "Craven.gdb", "Darlington.gdb", "Doncaster.gdb", "East Riding of Yorkshire.gdb", "Eden.gdb", "Fylde.gdb", "Gateshead.gdb",
                     "Halton.gdb", "Hambleton.gdb", "Harrogate.gdb", "Hartlepool.gdb", "Hyndburn.gdb", "Kirklees.gdb", "Knowsley.gdb",
                     "Lancaster.gdb", "Leeds.gdb", "Liverpool.gdb", "Manchester.gdb", "Middlesbrough.gdb", "Newcastle upon Tyne.gdb",
                     "North East Lincolnshire.gdb", "North Lincolnshire.gdb", "Northumberland.gdb", "North Tyneside.gdb", "Oldham.gdb",
                     "Pendle.gdb", "Preston.gdb", "Redcar and Cleveland.gdb", "Ribble Valley.gdb",
                     "Richmondshire.gdb", "Rochdale.gdb", "Rossendale.gdb", "Rotherham.gdb", "Ryedale.gdb", "Salford.gdb",
                     "Scarborough.gdb", "Sefton.gdb", "Selby.gdb", "Sheffield.gdb", "South Lakeland.gdb", "South Ribble.gdb",
                     "South Tyneside.gdb", "St Helens.gdb", "Stockport.gdb", "Stockton-on-Tees.gdb", "Sunderland.gdb",
                     "Tameside.gdb", "Trafford.gdb", "Wakefield.gdb", "Warrington.gdb", "West Lancashire.gdb", "Wigan.gdb", "Wirral.gdb",
                     "Wyre.gdb", "York.gdb"]
        # LAD_names = []
        gdbs = []
        for LAD_name in LAD_names:
            gdbs.append(os.path.join(folder, LAD_name.replace(" ", "")))
        in_file_name = "OSMM"
        # in_file_name = "OSMM_CR_PHI_ALC_Desig_GS"  # Used for late corrections
        Hab_field = "Interpreted_habitat"

    # We only want to run delete_landform and simplify_OSMM.
    # *** Change to only simplify_OSMM for late habitat corrections ***.
    delete_landform = True
    add_OSMM_hab = False
    simplify_OSMM = True
    simplify_HLU = False
    select_HLU_or_OSMM = False
    interpret_BAP = False

else:
    print("ERROR: you cannot combine region " + region + " with method " + method)
    exit()

# If OSMM is "undefined" this usually means the area is under development or scheduled for development. Choose whether to map as
# "undefined" or as the current / original habitat pre-development. Up till now including NP we have used original but in future best to
# use undefined - in fact should maybe change this for NP as well, though bit late now!!!
# undefined_or_original = "original"
undefined_or_original = "undefined"

# Check the county from the table of LADs, to identify the list of LADs to process
LADs = []
if region == "Oxon":
    LADs = ["Oxfordshire"]

elif region == "Arc":
    for LAD in arcpy.SearchCursor(LAD_table):
        if LAD.getValue("county") in LADs_included:
            LADs.append(LAD.getValue("desc_").replace(" ", ""))
    # Or use this line to update only certain LADs
    # LADs = ["AylesburyVale", "Chiltern", "Oxford", "SouthOxfordshire", "Wycombe"]
elif region == "Blenheim":
    LADs = ["Blenheim"]

elif region == "NP":
    LADs = LAD_names

if region == "NP":
    OSMM_Term = "descriptiveterm"
    OSMM_Group = "descriptivegroup"
    OSMM_Make = "make"
else:
    OSMM_Term = "DescriptiveTerm"
    OSMM_Group = "DescriptiveGroup"
    OSMM_Make = "Make"

print("LADs to process: " + "\n ".join(LADs))

i=0
for gdb in gdbs:
    if (region == "Oxon" and (method == "HLU" or method == "OSMM_only")) or (os.path.split(gdb)[1])[:-4] in LADs or region == "NP":
        i = i + 1
        print "Processing LAD " + str(i) + " out of " + str(len(LADs))
        arcpy.env.workspace = gdb
        print(''.join(["## Started interpreting habitats for ", gdb, " ", in_file_name, " on : ", time.ctime()]))
        in_file = os.path.join(folder, gdb, in_file_name)

        if delete_landform:
            print("  Deleting overlapping 'Landform' and 'Pylon' from OSMM for " + in_file_name)
            arcpy.MakeFeatureLayer_management(in_file, "OSMM_layer")
            expression = "DescriptiveGroup LIKE '%Landform%' OR DescriptiveTerm IN ('Cliff','Slope','Pylon')"
            arcpy.SelectLayerByAttribute_management("OSMM_layer", where_clause=expression)
            arcpy.DeleteFeatures_management("OSMM_layer")
            arcpy.Delete_management("OSMM_layer")
    
        # Simplify the OSMM habitats
        # --------------------------
        if simplify_OSMM:
            print("  Simplifying OSMM habitats")
            if add_OSMM_hab:
                MyFunctions.check_and_add_field(in_file, "OSMM_hab", "TEXT", 100)
    
            codeblock = """
def Simplify_OSMM(OSMM_Group, OSMM_Term, OSMM_Make):

    if OSMM_Make == "Manmade":
        if OSMM_Group[:8] == "Building" or OSMM_Group == "Glasshouse":
            return "Building"
        elif OSMM_Group[:4] == "Rail" and (OSMM_Term is None or OSMM_Term == ""):
            return "Rail"
        elif OSMM_Group == "Road Or Track":
            return "Road"
        elif "Path" in OSMM_Group:
            return "Path: manmade"
        elif OSMM_Term is None or OSMM_Term == "":
            if OSMM_Group == "Roadside":
                return "Roadside: manmade"
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
            if "Inactive" in OSMM_Term:
                return "Landfill: disused"
            else:
                return "Landfill"
        elif  "Mineral Workings" in OSMM_Term or "Spoil" in OSMM_Term or "Slag" in OSMM_Term:
            if "Inactive" in OSMM_Term:
                return "Quarry or spoil: disused"
            else:
                return "Quarry or spoil"
        else:
            return "Sealed surface"

    elif OSMM_Make == "Multiple":
        return "Garden"

    elif OSMM_Make == "Natural":

        if OSMM_Term is None or OSMM_Term == "":     # Need this test before we start comparing OSMM_Term, otherwise it crashes
            if "Roadside" in OSMM_Group:
                return "Road island / verge"
            elif "tidal water" in OSMM_Group.lower():
                return "Saltwater"
            elif "water" in OSMM_Group.lower():
                return "Water"
            else:
                return "Natural surface"
            
        elif "water" in OSMM_Group.lower() or "Leat" in OSMM_Term or OSMM_Term in ["Conduit","Spreads","Issues","Sink","Spring"]:
            if OSMM_Term in ["Canal","Canal Feeder", "Conduit"]:
                return "Canal"
            elif OSMM_Term in ["Reservoir","Drain"]:
                return OSMM_Term.capitalize()
            elif OSMM_Term in ["Static Water","Collects","Mill Leat","Mine Leat","Spreads","Sink"]:
                return "Standing water"
            elif OSMM_Term in ["Watercourse","Waterfall","Ford","Spring","Issues"]:
                return "Running water"
            elif "Trees" in OSMM_Term:
                return "Wet woodland"
            elif "Reeds" in OSMM_Term:
                return "Reedbed"
            elif "Foreshore" in OSMM_Term:
                if "Saltmarsh" in OSMM_Term:
                    return "Saltmarsh"
                elif (OSMM_Term[:4] == "Rock" or OSMM_Term[:8] == "Boulders") and "Sand" not in OSMM_Term and "Mud" not in OSMM_Term:
                    return "Coastal rock"
                elif OSMM_Term[:7] == "Shingle":
                    return "Shingle"
                elif OSMM_Term[:3] == "Mud":
                    return "Mudflats"
                else:
                    return "Intertidal sediment"
            else:
                return "Water"
        
        elif OSMM_Term == "Agricultural Land":
            return "Agricultural land"    # Unknown farmland

        elif OSMM_Term == "Track":
            return "Track"
        elif OSMM_Term in ["Bridge","Footbridge"]:
            return "Bridge: natural"
        elif OSMM_Term == "Tank":
            return "Sealed surface"

        elif "Trees" in OSMM_Term or "Coppice Or Osiers" in OSMM_Term:
            if "Nonconiferous" in OSMM_Term or "Coppice Or Osiers" in OSMM_Term:
                if "Coniferous" in OSMM_Term:
                    wood = "mixed"
                else:
                    wood = "broadleaved"
            else:
                wood = "coniferous"
            
            if (wood == "broadleaved" and "Nonconiferous Trees (Scattered)" in OSMM_Term):
                scattered_trees = True
            elif (wood == "coniferous" and "Coniferous Trees (Scattered)" in OSMM_Term):
                scattered_trees = True
            elif (wood == "mixed" and ("Nonconiferous Trees (Scattered)" in OSMM_Term and "Coniferous Trees (Scattered)" in OSMM_Term)):
                scattered_trees = True
            else:
                scattered_trees = False

            if scattered_trees == True or "Grass" in OSMM_Term or "Heath" in OSMM_Term or "Marsh" in OSMM_Term:
                if "Heath" in OSMM_Term:
                    if "Grass" in OSMM_Term:
                        return ("Heath/grass mosaic with scattered trees: " + wood)
                    else:
                        return ("Heath with scattered trees: " + wood)
                elif "Marsh" in OSMM_Term:
                    return ("Marsh with scattered trees: " + wood)
                elif "Rough Grassland" in OSMM_Term:
                    return ("Semi-natural grassland with scattered trees: " + wood)
                elif ("Scrub" in OSMM_Term and "Scrub (Scattered)" not in OSMM_Term):
                    return ("Scrub with scattered trees: " + wood)
                elif "Scree" in OSMM_Term:
                    return ("Scree with scattered trees: " + wood)
                elif ("Rock" in OSMM_Term and "Rock (Scattered)" not in OSMM_Term):
                    return ("Rock with scattered trees: " + wood)
                else:
                    return ("Scattered trees: " + wood)
            else:
                return ("Woodland: " + wood)

        elif "Scrub" in OSMM_Term:
            if "Scrub (Scattered)" in OSMM_Term or "Grass" in OSMM_Term or "Heath" in OSMM_Term or "Marsh" in OSMM_Term:
                if "Heath" in OSMM_Term:
                    if "Grass" in OSMM_Term:
                        return ("Heath/grass mosaic with scattered scrub")
                    else:
                        return ("Heath with scattered scrub")
                elif "Marsh" in OSMM_Term:
                    if OSMM_Term[:6] == "Scrub,":
                        return ("Scrub with marsh")
                    else:
                        return ("Marsh with scattered scrub")
                elif "Rough Grassland" in OSMM_Term:
                    return ("Semi-natural grassland with scattered scrub")
                elif "Scree" in OSMM_Term:
                    return ("Scree with scattered scrub")
                elif ("Rock" in OSMM_Term and "Rock (Scattered)" not in OSMM_Term):
                    return ("Rock with scattered scrub")
                else:
                    return "Scattered scrub"
            else:
                return "Dense scrub"

        elif "Orchard" in OSMM_Term:
            return "Orchard"
        elif "Heath" in OSMM_Term:
            if "Grass" in OSMM_Term:
                return "Heath/grass mosaic"
            else:
                return "Heathland"
        elif "Marsh" in OSMM_Term:
            return "Fen, marsh and swamp"
        elif OSMM_Term[:9] == "Saltmarsh":
            return "Saltmarsh"
        elif OSMM_Term[:3] == "Mud":
            return "Mudflats"
        elif OSMM_Term[:7] == "Shingle":
            return "Shingle"
        elif OSMM_Term[:4] == "Sand":
            return "Sand"
        elif "Grass" in OSMM_Term:
            return "Semi-natural grassland"
        elif  ("Mineral" in OSMM_Term or "Spoil" in OSMM_Term or "Slag" in OSMM_Term) and "Inactive" in OSMM_Term:
            return "Quarry or spoil: disused"
        elif OSMM_Term[:4] == "Rock":
            return "Rock"
        elif OSMM_Term[:5] == "Scree":
            return "Scree"
        elif OSMM_Term[:8] == "Boulders":
            return "Boulders"
        elif OSMM_Term == "Landfill (inactive)":
            return "Landfill: disused"

        else:
            return OSMM_Term.capitalize()

    else:
        if OSMM_Group == "Roadside":
            return "Roadside: unknown surface"
        else:
            return "Undefined"
"""
            expression = "Simplify_OSMM(!" + OSMM_Group + "!, !" + OSMM_Term + "!, !" + OSMM_Make + "!)"
            arcpy.CalculateField_management(in_file, "OSMM_hab", expression, "PYTHON_9.3", codeblock)

        # Simplify the HLU habitats
        #--------------------------
        if simplify_HLU:
            print("Simplifying HLU habitats")
            MyFunctions.check_and_add_field(in_file, "HLU_hab", "TEXT", 100)

            codeblock = """
def Simplify_HLU(HLU_Hab):

    if HLU_Hab is None or HLU_Hab.strip() == "" or HLU_Hab == "Unknown" or HLU_Hab == "Unidentified":
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
        if "grass" in HLU_Hab:
            return "Heath/grass mosaic"
        else:
            return "Heathland"
    elif "hedge" in HLU_Hab and "trees" in HLU_Hab:
        return "Hedge with trees"
    elif "hedge" in HLU_Hab:
        return "Hedge"
    elif "refuse" in HLU_Hab or "landfill" in HLU_Hab:
        return "Landfill"
    elif "spoil" in HLU_Hab or "quarry" in HLU_Hab:
        return "Quarry or spoil"
    elif "fen" in HLU_Hab:
        return "Lowland fens"
    elif "flush" in HLU_Hab:
        if "upland" in HLU_Hab:
            return "Upland flushes, fens and swamps"
        else:
            return "Fen, marsh and swamp"
    elif "marsh" in HLU_Hab:
        return "Marshy grassland"
    elif "marginal" in HLU_Hab:
        return "Aquatic marginal vegetation"
    elif "open mosaic" in HLU_Hab:
        return "Open mosaic habitats"
    else:
        return HLU_Hab.capitalize()
"""
            arcpy.CalculateField_management(in_file, "HLU_hab", "Simplify_HLU(!" + in_hab_field + "!)", "PYTHON_9.3", codeblock)

        # Choose whether to use OSMM or HLU
        # ----------------------------------
        if select_HLU_or_OSMM:
            print("Selecting or combining HLU and OSMM habitats")
            MyFunctions.check_and_add_field(in_file, Hab_field, "TEXT", 100)

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
                return ("Semi-natural grassland with scattered trees: " + wood)
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
                return "Semi-natural grassland with scattered scrub"
        else:
            if seminatural_grass == True:
                return "Scrub on semi-natural grassland"
            else:
                return "Dense scrub"

    # Where HLU says woodland and OSMM says trees or scattered trees, use HLU definition unless HLU is unknown woodland
    if ("woodland" in OSMM_hab or "orchard" in OSMM_hab) and ("woodland" in HLU_hab or "orchard" in HLU_hab):
        if ("unknown" in HLU_hab) or (HLU_hab == "woodland"):
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
            expression = "Interpret_hab(!HLU_hab!, !OSMM_hab!, !Make!, !OSMM_Area!, !HLU_Area!, '" + undefined_or_original + "')"
            arcpy.CalculateField_management(in_file, Hab_field, expression, "PYTHON_9.3", codeblock)

        # Update Interpreted_habitat column where appropriate using S41 Habitat information (previously known as BAP habitat)
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
            if Hab in ["Natural surface", "Improved grassland", "Agricultural land", "Unknown", "Unidentified"]:
                return "Semi-natural grassland"
            elif Hab == "Scattered scrub":
                return "Semi-natural grassland with scattered scrub"
            elif Hab == "Dense scrub":
                return "Scrub on semi-natural grassland"
            elif Hab == "Scattered trees: broadleaved":
                return "Semi-natural grassland with scattered trees: broadleaved"
            elif Hab == "Scattered trees: mixed":
                return "Semi-natural grassland with scattered trees: mixed"
            elif Hab == "Scattered trees: coniferous":
                return "Semi-natural grassland with scattered trees: coniferous"
            else:
                return Hab
        elif "possible priority fen" in BAP:
            if Hab in ["Natural surface", "Improved grassland", "Agricultural land", "Unknown", "Unidentified"]:
                return "Lowland fens"
            else:
                return Hab
        elif "reedbed" in BAP:
            return "Reedbed"
        elif "open mosaic habitat" in BAP:
            return "Open mosaic habitats"

        elif "purple moor grass" in BAP:
            return "Marshy grassland"
        elif "grazing marsh" in BAP:
            if "grass" in Hab.lower():
                return "Marshy grassland"
            else:
                return Hab
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
        elif "wood-pasture" in BAP or "wood pasture" in BAP:
            return "Parkland and scattered trees: broadleaved"
        elif "pond" in BAP or "river" in BAP or "water" in BAP or "lake" in BAP:
            return Hab
        else:
            return BAP.capitalize()
    else:
        return Hab
"""
            arcpy.CalculateField_management(in_file, Hab_field,
                                            "interpretBAP( !" + Hab_field + "! , !" + BAP_field + "!)", "PYTHON_9.3", codeblock)

print(''.join(["## Completed on : ", time.ctime()]))
exit()
