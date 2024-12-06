import argparse
import re
import hardConstraints
import main
import softConstraints

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


def get_associated_game(prac):
    return prac.subStr[0:-7]

# --------------------------- Parse ---------------------------
with open(args.filename, "r") as inputFile:
    
    
    tables = {} # Using a dictionary, key: headers, values: rows
                # tables[someHeader] = [rows] <- list of rows
    games = [] # games array
    practices = [] # practices array
    
    # slots creation
    slots = main.init_slots(0, 0, 0, 0)

    gameCounter = 0
    practiceCounter = 0
    validHeader = ("Name:", "Game slots:", "Practice slots:", "Games:", "Practices:", "Not compatible:", "Unwanted:", "Preferences:", "Pair:", "Partial assignments:") # a set of strings containing headers
    currentHeader = None
    
    # TODO strip everything:
    #    string = "CASA U19 DIV01, CASA U19 DIV02"
    #    print(string.split(", "))
    #    > ['CASA U19 DIV01', 'CASA U19 DIV02']                 # good 

    #    string = "CASA U19 DIV01,              CASA U19 DIV02"
    #    print(string.split(", "))
    #    > ['CASA U19 DIV01', '             CASA U19 DIV02']    # bad 

    
    #    string = "CASA U19 DIV01,              CASA U19 DIV02"
    #    print(string.split(", "))
    #    stripped = [x.strip() for x in string.split(",")]
    #    print(stripped)
    #    > ['CASA U19 DIV01', '             CASA U19 DIV02']    # bad 
    #    > ['CASA U19 DIV01', 'CASA U19 DIV02']                 # good
    
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
                tables[currentHeader] = [] # empty list with key header, list will hold rows
            continue

        line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
        
        # ####################### Parsing Game Slots: ########################
        # MO = 0-12, TU = 13-38, WE = 39-51, TH = 52-76, FR = 
        # TODO our slots are half hour, each entry is 2 or three slots
        if currentHeader == "Game slots:":
            gameLine = line.split(", ")    # [Day (ie MO), time (ie 8:00), gameMax, gameMin]
            if gameLine[0] == "MO":        # assign to Wednesday and Friday too
                slotInd = main.get_slot_index('M', gameLine[1])
                slots[slotInd][0] = int(gameLine[2])    # update the gameMax of specified slot index
                slots[slotInd][1] = int(gameLine[3]) 
            else:
                slotInd = main.get_slot_index('T', gameLine[1])
                slots[slotInd][0] = int(gameLine[2])    
                slots[slotInd][1] = int(gameLine[3])
                
                
        # ####################### Parsing Practice Slots: ########################
        # TODO our slots are half hour, each entry is 2 or 4 slots
        if currentHeader == "Practice slots:":
            pracLine = line.split(", ")
            if pracLine[0] == "MO":        # assign to Wednesday and Friday too
                slotInd = main.get_slot_index('M', pracLine[1])
                slots[slotInd][2] = int(pracLine[2])    # update the gameMax of specified slot index
                slots[slotInd][3] = int(pracLine[3]) 
            elif pracLine[0] == "TU":
                slotInd = main.get_slot_index('T', pracLine[1])
                slots[slotInd][2] = int(pracLine[2])    
                slots[slotInd][3] = int(pracLine[3])
            else:
                slotInd = main.get_slot_index('F', pracLine[1])
                slots[slotInd][2] = int(pracLine[2])    
                slots[slotInd][3] = int(pracLine[3])
        
        # ####################### Parsing Games: ########################
        if currentHeader == "Games:":
            
            # 
            lineCopy = line.split()
            age = int(lineCopy[1][1:2])     # age/tier
            division = int(lineCopy[3][1:])
            
            # HELP: not sure about the logic below
            if (age < 16) and (division < 9):
                games.append([1, ()])
            elif (age < 16) and (division >= 9):
                games.append([1+main.EVENING_CONST, ()]) 
            elif (age >= 16) and (division < 9):
                games.append([-1, ()])
            elif (age >= 16) and (division >= 9):
                games.append([-1-main.EVENING_CONST, ()])
                
            practices.append([])
            
            tables["Games:"][line] = gameCounter # for quick referencing the index of game strings, used in practices
            gameCounter += 1
        
        # ####################### Parsing Practices: ########################
        if currentHeader == "Practices:":
            for i in range(len(line)):
                subString = line[:i+1]
                # print(subString)
                # print(tables["Games:"])
                if subString in tables["Games:"]:
                    practices[tables["Games:"][subString]].append(())
            tables["Practices:"][line] = practiceCounter
            practiceCounter += 1
        
        # ####################### Parsing Not Compatible: ########################
        elif currentHeader == "Not compatible:":
            event1, event2 = line.split(", ")
            if event1 in tables["Games:"]:
                event1_index = tables["Games:"][event1]
            elif event1 in tables["Practices:"]:
                # TODO (associated_game, practice_number)
                # associated_game = take the practice flag and number off and search for games
                # practice_number = take the length of the practice array before appending, then append the practice (zero index)
                event1_index = (0, 0)                       # HELP: not sure what to put for the practice indices still
                
            if event2 in tables["Games:"]:
                event2_index = tables["Games:"][event2]
            elif event2 in tables["Practices:"]:
                event2_index = (0, 0)                       # ^^^
                
            hardConstraints.set_incompatible(event1_index, event2_index)
            
            
        elif currentHeader == "Unwanted:":
            lineSplit = line.split()
            
            hardConstraints.set_unwanted()
            
        # TODO preferences
        # TODO pair
        # TODO partial assign
            
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
                associated_game = get_associated_game(event)
                game_index = tables["Games:"][associated_game]
                event_index = (game_index, practice_index)# HELP: not sure what to put for the practice indices still
                # TODO how are you gettting the practice index?

            # CUSA O18 DIV 01, TU, 8:00
            # ["CUSA O18 DIV 01", "TU", "8:00"]
            slots_indices = main.get_slot_index(lineStrip[1], lineStrip[1])

            # TODO there should also be a template game/ practice that can take assignments. 
            #   the model init takes a game and schedule, so whereever we call that
            hardConstraints.set_partassign(event_index, slots_indices)
            
            
        # create paralelles
        if line:
            line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
            
            # line = re.sub(r"\s+", " ", line) # cleanup possible excess spaces between words
            # ^ maybe unneccesary
            if currentHeader == "Games:":
                continue
            if currentHeader == "Practices:":
                continue
            else:
                tables[currentHeader].append(line)
            


# print(games)
# print(practices)

# string = "CASA U19 DIV01, CASA U19 DIV02"
# print(string.split(", "))

# # --------------------------- Populate Hard Constraints ---------------------------
# for rows in tables["Not compatible:"]:
#     hardConstraints.set_unwanted()
    













            
# TODO integrate the soft constraint integer modifiers


