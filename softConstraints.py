
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
            GAME, GAME_CODE, GAME_TIME, \
            PRAC, \
            SLOT, GAMX, GAMN, PRAX, PRAN



def eval_min(schedule, pen_gamemin, pen_practicemin):
    penalty = 0
    for slot in schedule[SLOT]:
        if slot[GAMN] > 0 and slot[GAMX] > slot[GAMN]:
            penalty += (slot[GAMN] - slot[GAMX]) * pen_gamemin
        if slot[PRAN] > 0 and slot[PRAX] > slot[PRAN]:
            penalty += (slot[PRAN] - slot[PRAX]) * pen_practicemin
    return penalty


def eval_pref(schedule, preference_map):
    penalty = 0
    for game_id, game_slots in enumerate(schedule[GAME]):
        if game_slots[GAME_TIME]:
            for slot in game_slots[GAME_TIME]:
                penalty += preference_map.get((game_id, slot), 0)
    return penalty


def eval_pair(schedule, pair_map, pen_notpaired):
    penalty = 0
    for game_id, paired_game in     pair_map.items():
        game_slot = schedule[GAME][game_id][GAME_TIME]
        paired_slot = schedule[GAME][paired_game][GAME_TIME]
        if game_slot != paired_slot:
            penalty += pen_notpaired
    return penalty


def eval_secdiff(schedule, tier_map, pen_section):
    penalty = 0
    for slot_index, slot in enumerate(schedule[SLOT]):
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
        eval_min(schedule, penalties['pen_gamemin'], penalties['pen_practicemin']) * weights['w_minfilled']
        + eval_pref(schedule, preference_map) * weights['w_pref']
        + eval_pair(schedule, pair_map, penalties['pen_notpaired']) * weights['w_pair']
        + eval_secdiff(schedule, tier_map, penalties['pen_section']) * weights['w_secdiff']
    )   