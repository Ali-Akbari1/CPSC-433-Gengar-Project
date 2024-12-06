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


# --------------------------- Parse ---------------------------
tables = {} # Using a dictionary, key: headers, values: rows
            # tables[someHeader] = [rows] <- list of rows
games = [] # games array
practices = [] # practices array



validHeader = ("Name:", "Game slots:", "Practice slots:", "Games:", "Practices:", "Not compatible:", "Unwanted:", "Preferences:", "Pair:", "Partial assignments:") # a set of strings containing headers
currentHeader = None

with open(args.filename, "r") as inputFile:
    for line in inputFile:
        line = line.strip() # remove leading or trailing spaces: " "
        
        if line in validHeader:
            if currentHeader != "Games:" or "Practice:":
                tables[currentHeader] = [] # empty list with key header, list will hold rows
            else:
                tables[currentHeader] = {}
            continue

        # empty line
        if not line:
            continue
        
        line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
        
        # Upon reaching Games: header we will create arrays for games
        if currentHeader == "Games:":
            main.addGame(tables, games, line)
            
            
            
            # lineCopy = line.split()
            # age = lineCopy[1][1:2]
            # division = lineCopy[3][1:]
            
            # if (age < 16) and (division < 9):
            #     games.append([1, ()])
            # elif (age < 16) and (division >= 9):
            #     games.append([1+main.EVENING_CONST, ()]) 
            # elif (age >= 16) and (division < 9):
            #     games.append([-1, ()])
            # elif (age >= 16) and (division >= 9):
            #     games.append([-1-main.EVENING_CONST, ()])
                
            practices.append([])
        
                
        # elif currentHeader == "Practice:":
        #     for i in range(len(line)):
        #         subString = line[:i+1]
        #         if subString in tables["Games:"]:
        #             practices[tables["Games:"][subString]].append([])
                  
                  
        # elif currentHeader == "Not compatible:":
        #     event1, event2 = line.split(", ")
        #     if event1 in tables["Games:"]:
        #         event1 = tables["Games:"]
        #     elif event1 in tables["Practice:"]:
            
        #     # for row in tables["Games:"]:
        #     #     if row == line[0]:
        #     #         event_index1 = row
        #     #     if row == line[1]:
        #     #         event_index2 = row
                    
        #     hardConstraints.set_incompatible()
            
            
        # create paralelle
        if line:
            line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
            
            # line = re.sub(r"\s+", " ", line) # cleanup possible excess spaces between words
            # ^ maybe unneccesary
            
            tables[currentHeader].append(line)
            


print(games)
print(practices)




# # --------------------------- Populate Hard Constraints ---------------------------
# for rows in tables["Not compatible:"]:
#     hardConstraints.set_unwanted()
    













            
# TODO integrate the soft constraint integer modifiers


