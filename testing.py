import argparse
import re

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
inputParser.add_argument("sectionPenalty",type=int)

# Parse the arguments
args = inputParser.parse_args()


# --------------------------- Parse ---------------------------
tables = {} # Using a dictionary, key: headers, values: rows

validHeader = ("Name:", "Game slots:", "Practice slots:", "Games:", "Practices:", "Not compatible:", "Unwanted:", "Preferences:", "Pair:", "Partial assignments:") # a set of strings containing headers
currentHeader = None

with open(args.filename, "r") as inputFile:
    for line in inputFile:
        line = line.strip() # remove leading or trailing spaces: " "
        
        if line in validHeader:
            currentHeader = line
            tables[currentHeader] = [] # empty list with key header, list will hold rows
            
        elif line:
            line = re.sub(r",\s*", ", ", line) # clean up the excess or none spacing after commas
            
            # line = re.sub(r"\s+", " ", line) # cleanup possible excess spaces between words
            # ^ maybe unneccesary
            
            tables[currentHeader].append(line)
            
# TODO integrate the soft constraint integer modifiers
        