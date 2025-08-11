import numpy as np
import sys
from dataclasses import dataclass
import functools
import itertools
from consts import LIMIT


@dataclass
class Move:
    score: int
    dice_consumed: int


@dataclass
class State:
    home: int
    away: int

    def __hash__(self):
        return int(self.home * 1000000 + self.away)

    def finished(self):
        return self.home >= LIMIT or self.away >= LIMIT

    def __repr__(self):
        return f"{self.home} {self.away}"


def get_score_by_roll(dice: list[int]) -> list[Move]:
    return score_by_rolls_sorted(tuple(sorted(dice)))


@functools.cache
def score_by_rolls_sorted(dice: list[int]) -> list[Move]:
    outputs = []
    rolls = {()}
    for n in dice:
        rolls |= {(*s, n) for s in rolls}

    for roll in rolls:
        if len(roll) == 0:
            continue
        move = score_dice_set(roll)
        if move is not None:
            outputs.append(move)
    return outputs


def score_dice_set(dice: tuple[int]) -> Move | None:
    by_type = np.zeros(6, int)
    for die in dice:
        by_type[die - 1] += 1

    score = 0

    score += 10 ** by_type[0]
    by_type[0] = 0
    if all(by_type[i] == 1 for i in range(6)):
        by_type[:] -= 1
        score += 1500

    score = 0
    if all(by_type[i] == 1 for i in range(1, 6)):
        by_type[1:6] -= 1
        score += 750

    if all(by_type[i] == 1 for i in range(0, 5)):
        by_type[0:5] -= 1
        score += 500

    for i in range(1, 6):
        if by_type[i] >= 3:
            score += (i + 1) * 10 ** (by_type[i] - 1)
            by_type[i] = 0

    if by_type[0] >= 3:
        score += 10 ** by_type[0]
        by_type[0] = 0

    score += by_type[0] * 100
    score += by_type[4] * 50
    by_type[0] = 0
    by_type[4] = 0
    if all(by_type == 0):
        return Move(score, len(dice))
    return None


class Node:
    def __init__(self, dice):
        self.dice = tuple(sorted(dice))
        self.moves = get_score_by_roll(dice)

    def __hash__(self):
        s = 0
        for i, v in enumerate(self.dice):
            s += v * 10**i
        return s

    def __str__(self):
        return "".join(map(str, self.dice))

    def __repr__(self):
        return "Node " + str(self)

    def __eq__(self, other):
        return hash(self) == hash(other)


@functools.cache
def factorial(x):
    if x < 0:
        raise ValueError("negative factorial!")
    if x == 0:
        return 1
    return factorial(x - 1) * x


class Seminode:
    def __init__(self, number_of_dice):
        self.number_of_dice = number_of_dice
        self.links = []

    def __hash__(self):
        return self.number_of_dice

    def generate_nodes(self):
        chance = factorial(self.number_of_dice) / 6**self.number_of_dice
        for dice in itertools.combinations_with_replacement(
            [1, 2, 3, 4, 5, 6], self.number_of_dice
        ):
            duplicates = 1
            for i in range(1, 7):
                duplicates *= factorial(dice.count(i))

            self.links.append((Node(dice), chance / duplicates))


def generate_all_nodes() -> tuple[list[Seminode], list[Node]]:
    seminodes = []
    all_nodes = []
    for length in range(1, 7):
        seminodes.append(Seminode(length))
        seminodes[-1].generate_nodes()
        all_nodes += [a[0] for a in seminodes[-1].links]

    print(
        f"Nodes have a total of {sum(len(node.moves) for node in all_nodes)} moves",
        file=sys.stderr,
    )
    return seminodes, all_nodes
