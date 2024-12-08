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
    for i in range((SLOTS_PER_DAY*3)): # mul by 3 MTF
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
    if day == "t" or day == "T" or day == "TU":
        res += SLOTS_PER_DAY
    elif day == "f" or day == "F" or day == "FR":
        res += SLOTS_PER_DAY * 2
    return res

def get_slot_index_from_string(day_time):
    day, time = day_time.split(",")
    day = day.strip()
    time = time.strip()
    return get_slot_index(day, time)

def get_slot_string(slot_index):
    if slot_index<0:
        print("err, slot index cannot be negative. ")
        exit()
    
    day = ""
    if slot_index < SLOTS_PER_DAY:
        day = "MO"
    elif slot_index < SLOTS_PER_DAY*2:
        day = "TU"
        slot_index -= SLOTS_PER_DAY
    elif slot_index < SLOTS_PER_DAY*3:
        day = "FR"
        slot_index -= SLOTS_PER_DAY*2
    else:
        print("slot index too high, max is:", SLOTS_PER_DAY*3)
        exit()
    
    hour = (slot_index//2) + 8
    min = "00" if slot_index % 2 == 0 else "30"
    return day + ", " + str(hour) + ":" + min



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



class StringToUniqueNumber:
    # creates two dicts. One to search for assigned number, the other to search for string given number. 
    # (one for input to encoding, the other for encoding to output maybe for debugging)
    def __init__(self):
        self.string_to_number = {}
        self.number_to_string = {}
        self.iterator = 0
    
    def get_number(self, string):
        res = self.string_to_number.get(string, None)
        if res is None:
            self.iterator += 1
            self.string_to_number[string] = self.iterator
            self.number_to_string[self.iterator] = string
            return self.iterator
        return res

    def get_string(self, number):
        return self.number_to_string.get(number, None)
    
# strs = StringToUniqueNumber()

# lamb = strs.get_number("lamb")
# beef = strs.get_number("beef")
# duck = strs.get_number("duck")
# print(lamb, beef, duck)

# lamb = strs.get_string(lamb)
# beef = strs.get_string(beef)
# duck = strs.get_string(duck)
# print(lamb, beef, duck)




# games_names = ["are", "cool", "alphabets"]
# games = [":are", ":cool", ":alphabets"]

# zipped_gam = list(zip(games_names, games))
# sorted_gam = sorted(zipped_gam, key=lambda x:x[0])

# sorted_names, sorted_games = zip(*sorted_gam)
# print(sorted_names)
# print(sorted_games)



def test_get_slot_with_get_slot_index():
    string = "MO, 8:00"
    print(get_slot_string(get_slot_index_from_string(string)) == string)
    string = "TU, 8:00"
    # print(get_slot_index_from_string(string))
    # print(get_slot(get_slot_index_from_string(string)))
    print(get_slot_string(get_slot_index_from_string(string)) == string)
    string = "FR, 8:00"
    print(get_slot_string(get_slot_index_from_string(string)) == string)
    string = "MO, 20:30"
    print(get_slot_string(get_slot_index_from_string(string)) == string)
    string = "TU, 20:30"
    print(get_slot_string(get_slot_index_from_string(string)) == string)
    string = "FR, 20:30"
    print(get_slot_string(get_slot_index_from_string(string)) == string)

# test_get_slot_with_get_slot_index()



#################################### Testing for testing.py with some dummy values
# # needs access to game_names
# def print_output(eval, schedule):
    
#     games_names = ["1", "2"]
#     prac_names = [["1:0", "1:1"],["2:0", "2:1"]]
#     print("Eval-value:", eval)

#     for game_index, _ in enumerate(schedule[GAME]):
#         # only need the first slot index, half hour was for collisions
#         game_slot = get_slot_string(schedule[GAME][game_index][GAME_TIME][0])
#         print(games_names[game_index], ":", game_slot)

#         for prac_index, _ in enumerate(schedule[PRAC][game_index]):
#             prac_slot = get_slot_string(schedule[PRAC][game_index][prac_index][0])
#             print(prac_names[game_index][prac_index], ":", prac_slot)



# # Sample Output (not related to above inputs)
# # Eval-value: 30
# # CMSA U13T3 DIV 01 : MO, 10:00
# # CMSA U13T3 DIV 01 PRC 01 : TU, 10:00
# # CMSA U13T3 DIV 02 : MO, 14:00
# # CMSA U13T3 DIV 02 OPN 02 : MO, 8:00
# # CMSA U17T1 DIV 01 : TU, 9:30
# # CMSA U17T1 PRC 01 : MO, 8:00
# # CUSA O18 DIV 01 : MO, 8:00
# # CUSA O18 DIV 01 PRC 01 : FR, 10:00

# s_games = []
# s_practices = []
# s_slots = [[]]
# test_schedule = [s_games, s_practices, s_slots]

# M = 0  # not needed, just use the number. Nice for CTRL+D changes to T or F
# T = SLOTS_PER_DAY
# F = SLOTS_PER_DAY * 2

# # def set_test_1(s_games, s_practices, s_slots, test_schedule):
# s_games = [[1, (0,1)], [-1000, (SLOTS_PER_DAY, SLOTS_PER_DAY+1)]]
# s_practices = [
#         [(2,3), (SLOTS_PER_DAY, SLOTS_PER_DAY+1)],
#         [(SLOTS_PER_DAY+1,SLOTS_PER_DAY+2), (10,11)]
#     ]
# s_slots = init_slots(1,1,1,1)
# test_schedule = [s_games, s_practices, s_slots]

# print_output(0, test_schedule)