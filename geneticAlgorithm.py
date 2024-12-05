import copy
import random

import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    SLOT, GAMX, GAMN, PRAX, PRAN, \
    EVENING_CONST, EVENING_BOUND

from hardConstraints import assign, unassign
from softConstraints import eval_penalty_contributions


def mutate(schedule, weights, penalties, preference_map, pair_map, tier_map):

    # Compute the penalty contributions per event
    contributions = eval_penalty_contributions(
        schedule, weights, penalties, preference_map, pair_map, tier_map)

    # Sum up total penalty contributions
    total_penalty = sum(contributions.values())

    # If there's no penalty, nothing to mutate
    if total_penalty == 0:
        return schedule

    # Compute selection probabilities as penalties / total_penalty
    events = list(contributions.keys())
    penalties = [contributions[event] for event in events]
    probabilities = [penalty / total_penalty for penalty in penalties]

    # Randomly select an event based on the computed probabilities
    selected_event = random.choices(events, weights=probabilities, k=1)[0]

    # Find all possible alternative placements for the selected event
    possible_slots = find_possible_slots(selected_event, schedule)

    # If alternative placements exist, choose one and reassign
    if possible_slots:
        new_slots_indices = random.choice(possible_slots)
        # Unassign the event from its current slot
        unassign(selected_event, schedule)
        # Assign the event to the new slot using hardConstraints' assign function
        assign(selected_event, new_slots_indices, schedule)

    # If no alternative placements, do nothing

    return schedule


def find_possible_slots(event_index, schedule):
    possible_slots = []
    current_assignment = None

    if event_index[0] == 'game':
        game_id = event_index[1]
        current_assignment = schedule[GAME][game_id][GAME_TIME]
        unassign(event_index, schedule)

        # Monday and Tuesday slots for games
        for day in range(0, SLOTS_PER_DAY * 2, SLOTS_PER_DAY):
            if day == 0:
                # Monday
                for start_slot in range(day, day + SLOTS_PER_DAY, 2):
                    slots_indices = [start_slot, start_slot + 1]
                    if slots_indices == current_assignment:
                        continue
                    if assign(event_index, slots_indices, schedule):
                        possible_slots.append(slots_indices)
                        unassign(event_index, schedule)  # Rollback
            else:
                # Tuesday
                for start_slot in range(day, day + SLOTS_PER_DAY - 2, 3):
                    slots_indices = [start_slot,
                                     start_slot + 1, start_slot + 2]
                    if slots_indices == current_assignment:
                        continue
                    if assign(event_index, slots_indices, schedule):
                        possible_slots.append(slots_indices)
                        unassign(event_index, schedule)  # Rollback

    elif event_index[0] == 'practice':
        game_id = event_index[1]
        prac_id = event_index[2]
        current_assignment = schedule[PRAC][game_id][prac_id]
        unassign(event_index, schedule)

        # Monday, Tuesday, and Friday slots for practices
        for day in range(0, SLOTS_PER_DAY * 3, SLOTS_PER_DAY):
            if day == 0 or day == SLOTS_PER_DAY:
                # Monday or Tuesday
                for start_slot in range(day, day + SLOTS_PER_DAY, 2):
                    slots_indices = [start_slot, start_slot + 1]
                    if slots_indices == current_assignment:
                        continue
                    if assign(event_index, slots_indices, schedule):
                        possible_slots.append(slots_indices)
                        unassign(event_index, schedule)  # Rollback
            else:
                # Friday
                for start_slot in range(day, day + SLOTS_PER_DAY - 3, 4):
                    slots_indices = [start_slot, start_slot +
                                     1, start_slot + 2, start_slot + 3]
                    if slots_indices == current_assignment:
                        continue
                    if assign(event_index, slots_indices, schedule):
                        possible_slots.append(slots_indices)
                        unassign(event_index, schedule)  # Rollback
    else:
        raise ValueError("Invalid event_index in find_possible_slots")

    # Reassign the original assignment if it existed
    if current_assignment:
        assign(event_index, current_assignment, schedule)

    return possible_slots
