import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
            GAME, GAME_CODE, GAME_TIME, \
            PRAC, \
            SLOT, GAMX, GAMN, PRAX, PRAN, \
            EVENING_CONST, EVENING_BOUND


# TODO work on overlapping, this is tougher
# - divisions within a tier

unwanted = {}  # dictionary unwanted[event_index] = (slots)
incompatible = {} # dictionary incompatible[event_index] = [event_indices]

# bandaids for bullet holes, worked in Breaking Bad
open_practices = {} # dictionary  open_practices[practice_tuple] = [game_indices].  append on taking in
upper_level = {} # set  upper_level = {slot_index, slot_index, ..., slot_index}  check for membership before assignment

# --------------------------- assignment ---------------------------
# - checks all slots_indices can be assigned to (max > 0) 
# - checks for viability (mod checks and contiguous checks) 
# - checks for practice collision with division game/ vice versa
# - checks collisions on Friday practice/ Monday games
# If any constraint fails, return false
# 
# On success:
# - decrements gamemax or practicemax for all slot indices
# - sets the event time tuple to slots_indices

# NOTE Assign/ partassign. partassign will not be placed in update list
# partassigns must be tracked for collisions, each event should be represented in games 
# and practices, but we can keep the update list optimization for actual search. 
# ### Update list is a requirement, not an optimization ###

# event_index    - one number for games, two for practices. This is where to assign the slots to. 
# slots_indices  - a list of slots to assign the game/ practice
# solution       - where to store the information that an event is assigned
def assign(event_index, slots_indices, schedule, set=True, DEBUG=False):
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
    if not assign_helper_game_prac_overlap(slots_indices, event_index, schedule, DEBUG):
        if DEBUG:
            print("Assign failed. Practice overlaps with associated div game: ", event_index)
        return False
    if not assign_helper_evening(slots_indices, event_index, schedule):
        if DEBUG:
            print("Assign failed. Evening class not in evening slot: ", event_index, slots_indices)
        return False
    
    # if integer, event is a game (one index)
    if(isinstance(event_index, int)):
        # check the assignment can be done
        if not schedule[GAME][event_index][GAME_TIME] == ():
            if DEBUG:
                print("Assign failed. Cannot reassign game. ")
            return False
        for slot in slots_indices:
            if schedule[SLOT][slot][GAMX] <= 0:
                if DEBUG:
                    print("Assign failed. Gamemax would be exceeded. ")
                return False
            
        # if set is true, do the assignment
        if set:
            for slot in slots_indices:
                schedule[SLOT][slot][GAMX] -= 1
            schedule[GAME][event_index][GAME_TIME] = slots_indices
    
    # else two integers, event is a practice (two indices)
    elif(len(event_index) == 2):
        # check the assignment can be done
        if not schedule[PRAC][event_index[0]][event_index[1]] == ():
            if DEBUG:
                print("Assign failed. Cannot reassign practice: ",schedule[PRAC][event_index[0]][event_index[1]])
        for slot in slots_indices:
            if schedule[SLOT][slot][PRAX] <= 0:
                if DEBUG:
                    print("Assign failed. Practicemax would be exceeded. ")
                return False
        # event has two indices, so is a practice
        # if set is true, make it so
        if set:
            for slot in slots_indices:
                schedule[SLOT][slot][PRAX] -= 1   # decrement practicemax
            schedule[PRAC][event_index[0]][event_index[1]] = slots_indices
    else:
        print("Assign failed. event_index not int or list of length two. This should not happen. ")
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
        # Friday practices are 120 mins and aligned starting 8:00 on Friday TODO not hour aligned? 
        elif not len(slot_indices) == 4 or not (slot_indices[0]-(SLOTS_PER_DAY*2)) % 4 == 0:
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

def assign_helper_game_prac_overlap(slots_indices, event_index, schedule, DEBUG=False):
    if DEBUG:
        print("Game/Prac overlap, slots:", slots_indices, ", event:", event_index)
    # test a potential assignment
    # game, check all practices
    if isinstance(event_index, int):
        for practice in schedule[PRAC][event_index]:
            for slot in practice:
                # Friday practices collide with Monday games
                # games cannot have Friday slot (slot index will never be that high)
                if slot >= SLOTS_PER_DAY*2:
                    slot -= SLOTS_PER_DAY*2

                if slot in slots_indices:
                    return False
    # practice, just check game
    else:
        for slot in slots_indices:
            # Friday collisions with Monday games
            if slot >= SLOTS_PER_DAY*2:
                slot -= SLOTS_PER_DAY*2
            if slot in schedule[GAME][event_index[0]][GAME_TIME]:
                if DEBUG: 
                    print("Fail on:", slot, " in game: ", schedule[GAME][event_index[0]])
                return False
        
    return True

