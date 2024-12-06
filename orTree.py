import copy
import random

from geneticAlgorithm import find_possible_slots
import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    SLOT, GAMX, GAMN, PRAX, PRAN, \
    EVENING_CONST, EVENING_BOUND

from hardConstraints import assign

from softConstraints import eval_cost


class OrTreeNode:
    def __init__(self, pr, sol='?', children=None):
        # pr = (slots, games, practices)
        self.pr = pr
        # slots: list of (gamemax, gamemin, pracmax, pracmin)
        self.sol = sol
        # practices: list of list of assigned_slots_tuple
        self.children = children if children is not None else []

    def is_leaf(self):
        return len(self.children) == 0

    def copy(self):
        return OrTreeNode(copy.deepcopy(self.pr), self.sol, copy.deepcopy(self.children))


def eval(pr, preference_map=None, pair_map=None, weights=None, penalties=None, tier_map=None):
    (slots, games, practices) = pr
    schedule = [games, practices, slots]
    return eval_cost(schedule, weights, penalties, preference_map, pair_map, tier_map)



def is_complete(pr):

    # see if all games and practices are assigned
    (slots, games, practices) = pr

    for g in games:
        if g[1] == ():
            return False
    for p_list in practices:
        for p in p_list:
            if p == ():
                return False
    return True


def altern(pr):
    (slots, games, practices) = pr

    for gi, g in enumerate(games):
        if g[GAME_TIME] == ():
            # unassigned game found
            return generate_game_alternatives(pr, gi)

    # if no unassigned game, check practices
    for gi, p_list in enumerate(practices):
        for pi, p in enumerate(p_list):
            if p == ():
                # Unassigned practice found
                return generate_practice_alternatives(pr, gi, pi)

    # No unassigned events
    return []


def generate_game_alternatives(pr, game_index):
    # find valid assignments for the game
    possible_assignments = find_valid_game_assignments(pr, game_index)
    new_nodes = []
    for assignment in possible_assignments:
        new_pr = apply_assignment(pr, ('game', game_index), assignment)
        if Constr(new_pr):
            new_nodes.append(OrTreeNode(new_pr, '?'))
    return new_nodes


def generate_practice_alternatives(pr, game_index, practice_index):
    # find valid assignments for the practice
    possible_assignments = find_valid_practice_assignments(
        pr, game_index, practice_index)
    new_nodes = []
    for assignment in possible_assignments:
        new_pr = apply_assignment(
            pr, ('practice', game_index, practice_index), assignment)
        if Constr(new_pr):
            new_nodes.append(OrTreeNode(new_pr, '?'))
    return new_nodes


def apply_assignment(pr, event_key, slots_indices):
    # Apply the assignment to the given event in a copy of pr.
    # Reorder pr into [games, practices, slots] for assign()
    (slots, games, practices) = pr
    schedule = [games, practices, slots]
    # assumes assign returns True/False
    success = assign(event_index, slots_indices, schedule)
    if success:
        # Update pr from schedule after assignment
        new_slots = schedule[SLOT]
        new_games = schedule[GAME]
        new_practices = schedule[PRAC]
        return (new_slots, new_games, new_practices)
    else:
        # if not successful, just return original pr (though ideally shouldn't happen if checked))
        return pr


def fleaf(nodes, preference_map=None, pair_map=None, r=10, weights=None, penalties=None, tier_map=None, A=None, B=None):
    scored = []
    for node in nodes:
        pr = node.pr
        if not Constr(pr):
            cost = 0
        else:
            if is_complete(pr):
                cost = 0
            else:
                # If A and B exist and current leaf event is in {A, B}, set cost=1
                # Otherwise, cost = 2 + Eval(...) + random
                # For demonstration (assuming we can identify an event in pr to compare to A,B):
                if A is not None and B is not None and event_in_AB(pr, A, B):
                    cost = 1
                else:
                    cost = 2 + Eval(pr, preference_map, pair_map, weights, penalties, tier_map) + random.randint(0, r)

        scored.append((cost, node))
    
    scored.sort(key=lambda x: x[0])
    return scored[0][1]


def ftrans(node):
    # ftrans logic:
    # If constr(pr)=false => (pr,no)
    # If no '?' remain => (pr,yes)
    # Else => (pr,?, b1,...,bn) from Altern

    pr = node.pr
    if not Constr(pr):
        node.sol = 'no'
    elif is_complete(pr):
        node.sol = 'yes'
    else:
        alts = Altern(pr)
        if len(alts) == 0:
            node.sol = 'no'
        else:
            node.children = alts
    return node


def get_leaves(nodes):
    # Return a list of all leaf nodes from a list of nodes (and their descendants)
    leaves = []
    stack = nodes[:]
    visited = set()
    while stack:
        n = stack.pop()
        if n not in visited:
            visited.add(n)
            if n.is_leaf():
                leaves.append(n)
            else:
                stack.extend(n.children)
    return leaves


def or_tree_search(pr, preference_map=None, pair_map=None, max_iter=1000):
    #  search:
    root = OrTreeNode(pr, '?')
    frontier = [root]

    for _ in range(max_iter):
        leaves = get_leaves(frontier)
        if not leaves:
            break
        leaf = fleaf(leaves, preference_map, pair_map, r=10, weights=weights, penalties=penalties, tier_map=tier_map)
        new_leaf = ftrans(leaf)
        if new_leaf.sol in ('yes', 'no'):
            if new_leaf.sol == 'yes':
                return new_leaf.pr
        else:
            frontier.extend(new_leaf.children)

    return None


################# STUB FUNCTIONS #################

def find_valid_game_assignments(pr, game_index):
    slots, games, practices = pr
    schedule = [games, practices, slots]

    valid_slots = find_possible_slots(game_index, schedule)

    return valid_slots


def find_valid_practice_assignments(pr, game_index, practice_index):
    slots, games, practices = pr
    schedule = [games, practices, slots]

    practice_event = (game_index, practice_index)
    valid_slots = find_possible_slots(practice_event, schedule)

    return valid_slots

def event_in_AB(pr, A, B):
    # Implement logic to determine if current pr involves events from A or B
    return False  # placeholder, implement your check here