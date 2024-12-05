import copy
import random

import main as m
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
    GAME, GAME_CODE, GAME_TIME, \
    PRAC, \
    SLOT, GAMX, GAMN, PRAX, PRAN, \
    EVENING_CONST, EVENING_BOUND

from hardConstraints import assign

##Need way to evaluate
from softConstraints import evaluate_schedule


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


def Constr(pr):

    #Checking for hard constraints
    (slots, games, practices) = pr

    # no slot max below 0

    for slot in slots: 
        if slot[0] < 0 or slot[2] < 0: #GAMX = 0, PRAX = 2 if indxing consistent
            return False
    return True

def Eval(pr, preference_map= None, pair_map= None):
    return evaluate_schedule(pr, preference_map, pair_map)


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


def Altern(pr):
    (slots, games, practices) = pr

    for gi, g in enumerate(games):
        if g[1] == ():
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
    possible_assignments = find_valid_practice_assignments(pr, game_index, practice_index)
    new_nodes = []
    for assignment in possible_assignments:
        new_pr = apply_assignment(pr, ('practice', game_index, practice_index), assignment)
        if Constr(new_pr):
            new_nodes.append(OrTreeNode(new_pr, '?'))
    return new_nodes


def apply_assignment(pr, event_key, slots_indices):
    # Apply the assignment to the given event in a copy of pr.
    # Reorder pr into [games, practices, slots] for assign()
    (slots, games, practices) = pr
    schedule = [games, practices, slots]
    success = assign(event_key, slots_indices, schedule)  # assumes assign returns True/False
    if success:
        # Update pr from schedule after assignment
        new_slots = schedule[2]
        new_games = schedule[0]
        new_practices = schedule[1]
        return (new_slots, new_games, new_practices)
    else:
        # if not successful, just return original pr (though ideally shouldn't happen if checked))
        return pr


def fleaf(nodes, preference_map=None, pair_map=None, r=10):
    # fleaf;; pick a leaf node to expand based on given criteria
    # 1) if Constr(pr)=false => cost=0
    # 2) if no '?' remain => cost=0
    # 3) if A,B environment vars set and event in {A,B}: cost=1 (not implemented here)
    # 4) else cost=2+Eval(pr)+Random(0,r)

    scored = []
    for node in nodes:
        pr = node.pr
        if not Constr(pr):
            cost = 0
        else:
            if is_complete(pr):
                cost = 0
            else:
                cost = 2 + Eval(pr, preference_map, pair_map) + random.randint(0, r)
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
        leaf = fleaf(leaves, preference_map, pair_map)
        new_leaf = ftrans(leaf)
        if new_leaf.sol in ('yes', 'no'):
            # ff yes or no, solution or dead end:
            if new_leaf.sol == 'yes':
                return new_leaf.pr
            # else just continue
        else:
            frontier.extend(new_leaf.children)

    return None


################# STUB FUNCTIONS #################
def find_valid_game_assignments(pr, game_index):
    # TODO: Implement logic based on your event alignment rules
    # Returning an empty list for now
    return []

def find_valid_practice_assignments(pr, game_index, practice_index):
    # TODO: Implement logic based on your event alignment rules
    # Returning an empty list for now
    return []