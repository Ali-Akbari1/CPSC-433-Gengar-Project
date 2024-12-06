import random
import copy

from main import GAME, PRAC, SLOT
from orTree import or_tree_search, OrTreeNode, Eval, Constr, is_complete
from geneticAlgorithm import mutate
from softConstraints import evaluate_schedule
from hardConstraints import assign, unassign
from main import print_schedule


class Model:

    def __init__(self, slots, games, practices, preference_map, pair_map, tier_map, weights, penalties, population_size=10, max_iter=1000):

        self.slots = slots
        self.games = games
        self.practices = practices

        self.preference_map = preference_map
        self.pair_map = pair_map
        self.tier_map = tier_map
        self.weights = weights
        self.penalties = penalties

        self.population_size = population_size
        self.max_iter = max_iter

        self.population = []

        self.initialize_population()

    def initialize_population(self):

        for _ in range(self.population_size):
            # Create a fresh problem representation (pr):
            # pr = (slots, games, practices)
            init_slots = copy.deepcopy(self.slots)
            init_games = copy.deepcopy(self.games)
            init_practices = copy.deepcopy(self.practices)
            pr = (init_slots, init_games, init_practices)

            # Use OR-Tree search to fill all '?' events
            result = or_tree_search(
                pr, self.preference_map, self.pair_map, self.max_iter)
            if result is not None:
                # result = (slots, games, practices)
                self.population.append(result)
            else:
                # If no solution found, try again, or break
                # For simplicity, if we fail to find population_size solutions, we proceed with fewer.
                pass

    def evaluate_solution(self, schedule):

        return evaluate_schedule(schedule, self.preference_map, self.pair_map)

    def select_parents(self):

        # Evaluate all solutions
        scored = [(self.evaluate_solution(sched), sched)
                  for sched in self.population]
        scored.sort(key=lambda x: x[0])

        # Simple approach: pick two best or top fraction
        parentA = scored[0][1]
        parentB = scored[min(1, len(scored)-1)][1]
        return parentA, parentB

    def crossover(self, parentA, parentB):

        init_slots = copy.deepcopy(self.slots)
        init_games = copy.deepcopy(self.games)
        init_practices = copy.deepcopy(self.practices)
        pr = (init_slots, init_games, init_practices)

        # Here we could incorporate a heuristic: for events that appear
        # in both parents similarly, pre-assign them. This isn't strictly

        # Perform an or-tree search. we need to modify or_tree_search to account
        # for parentA and parentB (e.g. preferences) - For now, we just call it as is.
        child = or_tree_search(pr, self.preference_map,
                               self.pair_map, self.max_iter)
        return child

    def run_generation(self):
        """
        Run one generation of the genetic process:
        1. Select parents
        2. Crossover to produce a child
        3. Possibly mutate the child
        4. Insert child into population, remove worst solution
        """

        if len(self.population) < 2:
            # If we don't have enough solutions skip
            return

        parentA, parentB = self.select_parents()
        child = self.crossover(parentA, parentB)

        if child is not None:
            # Potentially mutate the child
            if random.random() < 0.2:  # we can change this mutation rate as needed
                child = mutate(child, self.weights, self.penalties,
                               self.preference_map, self.pair_map, self.tier_map)

            # Add child to population
            self.population.append(child)
            # Remove worst solution to keep population size what we want
            scored = [(self.evaluate_solution(s), s) for s in self.population]
            scored.sort(key=lambda x: x[0])
            self.population = [x[1] for x in scored[:self.population_size]]

    def run_search(self, generations=50):

        for _ in range(generations):
            self.run_generation()

        # Return the best found solution
        scored = [(self.evaluate_solution(s), s) for s in self.population]
        scored.sort(key=lambda x: x[0])
        return scored[0][1]  # best solution

    def print_population(self, events=True, slots=False):

        for i, schedule in enumerate(self.population):
            print(
                f"--- Individual {i} (Score={self.evaluate_solution(schedule)}) ---")
            print_schedule(schedule, events=events, slots=slots)
