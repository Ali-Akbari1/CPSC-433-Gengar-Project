
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    GAMX, GAMN, PRAX, PRAN


def eval_min(schedule, pen_gamemin, pen_practicemin):
    print(schedule[0])
    penalty = 0
    for slot in schedule[0]:
        print(slot)
        if slot[GAMN] > 0 and slot[GAMX] > slot[GAMN]:
            penalty += (slot[GAMN] - slot[GAMX]) * pen_gamemin
        if slot[PRAN] > 0 and slot[PRAX] > slot[PRAN]:
            penalty += (slot[PRAN] - slot[PRAX]) * pen_practicemin
    return penalty


def eval_pref(schedule, preference_map):
    penalty = 0
    for game_id, game_slots in enumerate(schedule[1]):
        if game_slots[GAME_TIME]:
            for slot in game_slots[GAME_TIME]:
                penalty += preference_map.get((game_id, slot), 0)
    return penalty


def eval_pair(schedule, pair_map, pen_notpaired):
    penalty = 0
    for game_id, paired_game in pair_map.items():
        game_slot = schedule[1][game_id][GAME_TIME]
        paired_slot = schedule[1][paired_game][GAME_TIME]
        if game_slot != paired_slot:
            penalty += pen_notpaired
    return penalty


def eval_secdiff(schedule, tier_map, pen_section):
    penalty = 0
    for slot_index, slot in enumerate(schedule[0]):
        # List of leagues in the current slot
        leagues_in_slot = [
            game[GAME_CODE] for game in schedule[GAME] if slot_index in game[GAME_TIME]
        ]
        for league1 in leagues_in_slot:
            for league2 in leagues_in_slot:
                if league1 != league2 and tier_map[league1] == tier_map[league2]:
                    penalty += pen_section
    return penalty


def eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map):
    return (
        eval_min(schedule, penalties[0],
                 penalties[1]) * weights[0]
        + eval_pref(schedule, preference_map) * weights[1]
        + eval_pair(schedule, pair_map,
                    penalties[2]) * weights[2]
        + eval_secdiff(schedule, tier_map,
                       penalties[3]) * weights[3]
    )


def eval_penalty_contributions(schedule, weights, penalties, preference_map, pair_map, tier_map):
    contributions = {}  # event -> penalty

    # Evaluate preferences per event
    for game_id, game in enumerate(schedule[1]):
        # TODO each game in schedule is (n, ()) where () is the time slot, ^^ here game should already be the game slot
        penalty = 0
        if game[GAME_TIME]:
            for slot in game[GAME_TIME]:
                penalty += preference_map.get((game_id, slot), 0)
        contributions[('game', game_id)] = penalty * weights[1]

    # Evaluate pairing penalties
    for game_id, paired_game in pair_map.items():
        game_slot = schedule[GAME][game_id][GAME_TIME]
        paired_slot = schedule[GAME][paired_game][GAME_TIME]
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
                league1 = schedule[GAME][game_id1][GAME_CODE]
                league2 = schedule[GAME][game_id2][GAME_CODE]
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
                    if slot_index in practice:
                        key = ('practice', game_id, prac_id)
                        contributions[key] = contributions.get(
                            key, 0) + penalty / slot[PRAX]

    return contributions
