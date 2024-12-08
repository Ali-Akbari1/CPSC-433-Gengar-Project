import argparse
import re
import hardConstraints
import main
import model

from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
            GAME, GAME_CODE, GAME_TIME, \
            PRAC, \
            SLOT, GAMX, GAMN, PRAX, PRAN, \
            EVENING_CONST, EVENING_BOUND

# --------------------------- Setup ---------------------------
# Create command line arguments
inputParser = argparse.ArgumentParser()

inputParser.add_argument("filename", type=str)

# Soft constraint multipliers
inputParser.add_argument("minfilledWeight", type=int)
inputParser.add_argument("prefWeight", type=int)
inputParser.add_argument("pairWeight", type=int)
inputParser.add_argument("secdiffWeight", type=int)

# Soft constraint penalty values
inputParser.add_argument("gameminPenalty", type=int)
inputParser.add_argument("practiceminPenalty", type=int)
inputParser.add_argument("notpairedPenalty", type=int)
inputParser.add_argument("sectionPenalty", type=int)

# Parse the arguments
args = inputParser.parse_args()


def get_associated_game(prac): # TODO not working for no DIV practices
    return prac.subStr[0:-7]

games_names = []  # games array ["CSMA U16...", "CUSA U12...", ...]
prac_names = []  # practice array [["s", "s", "s"], ["s", "s", "s"], ...]

