import random
from main import GAME, GAME_TIME, PRAC, SLOT
from hardConstraints import assign, unassign
from softConstraints import eval_cost
from geneticAlgorithm import find_possible_slots


class OrTreeNode:
    def __init__(self, pr, sol="?", A=None, B=None, weights=None, penalties=None,
                 preference_map=None, pair_map=None, tier_map=None, r=10, children=None):
        """
        update pr
        pr = (games, practices, slots)
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
        # leaf off if no children
         return len(self.children) == 0

    def haveParents(self):
        # check if A and B (parent solutions) are set
        return self.A is not None and self.B is not None

    def isComplete(self):
        # Check if there is no {?} remain in games or practices
        games, practices, slots = self.pr

        for g in games:
            if g[GAME_TIME] == ():
                 return False

        for gpr in practices:
            for p in gpr:

                if p == ():
                     return False
        return True

    # might make the model more constrained towards one solution but we need something that works
    def next_unassigned_event(self):
        # Find the first event that is still '?'
        games, practices, slots = self.pr
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
        # check if given event is in A or B similarly assigned
        # event is either int (game id ) or tuple ( game_id, practice_id)
        if not self.haveParents():
            return False
        # get the assignments from A and B and check if event is assigned similarly in them
        # A and B are schedules: (slots, games, practices)
        # We can just check if they have a non? assignment for this targeted event
        
        A_games, A_practices, A_slots = self.A
        B_games, B_practices, B_slots = self.B

        if isinstance(event, int):
            #the Game
             return A_games[event][GAME_TIME] != () and A_games[event][GAME_TIME] == B_games[event][GAME_TIME]
        else:
            
            g, p = event
            
            return ( A_practices[g][p] != () and A_practices[g][p] == B_practices[g][p])

    def fleaf(self):
        # based off model, 
        # 1. 0 if constr(pr) = false
        # if not self.constr():
        #     return 0
        # 2. 0 if no '?' remain (complete solution)

        if self.isComplete():
            return 0

        # 3. 1 if A and B are set and the next event is in both A and B
        next_event = self.next_unassigned_event( )
        if self.haveParents() and self.event_in_parents(next_event):
            return 1

        # 4. 2 + Eval(pr) + Random(0, r)
        cost = eval_cost(self.pr, self.weights, self.penalties, self.preference_map, self.pair_map, self.tier_map )
        return 2 + cost + random.randint(0, self.r)

    def ftrans(self):
        # 1. (pr, ?) -> (pr, no) if constr(pr)=false
        # if not self.constr():
        #    self.sol = "no"
        #    self.children = []
        #    return []

        # 2. (pr, ?) -> (pr, yes) if no '?' remain
        if self.isComplete():

            self.sol = "yes"
            self.children = []
            return []

        # 3. (pr, ?) -> (pr, ?, b1, ..., bn) otherwise
        #expand the next event in all possible ways (Altern).
        next_event = self.next_unassigned_event()
        possible_slots = find_possible_slots(next_event, self.pr)

        if not possible_slots:
            #no possible assignment and it leads to a dead end
            self.sol = "no"
            self.children = []
            return []

        children = []
        games, practices, slots = self.pr

        for ps in possible_slots:
            
            # Copy the pr
            new_slots = [list(s)[:] for s in slots]
            
            new_games = [list(g) for g in games]
            
            new_practices = [list(row) for row in practices]

            new_pr = (new_games, new_practices, new_slots)
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
                # If we can't assign, skip this alternative
                pass

        self.children =  children
        
        return children

    def orTreeCrossover(self, A, B, pr):
        games, practices, slots = pr
        
        # unpack the parent schedules
        A_games, A_practices, A_slots = A
        B_games, B_practices, B_slots = B

        # Assign events that both parents agree on for games
        for i in range(len(games)):
            if i >= len(A_games) or i >= len(B_games):
                continue

            if A_games[i][GAME_TIME] != () and A_games[i][GAME_TIME] == B_games[i][GAME_TIME]:
                assign(i, A_games[i][GAME_TIME], pr )

        # Assign events that both parents agree on for practices
        for gi in range(len(practices )):

            for pi in range(len(practices[gi])):
                if gi >= len(
                    A_practices ) or gi >= len(B_practices):
                    continue
                if pi >= len(A_practices[gi]) or pi >= len(B_practices[gi]):
                    continue

                if A_practices[gi][pi] != () and A_practices[gi][pi] == B_practices[gi][pi]:
                    assign((gi, pi), A_practices[gi][pi], pr)

        # Handle remaining '?' events
        # Handle games

        for i, g in enumerate(games):
            if g[GAME_TIME] == ():
                # This game is still '?'
                order = [A, B]
                random.shuffle(order)
                first_parent = order[0]
                second_parent = order[1]

                f_games, f_prac, f_slots = first_parent
                s_games, s_prac, s_slots = second_parent

                # Try first parent's assignment
                if i < len(f_games) and f_games[i][GAME_TIME] != ():
                    if not assign(i, f_games[i][GAME_TIME], pr):
                        # Failed to assign from first parent, try second parent
                        if i < len(s_games) and s_games[i][GAME_TIME] != ():
                            if not assign(i, s_games[i][GAME_TIME], pr):
                                pass  # Both parents failed to assign
                else:
                    # first parent is '?', try second parent's assignment
                    if i < len(s_games) and s_games[i][GAME_TIME] != ():
                        if not assign(i, s_games[i][GAME_TIME], pr):
                            pass  # Both parents failed to assign
                    else:
                        pass  # Both parents have '?', leave as '?'

        # Handle practices
        for gi, gpr in enumerate(practices):
            for pi, p in enumerate(gpr):
                if p == ():
                    # This practice is still '?'
                    order = [A, B]

                    random.shuffle(order )
                    first_parent = order[0]
                    second_parent = order[1]

                    f_games, f_prac, f_slots = first_parent
                    s_games, s_prac, s_slots = second_parent

                    # Try first parent's assignment
                    if gi < len(f_prac ) and pi < len(f_prac[gi] ) and f_prac[gi][pi] != ():
                        if not assign((gi, pi), f_prac[gi][pi], pr):
                            # Failed, try second parent
                            if gi < len(s_prac) and pi < len( s_prac[gi]) and s_prac[gi][pi] != ():
                                if not assign((gi, pi), s_prac[gi][pi], pr):
                                    pass  # Both parents failed to assign
                    else:
                        # first parent '?', try second parent's assignment
                        if gi < len(s_prac) and pi < len(s_prac[gi]) and s_prac[gi][pi] != ():
                            if not assign((gi, pi), s_prac[gi][pi], pr):
                                pass  # this means both parents failed to assign
                        else:
                            pass  # this means both parents have '?', leave as '?'

        return pr

    def runCrossoverSearch(self, A, B, max_depth=1000):
        """
        Given parents A and B:
        1. we must use orTreeCrossover to pre-assign where possible
        2. Continue filling the rest using the or-tree search
        3. if search returns a complete schedule, return it.
        """
        # Pre-assign common elements using orTreeCrossover
        self.A = A
        self.B = B
        self.pr = self.orTreeCrossover(A, B, self.pr)

        # Check if the pre-assigned result is already complete
        if self.isComplete():
            # If crossover alone gave a complete schedule, return it
            
            return self.pr

        # Continue filling the remaining '?' using the or-tree search
        result = self.search(max_depth=max_depth)

        # Return the result of the search (either a complete schedule or None)
        return result

    def search(self, max_depth=1000, depth=0):
        # Perform a backtracking Or-tree search defined;
        # Evaluate this node

        if self.sol == "no":
            return None
        
        if self.sol == "yes":
            # return this solution
            return self.pr

        if depth > max_depth:
             return None

         # Not complete, expand
        children = self.ftrans()
        
        # **New Check After ftrans**
        if self.sol == "yes":

            return self.pr

        if not children:

            return None

        # Sort children by fleaf value
        scored_children = [(c.fleaf(), c) for c in children]
        random.shuffle(scored_children)  # to break ties randomly
        scored_children.sort(key=lambda x: x[0])

        for _, child in scored_children:
            result = child.search(max_depth, depth+1 )
            
            if result is not None:
                return result
        return None


# # ------------------------------------
# #         TEST CODE SECTION
# # ------------------------------------
# #  Below is an example test setup. 

# if __name__ == "__main__":
#     # small test scenario for demonstration:
#     # Remember our pr is now changed to = (games, practices, slots)
#     # Each game or practice time is first set to (), indicating unassigned
#     # GAME_TIME is an index used by the schedule structure (from main import GAME_TIME)

#     # Herew we have some mock data (these are just example formats, adapt as per your actual usage):
#     
# 
#     # Suppose a game is structured like: [GAME_ID, GAME_TIME]
#     # and a practice is structured like: [PRACTICE_TIME], etc.
#     test_games = [[ 0, ()], [ 1, ()]]  # Two games, times unassigned
#     test_practices = [
#         [(), ()],  # first team's two practices unassigned,
#         [()]        # Second team, one practice unassigned
#     ]
#     test_slots = [
#         [1, 1, 1, 1],  # slot index 0
#         [1, 1, 1, 1],  # slot index 1  (using short examples)
#     ]
#   # simple slot structure (one day, three possible slot indices)

#     pr = (test_games, test_practices, test_slots) new structuce of pr
#     node = OrTreeNode(
#         pr, 
#         weights=[1, 1, 1, 1], 
#         penalties=[1, 1, 1, 1],
#         preference_map={},  # empty dict if you have no preferences
#         
#         pair_map={},        # empty dict to avoid NoneType errors
#         tier_map={}
#     )


#     # --- Testing each method invdividually ---
#     # 1. Test is_leaf()
#     # should see "True" since no children initially.
#     print("Testing is_leaf:")
#     print(node.is_leaf())  # Expect True

#     # 2. Test haveParents()
#     # should Expect False, since A and B not set
#     print("Testing haveParents:")
#     print(node.haveParents())  # Expect False

#     # 3. Test isComplete()
#     # All the events are unassigned, so expect False
#     print("Testing isComplete:")
#     print(node.isComplete())  # Expect False

#     # 4. Test next_unassigned_event()
#     # Should return the index of the first unassigned game, which is 0
#     print("Testing next_unassigned_event:")
#     print(node.next_unassigned_event())  # Expect 0 (the first game is unassigned)

#     # 5. Test event_in_parents()
#     # No parents in a set, so should return False
#     print("Testing event_in_parents with event=0:")
#     print(node.event_in_parents(0))  # Expect False

#     # 6. Test fleaf()
#     # not fully complete, no parents, so fleaf = 2 + cost + random(0, r)
#     # cost likely 0 if no constraints. Expect something >= 2.
#     print("Testing fleaf:")
#     print(node.fleaf())  # Expect an integer >= 2

#     # 7. Test ftrans() 
#     # here we arent using actual constraints and slot assignment logic from other modules,
#     # we may not get meaningful children, If find_possible_slots returns no possibilities,
#     # we get "no" solution. For a real test, find_possible_slots would need proper mock data.
#     # For now, just run it to see it doesn't crash:
#     print("Testing ftrans:")
#     children = node.ftrans()
#     print("Number of children:", len(children))
#     # we're expecting either 0 (if no slot assignments possible) or more.

#     # 8. Test orTreeCrossover()
#     # We need two parent schedules A and B. We'll just mock them as well:
#     A = (
#         [[0, (0,1)], [1, ()]],  # Two games: Game 0 assigned to slots 0,1; Game 1 unassigned
#         [[ (1,), ()], [()]],      # Two practices: Team 0 has 2 practices, Team 1 has 1 practice
#         
#           [
#             [1,1,1,1], [1,1,1,1], [1,1,1,1], [1,1,1,1],
#             
#             [1,1,1,1], [1,1,1,1], [1,1,1,1], [1,1,1,1]
#         ]  # 8 slot lists matching pr's new slots
#     )

#     B = (
#         [[0, (0,1)], [1, ()]],  # Two games: Game 0 assigned to slots 0,1 : Game 1 unassigned
#         [[(1,), ()], [()]],      # Two practices: Team 0 has 2 practices, Team 1 has 1 practice
#         [
#             [1,1,1,1], [1,1,1,1], [1,1,1,1], [1,1,1,1],
#             
#             [1,1,1,1], [1,1,1,1], [1,1,1,1], [1,1,1,1]
#         ]  # 8 slot lists matching pr's slots
#     )  # Identical to A for ease of test
 
#     node.A = A
#     node.B = B
#     node.orTreeCrossover(A, B, pr)
#     # If A and B agree on assignment/task, pr might now be partially assigned.
#     print("Testing orTreeCrossover - pr after crossover:")
#     print(node.pr)  # Expect some assignments now set

#     # 9. Test runCrossoverSearch()
#     # With mock data not set up completley, this may not produce a complete schedule,
#     # we can still run it to verify no errors:
#     print("Testing runCrossoverSearch:")
#     result = node.runCrossoverSearch(A, B)
#     print("Crossover search result:", result)
#     # Expect either a completed schedule or None, depending on data.

#     # 10. Test search()
#     # similarly note as above, If data or constraints are not set for a solvable scenario,
#     print("Testing search:")
#     search_result = node.search()
#     print("Search result:", search_result)
#     # Expect None or a schedule if possible

