from collections import Counter
from .utils import dot_product, factorial, product
import numpy as np
import sys
from dataclasses import dataclass
import functools
import itertools
from .consts import DICE_COUNT, DICE_SIZE, LIMIT


@dataclass
class Move:
    score: int
    dice_consumed: int


@dataclass
class State:
    home: int
    away: int

    def __hash__(self):
        return int(self.home * 10**6 + self.away)

    def finished(self):
        return self.home >= LIMIT or self.away >= LIMIT

    def __repr__(self):
        return f"{self.home} {self.away}"


@functools.cache
def score_by_rolls_sorted(dice: tuple[int, ...]) -> list[Move]:
    rolls: set[tuple[int, ...]] = {()}
    for n in dice:
        rolls.update([(*s, n) for s in rolls])

    scores = (score_dice_set(roll) for roll in rolls if roll)

    return [score for score in scores if score is not None]


def score_dice_set(dice: tuple[int, ...]) -> Move | None:
    by_type = np.zeros(DICE_SIZE, np.uint)
    for die in dice:
        by_type[die - 1] += 1

    score = 0

    if all(by_type == 1):
        by_type[:] -= 1
        score += 1500

    if all(by_type[1:] == 1):
        by_type[1:] -= 1
        score += 750

    if all(by_type[:5] == 1):
        by_type[:5] -= 1
        score += 500

    for i in range(1, DICE_COUNT):
        count = by_type[i]
        die = i + 1
        if count >= 3:
            score += 100 * die * 2 ** (count - 3)
            by_type[i] = 0

    if by_type[0] >= 3:
        score += 1000 * 2 ** (by_type[0] - 3)
        by_type[0] = 0

    score += by_type[0] * 100
    score += by_type[4] * 50
    by_type[0] = 0
    by_type[4] = 0

    return Move(score, len(dice)) if all(by_type == 0) else None


class Node:
    HASH_VECTOR: list[int] = [DICE_SIZE**i for i in range(DICE_COUNT)]

    def __init__(self, dice):
        sorted_dice = tuple(sorted(dice))
        self.dice = sorted_dice
        self.moves = score_by_rolls_sorted(sorted_dice)
        self.hash = dot_product(sorted_dice, self.HASH_VECTOR)

    def __hash__(self):
        return self.hash

    def __str__(self):
        return "".join(map(str, self.dice))

    def __repr__(self):
        return f"Node {self}"

    def __eq__(self, other):
        return self.dice == other.dice


class Seminode:
    def __init__(self, number_of_dice: int):
        self.number_of_dice = number_of_dice

        chance: float = factorial(self.number_of_dice) / DICE_SIZE**self.number_of_dice
        self.links: list[tuple[Node, float]] = [
            (
                Node(dice),
                chance / product(map(factorial, Counter(dice).values())),
            )
            for dice in itertools.combinations_with_replacement(
                range(1, 7), self.number_of_dice
            )
        ]

    def __hash__(self):
        return self.number_of_dice


def generate_all_nodes() -> list[Seminode]:
    seminodes = [Seminode(length) for length in range(1, 7)]
    print(
        f"Nodes have a total of {sum(len(node.moves) for seminode in seminodes for node, _ in seminode.links)} moves",
        file=sys.stderr,
    )
    return seminodes
