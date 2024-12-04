import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
            GAME, GAME_CODE, GAME_TIME, \
            PRAC, \
            SLOT, GAMX, GAMN, PRAX, PRAN

# TODO is there a better way?  Hashing is inefficient
unwanted = {}  # dictionary unwanted[event_index] = (slots)
incompatible = {} # dictionary incompatible[event_index] = [event_indices]

# --------------------------- assignment ---------------------------
# - checks all slots_indices can be assigned to (max > 0) 
# - checks for viability (mod checks and contiguous checks) 
# If any constraint fails, return false
# else success:
# - decrements gamemax or practicemax for all slot indices
# - sets the event time tuple to slots_indices

# NOTE Assign/ partassign. partassign will not be placed in update list
# partassigns must be tracked for collisions, each event should be represented in games 
# and practices, but we can keep the update list optimization for actual search. 
# ### Update list is a requirement, not an optimization ###

# event_index    - one number for games, two for practices. This is where to assign the slots to. 
# slots_indices  - a list of slots to assign the game/ practice
# solution       - where to store the information that an event is assigned
def assign(event_index, slots_indices, schedule, DEBUG=False):
    if DEBUG:
        print("---------------DEBUG ASSIGN ---------------")
        print("event index: ", event_index)
        print("slot indices: ", slots_indices)
    # easy checks, get them out of the way
    if not assign_helper_contiguous(slots_indices):
        if(DEBUG):
            print("Assignment failed: slots must be contiguous. ")
        return False
    if not assign_helper_alignment(slots_indices, event_index):
        if(DEBUG):
            print("Assignment failed: alignment. ")
        return False
    if not assign_helper_unwanted(event_index, schedule):
        if DEBUG:
            print("Assignment failed: unwanted. ")
        return False
    if not assign_helper_incompatible(event_index, schedule):
        if DEBUG:
            print("Assignment failed: incompatible. ")
        return False
    
    # if integer, event is a game (one index)
    if(isinstance(event_index, int)):
        # check the assignment can be done
        if not schedule[GAME][event_index][GAME_TIME] == ():
            if DEBUG:
                print("Cannot reassign game. ")
            return False
        for slot in slots_indices:
            if schedule[SLOT][slot][GAMX] <= 0:
                return False
            
        # do the assignment
        for slot in slots_indices:
            schedule[SLOT][slot][GAMX] -= 1
        schedule[GAME][event_index][GAME_TIME] = slots_indices
    
    # else two integers, event is a practice (two indices)
    elif(len(event_index) == 2):
        # check the assignment can be done
        if not schedule[PRAC][event_index[0]][event_index[1]] == ():
            if DEBUG:
                print("Cannot reassign practice: ",schedule[PRAC][event_index[0]][event_index[1]])
        for slot in slots_indices:
            if schedule[SLOT][slot][PRAX] <= 0:
                return False
        # event has two indices, so is a practice
        for slot in slots_indices:
            schedule[SLOT][slot][PRAX] -= 1   # decrement practicemax
        schedule[PRAC][event_index[0]][event_index[1]] = slots_indices
    else:
        print("event_index not int or list of length two. This should not happen. ")
        exit()

    return True

# function calls are probably inefficient. Maybe python is optimizing... 
def assign_helper_contiguous(slot_indices, max_index=(SLOTS_PER_DAY*3)-1, DEBUG=False):
    # error check
    if not slot_indices[0] >= 0:
        if DEBUG: print("Index must be greater than 0. ")
        return False
    if not slot_indices[-1] <= max_index:
        if DEBUG: print("Index must be less than max_index. ")
        return False
    
    # contiguous check
    for i in range(len(slot_indices)-1):
        if not slot_indices[i] - slot_indices[i+1] == -1:
            if DEBUG: print("Non-contiguous in slot_indices: %d, %d" % (slot_indices[i],slot_indices[i+1]))
            return False
        
    return True

