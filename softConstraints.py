
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    GAMX, GAMN, PRAX, PRAN



# CONSTANTS were changed to numbers but the numbers are different, 
# however those functions i believe were working so not going to change them for now

## eval_min, eval_pref, eval_pair working 

# game min and practice min is less than amount of games/practices assigned
def eval_min(schedule, pen_gamemin, pen_practicemin):
    print(schedule[0])
    penalty = 0
    for slot in schedule[2]: ## was for slot in schedule[SLOT] but SLOT is equal to 2
        #print(slot)
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty += (slot[GAMN] - slot[GAMX]) * pen_gamemin
            print(penalty, "penalty game min")
        if slot[PRAN] > 0 and slot[PRAX] < slot[PRAN]:
            penalty += (slot[PRAN] - slot[PRAX]) * pen_practicemin
            print(penalty,"penalty game min + practice min")
    print("here eval min")
    return penalty

# pref where games are scheduled
def eval_pref(schedule, preference_map):
    penalty = 0
    for game_id, game_slots in enumerate(schedule[0]): ## was schedule[GAME] but GAME is 0
        if game_slots[1]:
            for slot in game_slots[1]:
                penalty += preference_map.get((game_id, slot), 0)
    print("here eval pref")
    return penalty

# games and/or practices to be scheduled at same times
def eval_pair(schedule, pair_map, pen_notpaired):
    penalty = 0
    for game1id in pair_map:
        print(game1id)
        game2id = pair_map[game1id]
        game_slot = schedule[0][int(game1id)][GAME_TIME]
        paired_slot = schedule[1][game2id][1]
        if game_slot != paired_slot:
            penalty += pen_notpaired
        print("here eval pair")
    return penalty


## if two teams in the same tier 
def eval_secdiff(schedule, tier_map, pen_section):
    penalty = 0
    for slot_index, slot in enumerate(schedule[2]):
        # List of leagues in the current slot
        leagues_in_slot = [
            game[GAME_CODE] for game in schedule[0] if slot_index in game[GAME_TIME]
        ]

        for league1 in leagues_in_slot:
            for league2 in leagues_in_slot:
                if league1 != league2 and tier_map[league1] == tier_map[league2]:
                    #print("here")
                    penalty += pen_section
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
                       penalties[3]) * weights[3] ## if two teams in the same tier 
    )


def eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map):
    contributions = {}  # event -> penalty

    # Evaluate preferences per event
    for game_id, game in enumerate(schedule[1]):
        penalty = 0
        if game[GAME_TIME]:
            for slot in game[GAME_TIME]:
                penalty += preference_map.get((game_id, slot), 0)
        contributions[('game', game_id)] = penalty * weights[1]

    # Evaluate pairing penalties
    for game_id, paired_game in pair_map.items():
        game_slot = schedule[1][game_id][GAME_TIME]
        paired_slot = schedule[1][paired_game][GAME_TIME]
        if game_slot != paired_slot:
            penalty = penalties[2] * weights[2]
            contributions[('game', game_id)] = contributions.get(
                ('game', game_id), 0) + penalty / 2
            contributions[('game', paired_game)] = contributions.get(
                ('game', paired_game), 0) + penalty / 2

    # Evaluate section differences
    for slot_index, slot in enumerate(schedule[0]):
        game_ids_in_slot = [game_id for game_id, game in enumerate(
            schedule[1]) if slot_index in game[GAME_TIME]]
        for i in range(len(game_ids_in_slot)):
            for j in range(i + 1, len(game_ids_in_slot)):
                game_id1 = game_ids_in_slot[i]
                game_id2 = game_ids_in_slot[j]
                league1 = schedule[1][game_id1][GAME_CODE]
                league2 = schedule[1][game_id2][GAME_CODE]
                if league1 != league2 and tier_map[league1] == tier_map[league2]:
                    penalty = penalties[3] * weights[3]
                    contributions[('game', game_id1)] = contributions.get(
                        ('game', game_id1), 0) + penalty / 2
                    contributions[('game', game_id2)] = contributions.get(
                        ('game', game_id2), 0) + penalty / 2

    # Evaluate minimum fill penalties
    for slot_index, slot in enumerate(schedule[0]):
        # Games
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty = (slot[GAMN] - slot[GAMX]) * \
                penalties[0] * weights[0]
            assigned_games = [game_id for game_id, game in enumerate(
                schedule[1]) if slot_index in game[GAME_TIME]]
            for game_id in assigned_games:
                contributions[('game', game_id)] = contributions.get(
                    ('game', game_id), 0) + penalty / len(assigned_games)
        # Practices
        if slot[PRAN] > 0 and slot[PRAX] < slot[PRAN]:
            penalty = (slot[PRAN] - slot[PRAX]) * \
                penalties[1] * weights[0]
            for game_id, practices in enumerate(schedule[PRAC]):
                for prac_id, practice in enumerate(practices):
                    if isinstance(practice, int):
                        practice = [practice]
                        if slot_index in practice:
                            if slot[PRAX] > 0:
                                contributions[key] = contributions.get(key, 0) + penalty / slot[PRAX]
                            else:
                                raise ValueError(f"PRAX value is 0 for slot {slot_index}, division by zero prevented.")


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
#     # Slots
#     [
#         {GAMN: 3, GAMX: 4, PRAN: 1, PRAX: 0},  # Exceeds minimum games, no practices
#         {GAMN: 2, GAMX: 1, PRAN: 2, PRAX: 1},  # Does not meet min games or practices
#     ],
#     # Games
#     [(0, [0]), (1, [1])],
#     # Practices
#     [[[]], [[]]],
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
