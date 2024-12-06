HOURS_PER_DAY = 13                    # 8am-start to 9pm-end would be 13
SLOTS_PER_DAY = HOURS_PER_DAY * 2

GAME = 0        # index of game array in schedule
GAME_CODE = 0   # index of game encoding in a game array
GAME_TIME = 1   # index of game slots tuple in a game array

PRAC = 1        # index of practice array in schedule

SLOT = 2        # index of slot array in schedule
GAMX = 0        # index of gamemax in slot array
GAMN = 1        # index of gamemin in slot array
PRAX = 2        # index of practicemax in slot array
PRAN = 3        # index of practicemin in slot array

# Game number key
# - positive number league/age, young divisions
# - positive number plus constant, = evening, young divisions
# - negative number for league/ age group 16 and above
# - negative number minus constant = evening, old divisions
EVENING_CONST = 1000
EVENING_BOUND = 20   # 8am start, this should be 6pm


################################# slots ###################################
# placeholder, parser can assign as needed
def init_slots(game_max, game_min, practice_max, practice_min, DEBUG=False):
    slots = []
    for i in range((SLOTS_PER_DAY*3)): # mul by 3 for MTF
        slots.append([game_max, game_min, practice_max, practice_min])
        if(DEBUG and i<HOURS_PER_DAY*2):
            if(i%2 == 0):
                print("slot %d: M@%d:00" % (i, 8+(i//2)))
            else:
                print("slot %d: M@%d:30" % (i, 8+(i//2)))
    return slots


def set_slot(slot_index, slot_array, schedule):
    schedule[SLOT][slot_index] = slot_array

# Find the index, given information about the slot.
# For testing/ DEBUG purposes.  
# Assumes start at 8:00 and 24hr time
# day <- {m, M, t, T, f, F}
# time <- {8:00, 8:30, ..., 20:30}
def get_slot_index(day, time):
    res = 0
    
    time_arr = time.split(":")
    if int(time_arr[0]) < 8:
        print("Please use 24hr clock, I dont want to do AM PM logic")
        return None

    res = (int(time_arr[0]) - 8) * 2
    if(time_arr[1] == "30"):
        res += 1

    # monday is default, nothing needs to be done
    if day == "t" or day == "T":
        res += SLOTS_PER_DAY
    elif day == "f" or day == "F":
        res += SLOTS_PER_DAY * 2
    return res



# print("Monday: %d, %d, ..., %d. " % (get_slot_index("M", "18:00"), get_slot_index("M", "18:30"), get_slot_index("M", "20:30")))
# print("Tuesday: %d, %d, ..., %d. " % (get_slot_index("T", "8:00"), get_slot_index("T", "8:30"), get_slot_index("T", "20:30")))
# print("Friday: %d, %d, ..., %d. " % (get_slot_index("F", "8:00"), get_slot_index("F", "8:30"), get_slot_index("F", "20:30")))


# ------------------------ Schedule -----------------------
# schedule = [games, practices, slots]
# games = [[n0, ()], [n1, ()], ..., [nk, ()]]
# practices = [[(), (), ..., ()],   # each game has multiple practices
#               [(), (), ..., ()],
#               ... 
#               [(), (), ..., ()]   # k arrays of practices, each has variable length
#            ]
# slots = [(GAMX,GAMN,PRAX,PRAN), (GAMX,GAMN,PRAX,PRAN), ..., (GAMX,GAMN,PRAX,PRAN)]
def print_schedule(schedule, events=True, slots=False):
    if events:
        print("-------- EVENTS --------")
        for g, game in enumerate(schedule[GAME]):
            print(g, game)

            for p, practice in enumerate(schedule[PRAC][g]):
                print("|", p, practice)

    if slots:
        print("\n-------- SLOTS --------")
        for s, slot in enumerate(schedule[SLOT]):
            print(s, slot)


    

# Game number key
# - positive number league/age, young divisions
# - positive number plus constant, = evening, young divisions
# - negative number for league/ age group 16 and above
# - negative number minus constant = evening, old divisions
gameCounter = 0
def addGame(tables, games, line):
    lineCopy = line.split()
    age = lineCopy[1][1:2]
    division = lineCopy[3][1:]
    
    if (age < 16) and (division < 9):
        games.append([1, ()])
    elif (age < 16) and (division >= 9):
        games.append([1+EVENING_CONST, ()]) 
    elif (age >= 16) and (division < 9):
        games.append([-1, ()])
    elif (age >= 16) and (division >= 9):
        games.append([-1-EVENING_CONST, ()])
        
    tables["Games:"][line] = gameCounter # for quick referencing the index of game strings, used in practices
    gameCounter += 1
    
