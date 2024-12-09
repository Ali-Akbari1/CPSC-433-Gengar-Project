
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    GAMX, GAMN, PRAX, PRAN, SLOT, EVENING_CONST




# game min and practice min is less than amount of games/practices assigned
def eval_min(schedule, pen_gamemin, pen_practicemin):
    penalty = 0
    for slot in schedule[2]:  # was for slot in schedule[SLOT] but SLOT is equal to 2
        # print(slot)
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty += (slot[GAMN] - slot[GAMX]) * pen_gamemin

        if slot[PRAN] > 0 and slot[PRAX] < slot[PRAN]:
            penalty += (slot[PRAN] - slot[PRAX]) * pen_practicemin

    return penalty





# pref where games are scheduled
# TODO FIX EVAL PREF, I believe is right but schedule does not have any game times assigned to it 
# games and practices have a certain preference number to be in a time slot
# go through the preference map check if the game or practice is in the correct slot if not add the penalty to the preference number
# pref map = [[slotindex, gameindex, preference value]
#              slotindex2, gameindex2, preference value2...]
def eval_pref(schedule, preference_map):


    # ------------- CODE I BELIEVE IS ALMOST RIGHT---------------
    # penalty = 0
    # for pref_entry in preference_map:
    #     slot_index, event_index, preference_value = pref_entry
    #     print(schedule[PRAC])
    #     print(schedule[GAME])
    #     print(event_index)

    #     if isinstance(slot_index, tuple):
    #         if slot_index not in schedule[PRAC][event_index]:
    #             penalty += int(preference_value)
    #     # Check if the game is scheduled in the preferred slot
    #     elif slot_index not in schedule[GAME][event_index][GAME_TIME]:
    #         # Add the penalty if the game is not in the preferred slot
    #         penalty += int(preference_value)

    return 0
    
            




    # --------------- OLD CODE ----------------
    # print(preference_map)
    # print(schedule[GAME])
    # for game_id, game_slots in enumerate(schedule[GAME]):
    #     print(game_id, game_slots, "game id and sltos")
    #     if game_slots[0]:
    #         for slot in game_slots[1]:
    #             penalty += preference_map.get((game_id, slot), 0)
    #             print(penalty, "pennalty")
    # for game_id, practices in enumerate(schedule[PRAC]):
    #     if practices:
    #         for practice_id, practice in enumerate(practices):
    #             penalty += preference_map.get((game_id,
    #                                           tuple(practice_id), practice), 0)

    # #print("here eval pref")
    # return 0







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


    return penalty







# TODO game code should be different for diff disions with the same club - does this wok?
# TODO fix eval_secdiff
# No more tier map
# game_code = abs(games[gameCounter][GAME_CODE])
# if game_code > EVENING_CONST:
#     game_code -= EVENING_CONST
# if two teams in different divisions and same tier and age 
# game_code is the same for each 
def eval_secdiff(schedule, pen_section):
    penalty = 0
    game_code = abs(games[gameCounter][GAME_CODE])
    if game_code > EVENING_CONST:
        game_code -= EVENING_CONST
    print(game_code, "game code")

    return penalty





# evaluate all penalties
def eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map):
    return (
        eval_min(schedule, penalties[0],
                 penalties[1]) * weights[0]
        + eval_pref(schedule, preference_map) * weights[1]
        + eval_pair(schedule, pair_map,
                    penalties[2]) * weights[2]
        + eval_secdiff(schedule,
                       # if two teams in the same tier
                       penalties[3]) * weights[3]
    )









