#from testing import preference_map, tier_map, pair_map
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    GAMX, GAMN, PRAX, PRAN, SLOT, slots_from_testing, pref_map_from_testing, pair_map_from_testing, tier_map_from_testing



# slots = [[]]
# game min and practice min is less than amount of games/practices assigned
def eval_min(schedule, pen_gamemin, pen_practicemin):
    #print(schedule[0])
    #print(schedule[1])
    #print(schedule)
    penalty = 0
    # CHANGE IMPORT ONCE CIRCULAR IMPORT ERROR 
    # for now circular import error
    for slot_index, slot in enumerate(schedule[SLOT]):  
        #print(slot)
        #print(schedule[SLOT])
        slot_max = slot[GAMX]
        #print(slot_max)
        #print(slots_from_testing)
        template_max = slots_from_testing[slot_index][GAMX]
        num_games_assigned = template_max - slot_max
        template_PRAX = slots_from_testing[slot_index][PRAX]
        slot_PRAX = slot[PRAX]
        num_prac_assigned = template_PRAX - slot_PRAX
        if slot[GAMN] > 0 and slot[GAMN] > (num_games_assigned):
            penalty += (slot[GAMN] - num_games_assigned) * pen_gamemin # pen_gamemin = 10
            #print(penalty, "penalty game min")
        if slot[PRAN] > 0 and slot[PRAN] > (num_prac_assigned): # PRAN = 3, PRAX = 2
            penalty += (slot[PRAN] - num_prac_assigned) * pen_practicemin
            #print(penalty, "penalty game min + practice min") # pen_practicemin = 20
    #print("here eval min")
    return penalty

# pref where games are scheduled

# TODO practices are not put into the prefernece map so i am guessing key structure
# TODO in testing preference map key for games is (game_id, slot)
# where  slot = f"{day}, {time}" and game is its name not the current format

def eval_pref(schedule, preference_map):
#     penalty = 0
#     # was schedule[GAME] but GAME is 0
    
#     for game_id, game_slots in enumerate(schedule[0]):
#         if game_slots[1]:
#             for slot in game_slots[1]:
#                 penalty += preference_map.get((game_id, slot), 0)
#     for game_id, practices in enumerate(schedule[1]):
#         if practices:
#             for practice_id, practice in enumerate(practices):
#                 penalty += preference_map.get((game_id,
#                                               tuple(practice_id), practice), 0)

    #print("here eval pref")
    return 0

# games and/or practices to be scheduled at same times

# TODO needs testing


def eval_pair(schedule, pair_map, pen_notpaired):
    penalty = 0

    for event1, event2 in pair_map.items():
        # Determine the type of the first event
        if isinstance(event1, int):
            # It's a game
            event1_slot = schedule[GAME][event1][GAME_TIME]
        elif isinstance(event1, tuple) and len(event1) == 2:
            # It's a practice
            event1_slot = schedule[PRAC][event1[0]][event1[1]]
        else:
            raise ValueError(f"Invalid event type for event1: {event1}")

        # Determine the type of the second event
        if isinstance(event2, int):
            # It's a game
            event2_slot = schedule[GAME][event2][GAME_TIME]
        elif isinstance(event2, tuple) and len(event2) == 2:
            # It's a practice
            event2_slot = schedule[PRAC][event2[0]][event2[1]]
        else:
            raise ValueError(f"Invalid event type for event2: {event2}")

        # Compare the slots
        if event1_slot != event2_slot:
            penalty += pen_notpaired

    #print("Pairing penalty calculated:", penalty)
    return penalty

# TODO game code should be different for diff disions with the same club - does this wok?
# if two teams in the same tier

def eval_secdiff(schedule, tier_map, pen_section):
    penalty = 0
    # for slot_index, slot in enumerate(schedule[2]):
    #     # List of leagues in the current slot
    #     leagues_in_slot = [
    #         game[GAME_CODE] for game in schedule[0] if slot_index in game[GAME_TIME]
    #     ]

    #     for league1 in leagues_in_slot:
    #         for league2 in leagues_in_slot:
    #             if league1 != league2 and tier_map[league1] == tier_map[league2]:
    #                 # print("here")
    #                 penalty += pen_section
    return penalty


# evaluate all penalties
def eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map):
    return (
        eval_min(schedule, penalties[0],
                 penalties[1]) * weights[0]
        + eval_pref(schedule, preference_map) * weights[1]
        + eval_pair(schedule, pair_map,
                    penalties[2]) * weights[2]
        + eval_secdiff(schedule, tier_map,
                       # if two teams in the same tier
                       penalties[3]) * weights[3]
    )

# TODO after main evals are fixed this should be remodelled to resemble them!
# if needed can be replaced with:


# game_code = abs(games[game index][GAME_CODE])
# if game_code > EVENING_CONST
#   game_code -= EVENING_CONST
#

def eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map):
    contributions = {}  # Dictionary to store contributions for each event

    # Evaluate preference penalties
    for game_id, game in enumerate(schedule[GAME]):
        if game[GAME_TIME]:
            penalty = 0
            for slot in game[GAME_TIME]:
                penalty += preference_map.get((game_id, slot), 0)
            contributions[('game', game_id)] = penalty * weights[1]

    # Evaluate pairing penalties
    for event1, event2 in pair_map.items():
        event1_slot = schedule[GAME][event1][GAME_TIME] if isinstance(
            event1, int) else schedule[PRAC][event1[0]][event1[1]]
        event2_slot = schedule[GAME][event2][GAME_TIME] if isinstance(
            event2, int) else schedule[PRAC][event2[0]][event2[1]]
        if event1_slot != event2_slot:
            penalty = penalties[2] * weights[2]
            contributions[('event', event1)] = contributions.get(
                ('event', event1), 0) + penalty / 2
            contributions[('event', event2)] = contributions.get(
                ('event', event2), 0) + penalty / 2

    # Evaluate section difference penalties
    for slot_index, slot in enumerate(schedule[SLOT]):
        game_ids_in_slot = [game_id for game_id, game in enumerate(
            schedule[GAME]) if slot_index in game[GAME_TIME]]
        for i in range(len(game_ids_in_slot)):
            for j in range(i + 1, len(game_ids_in_slot)):
                league1 = schedule[GAME][game_ids_in_slot[i]][GAME_CODE]
                league2 = schedule[GAME][game_ids_in_slot[j]][GAME_CODE]
                if league1 != league2 and tier_map[league1] == tier_map[league2]:
                    penalty = penalties[3] * weights[3]
                    contributions[('game', game_ids_in_slot[i])] = contributions.get(
                        ('game', game_ids_in_slot[i]), 0) + penalty / 2
                    contributions[('game', game_ids_in_slot[j])] = contributions.get(
                        ('game', game_ids_in_slot[j]), 0) + penalty / 2

    # Evaluate minimum fill penalties
    for slot_index, slot in enumerate(schedule[SLOT]):
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty = (slot[GAMN] - slot[GAMX]) * penalties[0] * weights[0]
            assigned_games = [game_id for game_id, game in enumerate(
                schedule[GAME]) if slot_index in game[GAME_TIME]]
            for game_id in assigned_games:
                contributions[('game', game_id)] = contributions.get(
                    ('game', game_id), 0) + penalty / len(assigned_games)
        if slot[PRAN] > 0 and slot[PRAX] < slot[PRAN]:
            penalty = (slot[PRAN] - slot[PRAX]) * penalties[1] * weights[0]
            assigned_practices = [(game_id, prac_id) for game_id, practices in enumerate(
                schedule[PRAC]) for prac_id, practice in enumerate(practices) if slot_index in practice]
            for game_id, prac_id in assigned_practices:
                contributions[('practice', game_id, prac_id)] = contributions.get(
                    ('practice', game_id, prac_id), 0) + penalty / len(assigned_practices)

    return contributions



# # --------------------------- TESTING -------------------- ##


# def test_eval_functions():
#     # Mock data
#     scheduleEvalSecDiff = [

#         # Games (mock data with (code, time slot))
#         [[0, (0)], [1, (0)], [2, (0)]],
#         # Practices
#         [[()],
#         [()],
#         [()]],
#         # Slots (mock example with some fields)
#         [[2, 1, 1,  4]],
#     ]

#     schedule_eval_min = [
#     # Games
#     [[0, ()], [1, (1)]],
#     # Practices
#     [[()],
#     [()],
#     [()]],
#     # Slots
#     [
#         [ 3,  4,  1,  0],  # Exceeds minimum games, no practices
#         [ 2,  1,  1,  2],  # Does not meet min games or practices
#     ]
# ]
#     schedule_eval_pref = [

#     # Games
#     [
#         [0, (0)],  # Game 0 in slot 0
#         [1,(0)],  # Game 1 in slot 0
#     ],
#     # Practices
#     [[()],
#     [()],
#     [()]],
#     # Slots
#     [[]],
# ]

#     schedule_eval_pair = [

#     # Games
#     [
#         [0, (0)],  # Game 0 in slot 0
#         [1, (1)],  # Game 1 in slot 1
#     ],
#     # Practices
#     [[()],
#     [()],
#     [()]],
#     # Slots
#     [[]],
# ]
#     pair_map_eval_pair = {0: 1, 1: 0}  # Games 0 and 1 are paired

#     preference_map_eval_pref = {(0, 0): 5, (1, 0): 3}


#     tier_map = {0: 1, 1: 1, 2: 2}  # Game codes and their tiers
#     penalties = [10, 20, 30, 40]  # Mock penalties
#     weights = [1, 1, 1, 1]  # Mock weights
#     preference_map = {(0, 0): 5, (1, 0): 3}  # Preferences for games
#     pair_map = {0: 1, 1: 0}  # Pairing of games

#     print("PRINTING EVALS")
#     #print(schedule_eval_min)
#     print(eval_min(schedule_eval_min, penalties[0], penalties[1])) ## penalties[0] = 10, penalties[1] = 20
#     print(eval_pref(schedule_eval_pref, preference_map_eval_pref)) ## eval_pref = 8
#     print(eval_pair(schedule_eval_pair, pair_map_eval_pair, penalties[2])) ## eval_pair = 1
#     #print(eval_secdiff(scheduleEvalSecDiff, tier_map, penalties[3])) ## eval_secdiff = 80


#     # Test eval_secdiff
#     #secdiff_penalty = eval_secdiff(scheduleEvalSecDiff, tier_map, penalties[3]) ## penalties[3] == 40
#     #assert secdiff_penalty == 80, f"Expected 40, got {secdiff_penalty}"

#     # Test eval_cost
#     ## sec_diff = 40

#     # total_cost = eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map)
#     # expected_cost = 28
#     # assert total_cost == expected_cost, f"Expected {expected_cost}, got {total_cost}"

#     # Test eval_penalty_contributions
#     # contributions = eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map)
#     # expected_contributions = {
#     #     ('game', 0): 5,  # Preference penalty
#     #     ('game', 1): 3,  # Preference penalty
#     #     ('game', 0): 20,  # Pairing penalty
#     #     ('game', 1): 20,  # Pairing penalty
#     # }

#     #print("All tests passed.")

# # Run the test
# test_eval_functions()
