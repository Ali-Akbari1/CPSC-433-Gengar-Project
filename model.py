import random
import copy

from main import GAME, PRAC, SLOT, GAME_TIME
from hardConstraints import assign, unassign
from softConstraints import eval_cost
from geneticAlgorithm import mutate, find_possible_slots
from main import print_schedule
from alternateOrTree import OrTreeNode


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
        # print("MODEL")
        # print(self.slots)
        # print(self.games)
        # print(self.practices)
        # print(self.preference_map)
        # print(self.pair_map)
        # print(self.tier_map)
        # print(self.weights)
        # print(self.penalties)

    def initialize_population(self):
        for _ in range(self.population_size):
            
            # Create a fresh problem representation (pr):
            # pr = (slots, games, practices)
            init_slots = copy.deepcopy(self.slots)
            init_games = copy.deepcopy(self.games)
            init_practices = copy.deepcopy(self.practices)
            pr = (init_games, init_practices, init_slots)

            # Use OrTreeNode search to fill all '?' events
            root = OrTreeNode(pr,
                              sol="?",
                              A=None, B=None,
                              weights=self.weights,
                              penalties=self.penalties,
                              preference_map=self.preference_map,
                              pair_map=self.pair_map,
                              tier_map=self.tier_map,
                              r=10)

            result = root.search(max_depth=self.max_iter)
            #print(result, "RESULT")
            # result is either None or a complete (slots, games, practices)
            if result is not None:
                #print("NOT NONE-------------------------------")
                # result = (slots, games, practices)
                self.population.append(result)
            else:
                # If no solution found, try again or accept fewer individuals.
                pass

    def evaluate_solution(self, schedule):
        # Use eval_cost to evaluate the schedule
        return eval_cost(schedule, self.weights, self.penalties, self.preference_map, self.pair_map, self.tier_map)

    def select_parents(self):
        # Evaluate all solutions
        scored = [(self.evaluate_solution(sched), sched)
                  for sched in self.population]
        scored.sort(key=lambda x: x[0])

        # Pick two best
        parentA = scored[0][1]
        parentB = scored[min(1, len(scored)-1)][1]
        return parentA, parentB

    def crossover(self, parentA, parentB):
        init_slots = copy.deepcopy(self.slots)
        init_games = copy.deepcopy(self.games)
        init_practices = copy.deepcopy(self.practices)
        pr = (init_games, init_practices, init_slots)

        # Create an OrTreeNode for crossover
        node = OrTreeNode(pr,
                          sol="?",
                          A=parentA,
                          B=parentB,
                          weights=self.weights,
                          penalties=self.penalties,
                          preference_map=self.preference_map,
                          pair_map=self.pair_map,
                          tier_map=self.tier_map,
                          r=10)

        # Run the crossover + search
        child = node.runCrossoverSearch(
            parentA, parentB, max_depth=self.max_iter)
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
            # If we don't have enough solutions, skip
            return

        parentA, parentB = self.select_parents()
        child = self.crossover(parentA, parentB)

        if child is not None:
            # Potentially mutate the child
            if random.random() < 0.2:  # mutation rate
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
        if scored:
            return scored[0][1]  # best solution
        else:
            return None

    def print_population(self, events=True, slots=False):
        for i, schedule in enumerate(self.population):
            print(
                f"--- Individual {i} (Score={self.evaluate_solution(schedule)}) ---")
            print_schedule(schedule, events=events, slots=slots)

    def find_best_schedule(self):

        if not self.population:
            print("Population is empty. No schedules to evaluate.")
            
            return None

        # Use the min function with evaluate_solution as the key to find the best schedule
        best_schedule = min(self.population, key=self.evaluate_solution)
        
        best_score = self.evaluate_solution(best_schedule)

        print(f"Best Schedule Found with Score: {best_score}")
        print_schedule(best_schedule, events=True, slots=True)

        return best_schedule