# TODO after main evals are fixed this should be remodelled to resemble them!
# if needed can be replaced with:
def eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map):
    contributions = {}  # Dictionary to store contributions for each event

    # Evaluate preference penalties
    for pref_entry in preference_map:
        slot_index, event_index, preference_value = pref_entry
        penalty = 0

        # Check if the event is a game or practice
        if isinstance(slot_index, tuple):
            # It's a practice
            if slot_index not in schedule[PRAC][event_index]:
                penalty += int(preference_value)
        else:
            # It's a game
            if slot_index not in schedule[GAME][event_index][GAME_TIME]:
                penalty += int(preference_value)

        contributions[('event', event_index)] = contributions.get(('event', event_index), 0) + penalty * weights[1]

    # Evaluate pairing penalties
    for event1, event2 in pair_map.items():
        # Determine slots for both events
        if isinstance(event1, int):
            event1_slot = schedule[GAME][event1][GAME_TIME]
        else:  # event1 is a practice
            event1_slot = schedule[PRAC][event1[0]][event1[1]]

        if isinstance(event2, int):
            event2_slot = schedule[GAME][event2][GAME_TIME]
        else:  # event2 is a practice
            event2_slot = schedule[PRAC][event2[0]][event2[1]]

        # Add penalty if events are not paired in the same slot
        if event1_slot != event2_slot:
            penalty = penalties[2] * weights[2]
            contributions[('event', event1)] = contributions.get(('event', event1), 0) + penalty / 2
            contributions[('event', event2)] = contributions.get(('event', event2), 0) + penalty / 2

    # Evaluate section difference penalties
    for slot_index, slot in enumerate(schedule[SLOT]):
        game_ids_in_slot = [
            game_id for game_id, game in enumerate(schedule[GAME]) if slot_index in game[GAME_TIME]
        ]
        for i in range(len(game_ids_in_slot)):
            for j in range(i + 1, len(game_ids_in_slot)):
                game1 = game_ids_in_slot[i]
                game2 = game_ids_in_slot[j]
                league1 = abs(schedule[GAME][game1][GAME_CODE])
                league2 = abs(schedule[GAME][game2][GAME_CODE])

                # Check if they are in the same tier/age group but different divisions
                if league1 == league2:
                    penalty = penalties[3] * weights[3]
                    contributions[('game', game1)] = contributions.get(('game', game1), 0) + penalty / 2
                    contributions[('game', game2)] = contributions.get(('game', game2), 0) + penalty / 2

    # Evaluate minimum fill penalties
    for slot_index, slot in enumerate(schedule[SLOT]):
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty = (slot[GAMN] - slot[GAMX]) * penalties[0] * weights[0]
            assigned_games = [
                game_id for game_id, game in enumerate(schedule[GAME]) if slot_index in game[GAME_TIME]
            ]
            for game_id in assigned_games:
                contributions[('game', game_id)] = contributions.get(('game', game_id), 0) + penalty / len(assigned_games)

        if slot[PRAN] > 0 and slot[PRAX] < slot[PRAN]:
            penalty = (slot[PRAN] - slot[PRAX]) * penalties[1] * weights[0]
            assigned_practices = [
                (game_id, prac_id) for game_id, practices in enumerate(schedule[PRAC])
                for prac_id, practice in enumerate(practices) if slot_index in practice
            ]
            for game_id, prac_id in assigned_practices:
                contributions[('practice', game_id, prac_id)] = contributions.get(
                    ('practice', game_id, prac_id), 0
                ) + penalty / len(assigned_practices)

    return contributions


## --------------------------- TESTING -------------------- ##


# def test_eval_functions():
#     # Mock data
#     scheduleEvalSecDiff = [
#         # Slots (mock example with some fields)
#         [{GAMN: 2, GAMX: 1, PRAN: 1, PRAX: 4}],
#         # Games (mock data with (code, time slot))
#         [(0, [0]), (1, [0]), (2, [0])],
#         # Practices
#         [[[]], [[]], [[]]],
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
#     # Slots
#     [{}],
#     # Games
#     [
#         (0, [0]),  # Game 0 in slot 0
#         (1, [0]),  # Game 1 in slot 0
#     ],
#     # Practices
#     [[[]], [[]]],
# ]

#     schedule_eval_pair = [
#     # Slots
#     [{}],
#     # Games
#     [
#         (0, [0]),  # Game 0 in slot 0
#         (1, [1]),  # Game 1 in slot 1
#     ],
#     # Practices
#     [[[]], [[]]],
# ]
#     pair_map_eval_pair = {0: 1, 1: 0}  # Games 0 and 1 are paired

#     preference_map_eval_pref = {(0, 0): 5, (1, 0): 3}


#     tier_map = {0: 1, 1: 1, 2: 2}  # Game codes and their tiers
#     penalties = [10, 20, 30, 40]  # Mock penalties
#     weights = [1, 1, 1, 1]  # Mock weights
#     preference_map = {(0, 0): 5, (1, 0): 3}  # Preferences for games
#     pair_map = {0: 1, 1: 0}  # Pairing of games

#     # print("PRINTING EVALS")
#     # print(eval_min(schedule_eval_min, penalties[0], penalties[1])) ## penalties[0] = 10, penalties[1] = 20
#     # print(eval_pref(schedule_eval_pref, preference_map_eval_pref)) ## eval_pref = 8
#     # print(eval_pair(schedule_eval_pair, pair_map_eval_pair, penalties[2])) ## eval_pair = 1
#     # print(eval_secdiff(scheduleEvalSecDiff, tier_map, penalties[3])) ## eval_secdiff = 80


#     # Test eval_secdiff
#     secdiff_penalty = eval_secdiff(scheduleEvalSecDiff, tier_map, penalties[3]) ## penalties[3] == 40
#     assert secdiff_penalty == 80, f"Expected 40, got {secdiff_penalty}"

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
