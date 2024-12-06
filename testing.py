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






# # day: M, T, F | time: ex. 3:00
# def getSlotIndex(day, time):
#     hours, halfHours  = time.split(':')
#     time = int(hours)
#     if halfHours != "00":
#         time += 1
        
#     if day == "M":     # 0-25
#         return time - 16
#     elif day == "T":   # 26-51
#         return 26+time -16
#                 # W 52-77 (add 26 to skip Tuesday)
#                 # T 78-103
#     else:            # F 104-129
#         return 84+time -16

# --------------------------- Parse ---------------------------
with open(args.filename, "r") as inputFile:
    
    
    tables = {} # Using a dictionary, key: headers, values: rows
                # tables[someHeader] = [rows] <- list of rows (for Games and Practices I used a Dictionary instead)
    games = [] # games array [(g0, (), ...]
    practices = []  # practices array [ [(), (), (), ]
                    #                   [(), ()], [] ]
    
    # slots creation
    slots = main.init_slots(0, 0, 0, 0)

    gameCounter = 0
    practiceCounter = 0
    validHeader = ("Name:", "Game slots:", "Practice slots:", "Games:", "Practices:", "Not compatible:", "Unwanted:", "Preferences:", "Pair:", "Partial assignments:") # a set of strings containing headers
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
                tables[currentHeader] = [] # empty list with key header, list will hold rows
            continue

        line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
        
        # ####################### Parsing Game Slots: ########################
        if currentHeader == "Game slots:":
            gameLine = line.split(", ")    # [Day (ie MO), time (ie 8:00), gameMax, gameMin]
            if gameLine[0] == "MO":        # assign to Wednesday and Friday too
                slotInd = main.get_slot_index('M', gameLine[1])
                slots[slotInd][0] = int(gameLine[2])    # update the gameMax of specified slot index
                slots[slotInd][1] = int(gameLine[3])    # update gameMin
                slotInd+=27 # move to Wednesday
                slots[slotInd][0] = int(gameLine[2])    
                slots[slotInd][1] = int(gameLine[3])  
                slotInd+=27 # move to Friday
                slots[slotInd][0] = int(gameLine[2])    
                slots[slotInd][1] = int(gameLine[3])  
            else:
                slotInd = main.get_slot_index('T', gameLine[1])
                slots[slotInd][0] = int(gameLine[2])    
                slots[slotInd][1] = int(gameLine[3])
                slotInd+=27 # move to Thurday
                slots[slotInd][0] = int(gameLine[2])    
                slots[slotInd][1] = int(gameLine[3])
                
                
        # ####################### Parsing Practice Slots: ########################
        if currentHeader == "Practice slots:":
            pracLine = line.split(", ")
            if pracLine[0] == "MO":
                slotInd = main.get_slot_index('M', pracLine[1])
                slots[slotInd][2] = int(pracLine[2])   
                slots[slotInd][3] = int(pracLine[3]) 
                slotInd+=27
                slots[slotInd][2] = int(pracLine[2])   
                slots[slotInd][3] = int(pracLine[3]) 
            elif pracLine[0] == "TU":
                slotInd = main.get_slot_index('T', pracLine[1])
                slots[slotInd][2] = int(pracLine[2])    
                slots[slotInd][3] = int(pracLine[3])
                slotInd+=27
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
            
            # TODO: game index creation logic
            # idk if this is right...
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
                subString = line[:i+1]      # slice throught the string until we have a substring in Games
                # print(subString)
                # print(tables["Games:"])
                if subString in tables["Games:"]:
                    practices[tables["Games:"][subString]].append(())
            tables["Practices:"][line] = practiceCounter
            practiceCounter += 1
        
        # ####################### Parsing Not Compatible: ########################
        elif currentHeader == "Not compatible:":
            event1, event2 = line.split(", ")
            
            # TODO: failed ali_tests\SmallerInput1
            # are there cases where the games in the "Not Compatible" input are not valid games? 
            if event1 in tables["Games:"]:
                event1_index = tables["Games:"][event1]
            elif event1 in tables["Practices:"]:
                event1_index = (0, 0)                       # TODO: not sure what to put for the practice indices still
                
            if event2 in tables["Games:"]:
                event2_index = tables["Games:"][event2]
            elif event2 in tables["Practices:"]:
                event2_index = (0, 0)                       # ^^^
                
            hardConstraints.set_incompatible(event1_index, event2_index)
            
            
        elif currentHeader == "Unwanted:":
            unwantedSplit = line.split(", ")
            gameStr = unwantedSplit[0]
            if gameStr in tables["Games:"]:
                game_index = tables["Games:"][gameStr]
                hardConstraints.set_unwanted(game_index, [main.get_slot_index(unwantedSplit[1], unwantedSplit[2])])
                # print(hardConstraints.unwanted)
            
            
        
            
            
            
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
        
        

print("\nThese are test prints")
print(games)
print(practices)
print(slots)





            
# TODO integrate the soft constraint integer modifiers