# --------------------------- Parse ---------------------------
with open(args.filename, "r") as inputFile:

    preference_map = {}
    pair_map = {}
    tier_map = {}
    tables = {}  # Using a dictionary, key: headers, values: rows
    
    sorted_ = None

    league_and_tiers = main.StringToUniqueNumber()

    # tables[someHeader] = [rows] <- list of rows (for Games and Practices I used a Dictionary instead)
    # tables[Games:/Practices:] = {Input line:index}
    games = []  # games array [(g0, (), ...]
    practices = []  # practices array [ [(), (), (), ]
    #                   [(), ()], [] ]

    # slots creation
    slots = main.init_slots(0, 0, 0, 0)

    gameCounter = 0
    practiceCounter = 0
    validHeader = ("Name:", "Game slots:", "Practice slots:", "Games:", "Practices:", "Not compatible:",
                   "Unwanted:", "Preferences:", "Pair:", "Partial assignments:")
    currentHeader = None

    for line in inputFile:
        line = line.strip()

        if not line:
            continue

        if line in validHeader:
            currentHeader = line
            if (currentHeader == "Games:"):
                tables[currentHeader] = {}
                _ = None

            elif (currentHeader == "Practices:"):
                tables[currentHeader] = {}
                _ = None
            else:
                # empty list with key header, list will hold rows
                tables[currentHeader] = []
            continue

        # clean up the excess or none spacing after commas
        line = re.sub(r",\s*", ", ", line)

        # ####################### Parsing Game Slots: ########################
        if currentHeader == "Game slots:":
            # [Day,  time,   gameMax, gameMin] for example:
            # ["MO", "8:00", 2,       1      ]
            gameLine = line.split(", ")
            if gameLine[0] == "MO":
                # 2 slots for Monday games 
                # update the gameMax of specified slot index
                slotInd = main.get_slot_index(gameLine[0], gameLine[1])
                slots[slotInd][0] = int(gameLine[2])
                slots[slotInd][1] = int(gameLine[3])
                slotInd+=1
                slots[slotInd][0] = int(gameLine[2])
                slots[slotInd][1] = int(gameLine[3]) 
            else:
                # 3 slots for Tuesday games 
                slotInd = main.get_slot_index(gameLine[0], gameLine[1])
                slots[slotInd][0] = int(gameLine[2])
                slots[slotInd][1] = int(gameLine[3])
                slotInd+=1
                slots[slotInd][0] = int(gameLine[2])
                slots[slotInd][1] = int(gameLine[3])
                slotInd+=1
                slots[slotInd][0] = int(gameLine[2])
                slots[slotInd][1] = int(gameLine[3])

        # ####################### Parsing Practice Slots: ########################

        if currentHeader == "Practice slots:":
            pracLine = line.split(", ")
            if pracLine[0] == "MO":
                # 2 slots for Monday Practices
                slotInd = main.get_slot_index(pracLine[0], pracLine[1])
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
            elif pracLine[0] == "TU":
                # 2 slots for Tuesday Practices
                slotInd = main.get_slot_index(pracLine[0], pracLine[1])
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
            else:
                # 4 slots for Friday practices
                slotInd = main.get_slot_index(pracLine[0], pracLine[1])
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=1
                slots[slotInd][2] = int(pracLine[2])
                slots[slotInd][3] = int(pracLine[3])

        # ####################### Parsing Games: ########################
        if currentHeader == "Games:":

            lineCopy = line.split()
            age = int(lineCopy[1][1:3])     # get age from age/tier, for example: U18T3 should be 18
            division = int(lineCopy[3][1:])

            # store the name
            games_names.append(line)

            # store the encoded game
            # get a unique number for the league and tier, this is used for open practices
            league_and_tier = lineCopy[0] + " " + lineCopy[1]
            game_id = league_and_tiers.get_number(league_and_tier)
            # Day games for under 16 have identifier: 0 < game_id < EVENING_CONST
            if (age < 16) and (division < 9):
                games.append([game_id, ()])
            # Evening games for under 16 have identifier: EVENING_CONST < game_id
            elif (age < 16) and (division >= 9):
                games.append([game_id+main.EVENING_CONST, ()])
            # Day games for over 16 have identifier: -EVENING_CONST < game_id < 0
            elif (age >= 16) and (division < 9):
                games.append([-game_id, ()])
            # Day games for over 16 have identifier: game_id < -EVENING_CONST
            elif (age >= 16) and (division >= 9):
                games.append([-game_id-main.EVENING_CONST, ()])

            # make a practice row for game, these are unnamed until pratices are read in. 
            # (so the order of games can switch)
            practices.append([])
            prac_names.append([])

            # game counter will be incorrect after alphabetizing. Game counter moved to out of loop. 
            # this needs to preserve order so that we can alphabetize it. Using an array for
            # that, then changing all the values. 
            # tables["Games:"][line] = game_index
            # this will let us read the output without searching dict values as well. 

            # Extracting the tier, e.g., "CSSC O19T1"
            tier_key = " ".join(line.split()[:2])
            # TODO tier map maps string to substring, we need to track the game names for
            # output anyways, we can just use the string itself and adjacent encodings
            tier_map[line] = tier_key


        # ####################### Parsing Practices: ########################
        if currentHeader == "Practices:":
            # games are done, sort them 
            if not sorted_:
                # alphabetize the games, keeping relative order to the abstracted games
                zipped_ = list(zip(games_names, games))
                sorted_ = sorted(zipped_, key=lambda x:x[0])

                games_names, games = zip(*sorted_)
                # TODO output uses games_names

                # now the indices will be correct so we can populate the dictionary entries
                for name_ in games_names:
                    tables["Games:"][name_] = gameCounter
                    gameCounter +=1

            # TODO open practices
            for i in range(len(line)):
                # TODO yikes, we do not need to do that much work
                # slice throught the string until we have a substring in Games
                subString = line[:i+1]
                # print(subString)
                # print(tables["Games:"])
                if subString in tables["Games:"]:
                    associated_game_index = tables["Games:"][subString]
                    practices[associated_game_index].append(())
                    prac_names[associated_game_index].append(line)
                    print("DEBUG: ",line, len(prac_names[associated_game_index]))
                    # add the index of the corresponding game, append an empty tuple
                    
                    # add to tables for easy access later
                    tables["Practices:"][line] = [associated_game_index, len(practices[associated_game_index])-1]
                    break
            pracArr = line.split()

            # case where 'DIV' was dropped, every division of this tier gets the practice
            if pracArr[-4] != "DIV":
                tierStr = pracArr[0] + " " + pracArr[1]
                for key in tables["Games:"]:
                    if tierStr in key:  # TODO is this ever true?  the whole game line is in there, not just the tierStr = pracArr[0] + " " + pracArr[1]
                        # TODO how do we handle this for not DIV?
                        practices[tables["Games:"][key]].append(())
                        tables["Practices:"][line] = [
                            tables["Games:"][key], int(pracArr[-1])]

            # elif (pracArr[-2] == "PRC" or pracArr[-2] == "OPN"):
            #     # print(pracArr)
            #     tables["Practices:"][line] = [
            #         tables["Games:"][subString], int(pracArr[-1])]

        # ####################### Parsing Not Compatible: ########################
        elif currentHeader == "Not compatible:":
            event1, event2 = line.split(", ")
            valid_flag = True

            # TODO: failed ali_tests\SmallerInput1
            # are there cases where the games in the "Not Compatible" input are not valid games?
            if event1 in tables["Games:"]:
                event1_index = tables["Games:"][event1]
            elif event1 in tables["Practices:"]:
                event1_index = tables["Practices:"][event1]
            else:
                print("Not Compatible: EVENT NOT FOUND: ", event1) # TODO flag? ignore?
                valid_flag = False

            if event2 in tables["Games:"]:
                event2_index = tables["Games:"][event2]
            elif event2 in tables["Practices:"]:
                event2_index = tables["Practices:"][event2]
            else:
                print("Not Compatible: EVENT NOT FOUND: ", event2) # TODO flag? ignore?
                valid_flag = False

            if valid_flag:
                hardConstraints.set_incompatible(event1_index, event2_index)

        elif currentHeader == "Unwanted:":
            unwantedSplit = line.split(", ")
            eventStr = unwantedSplit[0]
            if eventStr in tables["Games:"]:
                game_index = tables["Games:"][eventStr]
                hardConstraints.set_unwanted(
                    game_index, [main.get_slot_index(unwantedSplit[1], unwantedSplit[2])])
                # print(hardConstraints.unwanted)
            if eventStr in tables["Practices:"]:
                hardConstraints.set_unwanted(tables["Practices:"][eventStr], [
                                             main.get_slot_index(unwantedSplit[1], unwantedSplit[2])])

        # Nathan
        elif currentHeader == "Partial assignments:":
            # CUSA O18 DIV 01, MO, 8:00
            # CUSA O18 DIV 01, TU, 8:00
            # CUSA O18 DIV 01 PRC 01, FR, 8:00
            lineSplit = line.split(",")
            lineStrip = [x.strip() for x in lineSplit]

            event = lineStrip[0]

            if event in tables["Games:"]:
                event_index = tables["Games:"][event]
            elif event in tables["Practices:"]:
                event_index = tables["Practices:"][event]

            # CUSA O18 DIV 01, TU, 8:00
            # ["CUSA O18 DIV 01", "TU", "8:00"]
            slots_indices = main.get_slot_index(lineStrip[-2], lineStrip[-1])

            # TODO there should also be a template game/ practice that can take assignments.
            #   the model init takes a game and schedule, so whereever we call that
            hardConstraints.set_partassign([slots_indices], event_index)

        # ------------------- Parsing Preferences -------------------
        elif currentHeader == "Preferences:":
            # TODO practice preferences
            # Example: MO, 8:00, CSSC O19T1 DIV 01, 100
            pref_parts = line.split(", ")
            day, time, game, weight = pref_parts
            slot = f"{day}, {time}"
            # TODO raw game and slot? Does it work with invalid events?
            preference_map[(game, slot)] = int(weight)

        # ------------------- Parsing Pair -------------------
        # TODO practices too?
        elif currentHeader == "Pair:":
            valid_flag = True
            # Example: CMSA U12T1 DIV 01, CMSA U13T1 DIV 01
            game1, game2 = line.split(", ")
            if game1 in tables["Games:"]:
                game1_index = tables["Games:"][game1]
            else:
                valid_flag = False
            if game2 in tables["Games:"]:
                game2_index = tables["Games:"][game2]
            else:
                valid_flag = False
            
            if valid_flag:
                pair_map[game1_index] = game2_index

        # # ------------------- Parsing Games (for Tier Map) -------------------
        # elif currentHeader == "Games:":
        #     # Example: CSSC O19T1 DIV 01
        #     tables[currentHeader][line] = gameCounter
        #     games.append([1, ()])  # Example game initialization
        #     tier_key = " ".join(line.split()[:2])  # Extracting the tier, e.g., "CSSC O19T1"
        #     tier_map[line] = tier_key
        #     gameCounter += 1

        # create paralleles
        if line:
            if currentHeader == "Games:":
                # already added to tables
                continue
            if currentHeader == "Practices:":
                # already added to tables
                continue
            else:
                tables[currentHeader].append(line)

