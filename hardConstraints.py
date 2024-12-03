# --------------------- Before Searching -------------------
# Put some assignments aside, these must be true. 
# If game CMSA U12T1 is requested:
# - CMSA U12T1S must be booked TR 18:00
# If game CMSA U13T1 is requested:
# - CMSA U13T1S must be booked TR 18:00
# Part-assign 
# No games on TR 11-1230


HOURS_PER_DAY = 13
TIMESLOTS = (HOURS_PER_DAY-1) * 2 # off by one error, 8-start to 9-end would be 12 hours

################################# init slots ###################################
def init_slots(game_max, game_min, practice_max, practice_min, DEBUG=False):
    slots = []
    for i in range((26*3)): # mul by 3 for MTF
        slots.append((game_max, game_min, practice_max, practice_min))
        if(DEBUG and i<HOURS_PER_DAY*2):
            if(i%2 == 0):
                print("slot %d: M@%d:00" % (i, 8+(i//2)))
            else:
                print("slot %d: M@%d:30" % (i, 8+(i//2)))
    return slots

def part_assign(game, slot):
    pass

# --------------------- Parser ---------------------
# Dictionary to get int for entry
# Query for assigned values
# <CMSA U12T1 DIV 01> <PRC 01>
# - make special note of type on read
# - practices can omit division (used by whole tier)

# --------------------- Slot interactions -------------------
# Method to decrement GAMEMAX
# Method to set GAMEMAX, GAMEMIN, PRACTICEMAX, PRACTICEMIN



# --------------------- Event Assignment ---------------------
# Modulus
# Gamemax
# Division 9 and above are evening divisions (6pm or later). 
# All games of U15/ U16/ U17/ U19 must not overlap.
# Unwanted
# Not compatible