import random
from main import GAME, GAME_TIME, PRAC, SLOT
from hardConstraints import assign, unassign
from softConstraints import eval_cost
from geneticAlgorithm import find_possible_slots


class OrTreeNode:
    def __init__(self, pr, sol="?", A=None, B=None, weights=None, penalties=None,
                 preference_map=None, pair_map=None, tier_map=None, r=10, children=None):
        """
        pr = (slots, games, practices)
        sol in { "?", "yes", "no" }
        A, B = optional parent solutions (Schedules) for bias in crossover
        weights, penalties, preference_map, pair_map, tier_map = environment parameters
        r = random bound (Random(0, r))
        children = list of OrTreeNodes (expansions)
        """
        self.pr = pr
        self.sol = sol
        self.A = A
        self.B = B
        self.weights = weights
        self.penalties = penalties
        self.preference_map = preference_map
        self.pair_map = pair_map
        self.tier_map = tier_map
        self.r = r
        self.children = children if children is not None else []

    def is_leaf(self):
        # Leaf if no children
        return len(self.children) == 0

    def haveParents(self):
        # Check if A and B (parent solutions) are set
        return self.A is not None and self.B is not None

    def isComplete(self):
        # Check if no {?} remain in games or practices
        slots, games, practices = self.pr
        for g in games:
            if g[GAME_TIME] == ():
                return False
        for gpr in practices:
            for p in gpr:
                if p == ():
                    return False
        return True

    # def constr(self):
        # If all assignments were made using 'assign', hard constraints should hold.
        # For now, we trust that invalid assignments are never made.
        # If a re-check is needed, we could implement a full constraint check here.
        # Return True if no known violation.
        # return True

    # might make the model more constrained towards one solution but we need something that works
    def next_unassigned_event(self):
        # Find the first event that is still '?'
        slots, games, practices = self.pr
        # Games first
        for i, g in enumerate(games):
            if g[GAME_TIME] == ():
                return i
        # Practices next
        for gi, gp in enumerate(practices):
            for pi, p in enumerate(gp):
                if p == ():
                    return (gi, pi)
        return None

    def event_in_parents(self, event):
        # Check if given event is in A or B similarly assigned.
        # event is either int (game id) or tuple (game_id, practice_id)
        if not self.haveParents():
            return False
        # Extract assignments from A and B and check if event is assigned similarly in them.
        # A and B are schedules: (slots, games, practices)
        # We can just check if they have a non-? assignment for this event.
        A_slots, A_games, A_practices = self.A
        B_slots, B_games, B_practices = self.B

        if isinstance(event, int):
            # Game
            return A_games[event][GAME_TIME] != () and A_games[event][GAME_TIME] == B_games[event][GAME_TIME]
        else:
            g, p = event
            return (A_practices[g][p] != () and A_practices[g][p] == B_practices[g][p])

    def fleaf(self):
        # According to the model:
        # 1. 0 if constr(pr) = false
        # if not self.constr():
        #     return 0

        # 2. 0 if no '?' remain (complete solution)
        if self.isComplete():
            return 0

        # 3. 1 if A and B are set and the next event is in both A and B
        next_event = self.next_unassigned_event()
        if self.haveParents() and self.event_in_parents(next_event):
            return 1

        # 4. 2 + Eval(pr) + Random(0, r)
        cost = eval_cost(self.pr, self.weights, self.penalties,
                         self.preference_map, self.pair_map, self.tier_map)
        return 2 + cost + random.randint(0, self.r)

    def ftrans(self):
        # According to the model:
        # 1. (pr, ?) -> (pr, no) if constr(pr)=false
        # if not self.constr():
        #     self.sol = "no"
        #     self.children = []
        #     return []

        # 2. (pr, ?) -> (pr, yes) if no '?' remain
        if self.isComplete():
            self.sol = "yes"
            self.children = []
            return []

        # 3. (pr, ?) -> (pr, ?, b1, ..., bn) otherwise
        # Expand the next event in all possible ways (Altern).
        next_event = self.next_unassigned_event()
        possible_slots = find_possible_slots(next_event, self.pr)

        if not possible_slots:
            # No possible assignment leads to a dead end
            self.sol = "no"
            self.children = []
            return []

        children = []
        slots, games, practices = self.pr

        for ps in possible_slots:
            # Copy the pr
            new_slots = [list(s)[:] for s in slots]
            new_games = [list(g) for g in games]
            new_practices = [list(row) for row in practices]

            new_pr = (new_slots, new_games, new_practices)
            if assign(next_event, ps, new_pr):
                child = OrTreeNode(
                    new_pr, "?",
                    A=self.A, B=self.B,
                    weights=self.weights,
                    penalties=self.penalties,
                    preference_map=self.preference_map,
                    pair_map=self.pair_map,
                    tier_map=self.tier_map,
                    r=self.r
                )
                children.append(child)
                # unassign is not needed on the copy since we made a copy
            else:
                # If can't assign, skip this alternative
                pass

        self.children = children
        return children

    def orTreeCrossover(self, A, B, pr):
        # If we have parent solutions A and B, we can pre-assign events that both parents agree on.
        A_slots, A_games, A_practices = A
        B_slots, B_games, B_practices = B
        slots, games, practices = pr

        # First assign events that A and B agree on for games
        for i in range(len(A_games)):
            if A_games[i][GAME_TIME] != () and A_games[i][GAME_TIME] == B_games[i][GAME_TIME]:
                assign(i, A_games[i][GAME_TIME], pr)

        # Assign events that A and B agree on for practices
        for gi in range(len(A_practices)):
            for pi in range(len(A_practices[gi])):
                if A_practices[gi][pi] != () and A_practices[gi][pi] == B_practices[gi][pi]:
                    assign((gi, pi), A_practices[gi][pi], pr)

        # for the remaining '?' events attempt to assign them from either A or B
        # try a random order: first attempt from one parent's assignment, if that fails attempt the other
        # If both fail or both have no assignment (()), leave as '?'

        # Handle games
        for i, g in enumerate(games):
            if g[GAME_TIME] == ():
                # This game is still '?'
                order = [A, B]
                random.shuffle(order)
                first_parent = order[0]
                second_parent = order[1]

                f_slots, f_games, f_prac = first_parent
                s_slots, s_games, s_prac = second_parent

                # Try first parent's assignment
                if f_games[i][GAME_TIME] != ():
                    if not assign(i, f_games[i][GAME_TIME], pr):
                        # Failed to assign from first parent, try second parent
                        if s_games[i][GAME_TIME] != ():
                            if not assign(i, s_games[i][GAME_TIME], pr):
                                # Also failed from second parent, leave as '?'
                                # No action needed, still '?'
                                pass
                        else:
                            # second parent's is also '?', leave as '?'
                            pass
                    # if we succeeded on first parent's assignment, nothing else to do
                else:
                    # first parent is '?', try second parent's assignment
                    if s_games[i][GAME_TIME] != ():
                        if not assign(i, s_games[i][GAME_TIME], pr):
                            # failed from second parent as well, leave as '?'
                            pass
                    else:
                        # both are '?', leave as '?'
                        pass

        # Handle practices
        for gi, gpr in enumerate(practices):
            for pi, p in enumerate(gpr):
                if p == ():
                    # This practice is still '?'
                    order = [A, B]
                    random.shuffle(order)
                    first_parent = order[0]
                    second_parent = order[1]

                    f_slots, f_games, f_prac = first_parent
                    s_slots, s_games, s_prac = second_parent

                    # Try first parent's assignment
                    if f_prac[gi][pi] != ():
                        if not assign((gi, pi), f_prac[gi][pi], pr):
                            # Failed, try second parent
                            if s_prac[gi][pi] != ():
                                if not assign((gi, pi), s_prac[gi][pi], pr):
                                    # fail again, leave as '?'
                                    pass
                            else:
                                # second parent is '?', leave as '?'
                                pass
                        # if succeeded, no action needed
                    else:
                        # first parent '?', try second parent
                        if s_prac[gi][pi] != ():
                            if not assign((gi, pi), s_prac[gi][pi], pr):
                                # fail, leave as '?'
                                pass
                        else:
                            # both '?'
                            pass
        return pr

    def runCrossoverSearch(self, A, B, max_depth=1000):
        """
        Given parents A and B:
        1. Use orTreeCrossover to pre-assign where possible.
        2. Continue filling the rest using the or-tree search.
        3. If search returns a complete schedule, return it.
        """
        # Pre-assign common elements using orTreeCrossover
        self.A = A
        self.B = B
        self.pr = self.orTreeCrossover(A, B, self.pr)

        # Check if the pre-assigned result is already complete
        if self.isComplete():
            # If crossover alone yielded a complete schedule, return it
            return self.pr

        # Continue filling the remaining '?' using or-tree search
        result = self.search(max_depth=max_depth)

        # Return the result of the search (either a complete schedule or None)
        return result

    def search(self, max_depth=1000, depth=0):
        # Perform a backtracking Or-tree search as defined:
        # Evaluate this node
        val = self.fleaf()
        if self.sol == "no":
            return None
        if self.sol == "yes":
            # return this solution
            return self.pr

        if depth > max_depth:
            return None

        # Not complete, expand
        children = self.ftrans()
        if not children:
            return None

        # Sort children by fleaf value
        scored_children = [(c.fleaf(), c) for c in children]
        random.shuffle(scored_children)  # to break ties randomly
        scored_children.sort(key=lambda x: x[0])

        for _, child in scored_children:
            result = child.search(max_depth, depth+1)
            if result is not None:
                return result
        return None