weights = [args.minfilledWeight, args.prefWeight,
           args.pairWeight, args.secdiffWeight]


penalties = [args.gameminPenalty, args.practiceminPenalty,
             args.notpairedPenalty, args.sectionPenalty]

myModel = model.Model(slots, games, practices, preference_map,
                      pair_map, tier_map, weights, penalties)



# print(args.gameminPenalty)

# inputParser.add_argument("gameminPenalty", type=int)
# inputParser.add_argument("practiceminPenalty", type=int)
# inputParser.add_argument("notpairedPenalty", type=int)
# inputParser.add_argument("sectionPenalty", type=int)

# print("\nThese are test prints")
# print(games)
# print(practices)
# print(slots)

# Print the maps for debugging
# print("Preference Map:", preference_map)
# print("Pair Map:", pair_map)
# print("Tier Map:", tier_map)
# main.print_schedule([games, practices, slots], 1, 1)

def print_output(eval, schedule):
    print("Eval-value:", eval)

    for game_index, _ in enumerate(schedule[GAME]):
        # only need the first slot index, half hour was for collisions
        if schedule[GAME][game_index][GAME_TIME][0]:
            game_slot = main.get_slot_string(schedule[GAME][game_index][GAME_TIME][0])
        else: 
            game_slot = "NOT ASSIGNED"
        print(games_names[game_index], ":", game_slot)

        for prac_index, _ in enumerate(schedule[PRAC][game_index]):
            if schedule[PRAC][game_index][prac_index][0]:
                prac_slot = main.get_slot_string(schedule[PRAC][game_index][prac_index][0])
            else: 
                prac_slot = "NOT ASSIGNED"
            print(prac_names[game_index][prac_index], ":", prac_slot)


# s_games = []
# s_practices = []
# s_slots = [[]]
# test_schedule = [s_games, s_practices, s_slots]

# M = 0  # not needed, just use the number. Nice for CTRL+D changes to T or F
# T = SLOTS_PER_DAY
# F = SLOTS_PER_DAY * 2

# # def set_test_1(s_games, s_practices, s_slots, test_schedule):
# s_games = [[1, (0,1)],[1, (0,1)],[1, (0,1)],[1, (0,1)], [-1000, (SLOTS_PER_DAY, SLOTS_PER_DAY+1)]]
# s_practices = [
#         [(2,3),(2,3),(2,3),(2,3), (SLOTS_PER_DAY, SLOTS_PER_DAY+1)],
#         [],
#         [],
#         [],
#         []
#     ]
# s_slots = main.init_slots(1,1,1,1)
# test_schedule = [s_games, s_practices, s_slots]

# print_output(0, test_schedule)