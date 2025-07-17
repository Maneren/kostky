from __future__ import annotations
from dataclasses import dataclass
import functools
import itertools
import random
import numpy as np

LIMIT = 4000
MIN_STEP = 50


@dataclass
class Move:
    score: int
    dice_consumed: int


def get_score_by_roll(dice: list[int]) -> list[Move]:
    return score_by_rolls_sorted(tuple(sorted(dice)))


@functools.cache
def score_by_rolls_sorted(dice: list[int]) -> list[Move]:
    outputs = []
    rolls = [[]]
    for n in dice:
        rolls.extend([[*s, n] for s in rolls])

    for roll in rolls:
        if len(roll) == 0:
            continue
        move = score_dice_set(roll)
        if move is not None:
            outputs.append(move)
    return outputs


def score_dice_set(dice: list[int]) -> Move | None:
    by_type = np.zeros(6, int)
    for die in dice:
        by_type[die - 1] += 1

    score = 0

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
        return hash(str(self))

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

    def generate_nodes(self):
        chance = factorial(self.number_of_dice) / 6**self.number_of_dice
        for dice in itertools.combinations_with_replacement(
            [1, 2, 3, 4, 5, 6], self.number_of_dice
        ):
            duplicates = 1
            for i in range(1, 7):
                duplicates *= factorial(dice.count(i))

            self.links.append((Node(dice), chance / duplicates))


def play_out_game(
    seminodes: list[Seminode],
    strategy: dict[Node, int],
    cutoffs: list[int],
):
    # we have the following equation:
    # EV_this_link = a_1 * EV_1 + a_2 * EV_2 + a_3 * EV_3 ...
    # EV_this_link = a * EV (where a and EV are both vectors)
    #

    EV_by_points = [
        [i for i in range(0, LIMIT + MIN_STEP, MIN_STEP)] for _ in seminodes
    ]
    for j, points in reversed(list(enumerate(range(0, LIMIT, MIN_STEP)))):
        for i, seminode in enumerate(seminodes):
            # no longer play after cutoff
            if EV_by_points[i][j] >= cutoffs[i]:
                continue

            EV_by_points[i][j] = 0

            for link, prob in seminode.links:
                # no legal move => final score is 0
                if link not in strategy:
                    continue

                # there is a legal move
                move = link.moves[strategy[link]]
                new_dice_count = seminode.number_of_dice - move.dice_consumed
                if new_dice_count == 0:
                    new_dice_count = 6
                new_points = points + move.score

                if new_points >= LIMIT:
                    new_points = LIMIT

                EV_by_points[i][j] += (
                    EV_by_points[new_dice_count - 1][new_points // MIN_STEP] * prob
                )

    return EV_by_points


class Strategy:
    def __init__(self, all_nodes, seminodes):
        self.all_nodes = all_nodes
        self.seminodes = seminodes
        self.play = {
            node: random.randint(0, len(node.moves) - 1)
            for node in all_nodes
            if len(node.moves) > 0
        }
        self.cutoffs = [LIMIT for _ in seminodes]

    def calculate_cutoffs(self, i):
        a = [*self.cutoffs]
        a[i] = LIMIT
        table = play_out_game(self.seminodes, self.play, a)
        for j, value in table[i]:
            if value < j * MIN_STEP:
                self.cutoffs[i] = j * 50

    def calculate_play(self, node):
        max_value = 0
        max_index = 0
        for i in range(len(node.moves)):
            self.play[node] = i
            value = play_out_game(self.seminodes, self.play, self.cutoffs)
            if value[5][0] > max_value:
                max_index = i

        self.play[node] = max_index

    def advance(self):
        r = random.randint(0, len(self.play) + len(self.cutoffs) - 1)
        if r < len(self.cutoffs):
            self.calculate_cutoffs(r)
        else:
            self.calculate_play(list(self.play.keys())[r - len(self.cutoffs)])

    def get_EV(self):
        return play_out_game(self.seminodes, self.play, self.cutoffs)


def test_out_strat(strat, cutoffs):
    score = 0
    dice = 6
    while True:
        rolls = [random.randint(1, 6) for _ in range(dice)]
        node = Node(rolls)
        if len(node.moves) == 0:
            return 0
        move = node.moves[strat[node]]
        score += move.score
        dice -= move.dice_consumed
        if dice == 0:
            dice = 6
        if cutoffs[dice - 1] <= score:
            return score


def generate_all_nodes():
    seminodes = []
    all_nodes = []
    for length in range(1, 7):
        seminodes.append(Seminode(length))
        seminodes[-1].generate_nodes()
        all_nodes += [a[0] for a in seminodes[-1].links]

    return seminodes, all_nodes


if __name__ == "__main__":
    print(get_score_by_roll([1, 1, 3, 4]))
    s, a = generate_all_nodes()
    strat = Strategy(a, s)
    for _ in range(1000):
        strat.advance()
        if _ % 10 == 0:
            print(strat.get_EV()[0][0])
    print(test_out_strat(strat.play, strat.cutoffs))