def assign_helper_alignment(slot_indices, event_index, DEBUG=False):
    # begin and end on the same day
    if not slot_indices[0] // SLOTS_PER_DAY == slot_indices[-1] // SLOTS_PER_DAY:
        if DEBUG:
            print("Alignment failed, slot beginning and end on different days. ")
        return False
    
    # all events are 60 mins on Monday
    if slot_indices[0] < SLOTS_PER_DAY:
        if not len(slot_indices) == 2 or not slot_indices[0] % 2 == 0:
            return False
    
    # Tuesday
    elif slot_indices[0] < SLOTS_PER_DAY*2:
        # Tuesday games are 90 mins
        if isinstance(event_index, int):
            if not len(slot_indices) == 3 or not (slot_indices[0]-SLOTS_PER_DAY) % 3 == 0:
                if DEBUG:
                    print("Failed Tuesday game alignment. ")
                return False
        # Tuesday practices are 60 mins
        elif not len(slot_indices) == 2 or not slot_indices[0] % 2 == 0:
            if DEBUG:
                print("Failed Tuesday practice alignment. ")
            return False
    # Friday 
    elif slot_indices[0] < SLOTS_PER_DAY*3:
        # No Friday games
        if isinstance(event_index, int):
            if DEBUG:
                print("Cannot assign game to Friday slot")
            return False
        # Friday practices are 120 mins TODO not hour aligned? 
        elif not len(slot_indices) == 4 or not slot_indices[0] % 4 == 0:
            if DEBUG:
                print("Failed Friday practice alignment. ")
            return False
    else:
        if DEBUG:
            print("index too high, cannot be more than 3*SLOTS_PER_DAY")
        return False
    
    return True

def assign_helper_unwanted(event_index, schedule):
    if isinstance(event_index, int):
        event = event_index
    else:
        event = tuple(event_index)  # needed to hash into a dictionary
    if event in unwanted:
        unwanted_slots = unwanted[event]
        # game
        if isinstance(event_index, int):
            for slot in schedule[GAME][event_index][GAME_TIME]:
                if slot in unwanted_slots:
                    return False
        # practice
        else: 
            for slot in schedule[PRAC][event_index[0]][event_index[1]]:
                if slot in unwanted_slots:
                    return False
    return True

def assign_helper_incompatible(event_index, schedule):
    if isinstance(event_index, int):
        event = event_index
    else:
        event = tuple(event_index)
    if event in incompatible:
        for event in incompatible[event]:
            if not check_no_overlap(event_index, event, schedule):
                return False
    return True


# --------------------------- checks ---------------------------
# shouldn't need this (loop invariant), but maybe for debugging
def check_all_maxes_non_negative(schedule):
    for slot in schedule[SLOT]:
        if slot[GAMX]<=0:
            return False
        if slot[PRAX]<=0:
            return False

# iterates thorugh a pre-set deictionary
# helper function is used in assign, but this can be used for debug/ final double check if needed
# changed to tuples, might be broken
def check_all_unwanted(schedule):
    for event in unwanted:
        if not assign_helper_unwanted(unwanted[event], event, schedule):
            return False
    return True


def check_no_overlap(event_index1, event_index2, schedule):
    slots1 = ()
    slots2 = ()
    # get first set of slots
    if isinstance(event_index1, int):
        slots1 = schedule[GAME][event_index1][GAME_TIME]
    else:
        slots1 = schedule[PRAC][event_index1[0]][event_index1[1]]
    # get second set of slots
    if isinstance(event_index2, int):
        slots2 = schedule[GAME][event_index2][GAME_TIME]
    else:
        slots2 = schedule[PRAC][event_index2[0]][event_index2[1]]
    
    # compare slots
    for slot in slots1:
        if slot in slots2:   # O(n) in slot size, but the arrays should be so small that it should not matter
            return False     # checkig each bound would be O(2) and n will be max 4
    return True

# --------------------------- set ---------------------------
# make gamemax/ gamemin zero for all provided slot_indices (use for staff meeting)
def set_zero_game_max(slot_indices, schedule):
    for slot in slot_indices:
        schedule[SLOT][slot][GAMX] = 0
        schedule[SLOT][slot][GAMN] = 0
    return schedule

# TODO   I'll work on these on the way home
# Not compatible()

