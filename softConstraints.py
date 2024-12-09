
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    GAMX, GAMN, PRAX, PRAN, SLOT, EVENING_CONST, pref_map_from_testing, tier_map_from_testing, pair_map_from_testing, slots_from_testing


# game min and practice min is less than amount of games/practices assigned
def eval_min(schedule, pen_gamemin, pen_practicemin):
    penalty = 0
    for slot_index, slot in enumerate(schedule[SLOT]):  
        slot_max = slot[GAMX]
        template_max = slots_from_testing[slot_index][GAMX]
        num_games_assigned = template_max - slot_max

        template_PRAX = slots_from_testing[slot_index][PRAX]
        slot_PRAX = slot[PRAX]
        num_prac_assigned = template_PRAX - slot_PRAX
        if slot[GAMN] > 0 and slot[GAMN] > (num_games_assigned):
            if slot_index < SLOTS_PER_DAY:
                penalty += ((slot[GAMN] - num_games_assigned) * pen_gamemin) / 2 
            else:
                penalty += ((slot[GAMN] - num_games_assigned) * pen_gamemin) / 3
        if slot[PRAN] > 0 and slot[PRAN] > (num_prac_assigned):
            if slot_index < SLOTS_PER_DAY*2:
                penalty += ((slot[PRAN] - num_prac_assigned) * pen_gamemin) / 2 
            else:
                penalty += ((slot[PRAN] - num_prac_assigned) * pen_gamemin) / 4
            #print(penalty, "penalty game min + practice min") # pen_practicemin = 20
    #print("here eval min")
    return penalty




#WORKS ON TEST1.TXT, DOES NOT WORK ON HUDSON MAYBE DUE TO DIV BEING OMIITED?
def eval_pref(schedule, preference_map):
    penalty = 0
    for pref_entry in preference_map:
        slot_index, event_index, preference_value = pref_entry

        if isinstance(slot_index, tuple):
            if slot_index not in schedule[PRAC][event_index]:
                penalty += int(preference_value)
        # Check if the game is scheduled in the preferred slot
        elif slot_index not in schedule[GAME][event_index][GAME_TIME]:
            # Add the penalty if the game is not in the preferred slot
            penalty += int(preference_value)

    return penalty
    
            
# EVAL PAIR WORKS BUT MODEL SOME TIMES DOES NOT BIAS TO BEING PAIRED
def eval_pair(schedule, pair_map, pen_notpaired):
    penalty = 0
    #print(pair_map)
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



# I THINK SEC DIFF WORKING 
# if two teams in different divisions and same tier and age 
def eval_secdiff(schedule, pen_section):
    penalty = 0

    # Iterate through all slots in the schedule
    for slot_index, slot in enumerate(schedule[SLOT]):
        # Get all games assigned to this slot
        games_in_slot = [
            game_index
            for game_index, game in enumerate(schedule[GAME])
            if slot_index in game[GAME_TIME]
        ]

        # Compare each pair of games in this slot
        for i in range(len(games_in_slot)):
            for j in range(i + 1, len(games_in_slot)):
                game1_index = games_in_slot[i]
                game2_index = games_in_slot[j]

                # Get game codes for comparison
                game1_code = abs(schedule[GAME][game1_index][GAME_CODE])
                game2_code = abs(schedule[GAME][game2_index][GAME_CODE])

                # Check if they are in the same tier/age group but different divisions
                if game1_code == game2_code and game1_index != game2_index:
                    slot_penalty = pen_section

                    # Adjust penalty based on slot index
                    if slot_index < SLOTS_PER_DAY:
                        slot_penalty /= 2
                    else:
                        slot_penalty /= 3
                    
                    penalty += slot_penalty

    return penalty


# evaluate all penalties
def eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map):
    return int((
    
        eval_min(schedule, penalties[0],
                 penalties[1]) * weights[0]

        + eval_pref(schedule, preference_map) * weights[1]
        + eval_pair(schedule, pair_map,
                    penalties[2]) * weights[2]
        + eval_secdiff(schedule,
                       # if two teams in the same tier
                       penalties[3]) * weights[3]
    ))


def eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map):
    contributions = {}  # Dictionary to store contributions for each event

    # Evaluate minimum fill penalties
    for slot_index, slot in enumerate(schedule[SLOT]):
        # Check for games not meeting the minimum
        if slot[GAMN] > 0 and slot[GAMX] < slot[GAMN]:
            penalty = (slot[GAMN] - slot[GAMX]) * penalties[0] * weights[0]
            assigned_games = [
                game_id for game_id, game in enumerate(schedule[GAME]) if slot_index in game[GAME_TIME]
            ]
            for game_id in assigned_games:
                contributions[('game', game_id)] = contributions.get(('game', game_id), 0) + penalty / len(assigned_games)

        # Check for practices not meeting the minimum
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

    # Evaluate preference penalties
    for pref_entry in preference_map:
        slot_index, event_index, preference_value = pref_entry

        if isinstance(slot_index, tuple):
            # It's a practice
            if slot_index not in schedule[PRAC][event_index]:
                penalty = int(preference_value) * weights[1]
                contributions[('practice', event_index)] = contributions.get(
                    ('practice', event_index), 0
                ) + penalty
        else:
            # It's a game
            if slot_index not in schedule[GAME][event_index][GAME_TIME]:
                penalty = int(preference_value) * weights[1]
                contributions[('game', event_index)] = contributions.get(
                    ('game', event_index), 0
                ) + penalty

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

    return contributions