def assign_helper_evening(slot_indices, event_index, schedule, DEBUG=False):
    # check whether the event has an evening restriction
    if isinstance(event_index, int):
        event_code = abs(schedule[GAME][event_index][GAME_CODE])
    else:
        event_code = abs(schedule[GAME][event_index[0]][GAME_CODE])
    
    if event_code < EVENING_CONST:
        # event is not evening, no restriction
        if DEBUG:
            print("Not evening class, no restriction:", event_code, "<", EVENING_CONST)
        return True
        
    # if event does have restriction, make sure it is within bounds
    # normalize to abstract the day out. Result should be 8:00-20:30 (0-something, i think it was 26) regardless of day
    # if the first one is evening, the rest must be too
    slot_zero_norm = slot_indices[0] - SLOTS_PER_DAY*(slot_indices[0]//SLOTS_PER_DAY)
    # if the normalized time is less than the evening bound, 
    # this evening class is being assigned a day slot. Kill it. 
    if slot_zero_norm < EVENING_BOUND:
        if DEBUG:
            print("Fail. Evening class with day slot:", slot_zero_norm, "<", EVENING_BOUND)
        return False
        
    if DEBUG:
        print("Alles Klar")
    return True

# half assed 
def assign_helper_open_practice(slot_indices, event_index, schedule, DEBUG=False):
    # game or not in open practices return True
    if isinstance(event_index, int) or (not tuple(slot_indices) in open_practices):
        return True
    
    for game_index in open_practices[tuple(event_index)]:
        if not check_slots_no_overlap(slot_indices, game_index, schedule):
            return False
    return True

def assign_helper_upper_level(slot_indices, event_index, schedule, DEBUG=False):
    # no restriction on tutorials
    if not isinstance(event_index, int):
        return True
    # no potential problem unless event is in upper_level
    if not event_index in upper_level:
        return True
    
    # games are aligned, bit of a shortcut but I think ti sohuld hold
    for game_index in upper_level: # iterate thorugh indices 
        if schedule[GAME][game_index][GAME_TIME][0] == slot_indices[0]:
            return False
    
    return True

# just for mutate
def unassign(event_index, schedule, DEBUG=False):
    # game
    if isinstance(event_index, int):
        slots = schedule[GAME][event_index][GAME_TIME]
        # put the max up again for each slot
        for slot in slots:
            schedule[SLOT][slot][GAMX] += 1
        # unassign slots from game
        schedule[GAME][event_index][GAME_TIME] = ()
    # practice
    else: 
        slots = schedule[PRAC][event_index[0]][event_index[1]]
        # put the max up again for each slot
        for slot in slots:
            schedule[SLOT][slot][PRAX] += 1
        # unassign slots from practice
        schedule[PRAC][event_index[0]][event_index[1]] = ()


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

# used by incompatible
def check_no_overlap(event_index1, event_index2, schedule, DEBUG=False):
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
            if DEBUG:
                print("Check overlap fail: ", event_index1, ":", slots1, event_index2, ":", slots2)
            return False     # checkig each bound would be O(2) and n will be max 4
    return True

def check_slots_no_overlap(slot_indices, event_index, schedule, DEBUG=False):
    slots_event = ()
    # get set of slots from event
    if isinstance(event_index, int):
        slots_event = schedule[GAME][event_index][GAME_TIME]
    else:
        slots_event = schedule[PRAC][event_index[0]][event_index[1]]
    # compare slots
    for slot in slots_event:
        if slot in slot_indices:
            if DEBUG:
                print("Check overlap fail: ", event_index, ":", slots_event, "with :", slot_indices)
            return False
    return True


# old, integrated as a helper in assign
# def check_game_prac_overlap(slot_indices, event_index, schedule, DEBUG=False):
#     # game, check all practices
#     if isinstance(event_index, int):
#         for practice_index, _ in enumerate(schedule[PRAC][event_index]):
#             if not check_no_overlap(event_index, (event_index, practice_index), schedule, DEBUG):
#                 if DEBUG:
#                     print("Fail in game practice overlap 1: ", event_index, practice_index)
#                 return False
#     # practice, check the game
#     else:
#         print(event_index[0], event_index)
#         if not check_no_overlap(event_index[0], event_index, schedule, DEBUG):
#             if DEBUG:
#                 print("Fail in game practice overlap 2: ", event_index, practice_index)
#             return False

#     return True

# --------------------------- set ---------------------------
# make gamemax/ gamemin zero for all provided slot_indices (use for staff meeting)
def set_zero_game_max(slot_indices, schedule):
    for slot in slot_indices:
        schedule[SLOT][slot][GAMX] = 0
        schedule[SLOT][slot][GAMN] = 0
    return schedule


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

M = 0  # not needed, just use the number. Nice for CTRL+D changes to T or F
T = SLOTS_PER_DAY
F = SLOTS_PER_DAY * 2

# def set_test_1(s_games, s_practices, s_slots, test_schedule):
s_games = [[1, ()], [-1000, ()]]
s_practices = [
        [(), ()],
        [(), ()]
    ]
s_slots = m.init_slots(1,1,1,1)
test_schedule = [s_games, s_practices, s_slots]

def test(b):
    if b:
        print("PASS")
    else:
        print("FAIL")

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
# not working, integrated check into assign
# t = SLOTS_PER_DAY
# assign(0, (t,t+1,t+2), test_schedule)
# assign(1, (t+3,t+4,t+5), test_schedule)
# assign([0,0], (t,t+1), test_schedule)
# assign([0,1], (t+2,t+3), test_schedule)
# assign([1,1], (t+4,t+5), test_schedule)
# print(check_no_overlap(0,1,test_schedule)) # True
# m.print_schedule(test_schedule)
# print(check_no_overlap([0,0],[0,1],test_schedule)) # True
# print(check_no_overlap(0,[0,0],test_schedule)) # False
# print(check_no_overlap(0,[0,1],test_schedule)) # False
# print(check_no_overlap(0,[1,1],test_schedule)) # True

# -------------------------- div/ practice -----------------------
def test_div_practice_collision():
    # print("Monday:")
    # test(assign(0, (0,1), test_schedule) == True) 
    # test(assign([0,0], (0,1), test_schedule) == False) # overlap err, game already assigned
    # test(assign([0,1], (2,3), test_schedule) == True)
    # test(assign([1,0], (2,3), test_schedule) == False) # max err 
    # test(assign([1,1], (4,5), test_schedule) == True) 
    # test(assign(1, (4,5), test_schedule) == False) # overlap err, practice already assigned

    print("Friday:")
    test(assign(0,      (F,F+1),            test_schedule) == False) # fail, game cannot be Friday 
    test(assign([0,0],  (F,F+1,F+2,F+3),    test_schedule) == True)
    test(assign(0,      (M,M+1),            test_schedule) == False) # fail, overlap with [0,0]
    test(assign(0,      (M+8,M+9),          test_schedule) == True)
    test(assign([0,1],  (F+2,F+3),          test_schedule) == False) # fail, F practices must be 2hrs
    test(assign([0,1],  (F+2,F+3,F+4,F+5),  test_schedule) == False) # fail, alignment
    test(assign([0,1],  (F+4,F+5,F+6,F+7),  test_schedule) == True)
    test(assign([1,0],  (F,F+1,F+2,F+3),    test_schedule) == False) # max err
    test(assign([1,0],  (F,F+1,F+2,F+3),    test_schedule) == False) # max err
    m.print_schedule(test_schedule)

# test_div_practice_collision()


def test_assign_helper_evening():
    # assign_helper_evening only checks the first slot index, so most of these are (n,0)
    test(assign_helper_evening((0,1), 0,        test_schedule) == True) # game 0 has code 1 (not evening)
    test(assign_helper_evening((0,1), [0,0],    test_schedule) == True) # practice [0,0] for game 0 with code 1 (not evening) 
    test(assign_helper_evening((0,1), 1,        test_schedule) == False) # game 1 has code -1000 (evening)
    test(assign_helper_evening((0,1), [1,0],    test_schedule) == False) # practice [1,0] for game 0 with code -1000 (evening)
    test(assign_helper_evening((20,21), 1,      test_schedule) == True) # good evening
    test(assign_helper_evening((24,25), [1,0],  test_schedule) == True) # good evening
    print("T")
    test(assign_helper_evening((T,0), 0,          test_schedule) == True) # good T game morning
    test(assign_helper_evening((T,0), [0,0],      test_schedule) == True) # good T prac morning
    test(assign_helper_evening((T,0), [0,0],      test_schedule) == True) # good T prac morning
    test(assign_helper_evening((T+20,0), 0,       test_schedule) == True) # good T game evening
    test(assign_helper_evening((T,0), 1,          test_schedule) == False) # bad T game morning
    test(assign_helper_evening((T,0), [1,0],      test_schedule) == False) # bad T prac morning
    test(assign_helper_evening((T+20,0), [1,0],   test_schedule) == True) # good T prac evening
    print("F") # dup t tests to make sure they work on Friday
    test(assign_helper_evening((F,0), 0,          test_schedule) == True) # good F game morning
    test(assign_helper_evening((F,0), [0,0],      test_schedule) == True) # good F prac morning
    test(assign_helper_evening((F,0), [0,0],      test_schedule) == True) # good F prac morning
    test(assign_helper_evening((F+20,0), 0,       test_schedule) == True) # good F game evening
    test(assign_helper_evening((F,0), 1,          test_schedule) == False) # bad F game morning
    test(assign_helper_evening((F,0), [1,0],      test_schedule) == False) # bad F prac morning
    test(assign_helper_evening((F+20,0), [1,0],   test_schedule) == True) # good F prac evening

# test_assign_helper_evening()