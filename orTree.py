import random 
import main as main
from main import HOURS_PER_DAY, SLOTS_PER_DAY, \
                GAME, GAME_CODE, GAME_TIME, \
                PRAC, \
                SLOT, GAMX, GAMN, PRAX, PRAN, \
                EVENING_CONST, EVENING_BOUND


class OrTreeNode:

    def __init__(self, pr, sol='?', children=None):
        self.solution = sool
        self.partial = pr
        self.children = children if children is not None else []
    
    def is_leaf(self):
        return len(self.children) == 0