# TODO work on overlapping, this is tougher
# - divisions within a game
# - practices for a division
# - open practices for divisions
# - all games of older age groups (U15/ U16/ U17/ U19)

# TODO
# Division 9 and above are evening divisions (6pm or later). 



# ########################## Tests ##########################

# -------------------------- assign -----------------------
# Baby example
# - 2 games
# - 2 practices each
# - 12 slots, (min/ max are 1), 6 hrs of time

# Encodings
# positive = young
# negative = old
# constant = evening 

s_games = []
s_practices = []
s_slots = [[]]
test_schedule = [s_games, s_practices, s_slots]

# def set_test_1(s_games, s_practices, s_slots, test_schedule):
s_games = [[1, ()], [-1000, ()]]
s_practices = [
        [(), ()],
        [(), ()]
    ]
s_slots = m.init_slots(1,1,1,1)
test_schedule = [s_games, s_practices, s_slots]


# print("BEFORE assign:")
# print_schedule(test_schedule)
# if(not assign(0, (0,1), test_schedule)):
#     print("Failed 1")
# if(not assign(1, (0,1), test_schedule)): # gamemax should be zero, leading to fail
#     print("Failed 1")
# print("AFTER assign:")
# print_schedule(test_schedule)

# -------------------------- contiguous -----------------------
# print(assign_helper_contiguous((1,2,3,4))) # true
# print(assign_helper_contiguous((1,2,4)))   # false
# print(assign_helper_contiguous((-1,0,1)))  # false bounds
# print(assign_helper_contiguous((10000,10001,10001)))   # false bounds

# -------------------------- alignment/ bounds -----------------------
# print("BLOCK 1")
# print(assign_helper_alignment((0,1), 0))      # true
# print(assign_helper_alignment((0,1), [0,0]))  # true
# print(assign_helper_alignment((1,2), 0))      # false, game starts M on half hour
# print(assign_helper_alignment((1,2,3), 0))    # false, game starts M but is too long

# print("\nBLOCK 2")
# t = SLOTS_PER_DAY
# print(assign_helper_alignment((t,t+1,t+2), 0))     # true
# print(assign_helper_alignment((t,t+1,t+2), [0,0])) # false, too long for T practice
# print(assign_helper_alignment((t+1,t+2,t+3), 0))   # false, alignment
# print(assign_helper_alignment((t,t+1,t+2,t+3), 0)) # false, size

# print("\nBLOCK 3")
# f = SLOTS_PER_DAY*2
# print(assign_helper_alignment((f,f+1,f+2,f+3), [0,0])) # true, practice of correct length for F
# print(assign_helper_alignment((f,f+1), 0))           # false, F game
# print(assign_helper_alignment((f,f+1,f+2), 0))       # false, F game
# print(assign_helper_alignment((f,f+1,f+2,f+3), 0))   # false, F game
# print(assign_helper_alignment((f+1,f+2,f+3,f+4), [0,0])) # false, alignment
# print(assign_helper_alignment((f+2,f+3,f+4,f+5), [0,0])) # false, alignment
# print(assign_helper_alignment((f+3,f+4,f+5,f+6), [0,0])) # false, alignment
# print(assign_helper_alignment((f,f+1,f+2), [0,0]))       # false, size
# print(assign_helper_alignment((f,f+1,f+2,f+3,f+4), [0,0])) # false, size


# -------------------------- o0verlap -----------------------
# t = SLOTS_PER_DAY
# assign(0, (t,t+1,t+2), test_schedule)
# assign(1, (t+3,t+4,t+5), test_schedule)
# assign([0,0], (t,t+1), test_schedule, DEBUG=True)
# assign([0,1], (t+2,t+3), test_schedule, DEBUG=True)
# assign([1,1], (t+4,t+5), test_schedule, DEBUG=True)
# print(check_no_overlap(0,1,test_schedule)) # True
# m.print_schedule(test_schedule)
# print(check_no_overlap([0,0],[0,1],test_schedule)) # True
# print(check_no_overlap(0,[0,0],test_schedule)) # False
# print(check_no_overlap(0,[0,1],test_schedule)) # False
# print(check_no_overlap(0,[1,1],test_schedule)) # True




