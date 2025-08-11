from __future__ import annotations

import random

from consts import LIMIT, MIN_STEP, STEPS
from game import Move, Node, Seminode, State


def linear_interpolation(a, b, k):
    return a * (1 - k) + b * k


class PartialStrategy:
    def __init__(self, play: dict[Node, int], cutoffs: dict[Seminode, int]):
        self.play = play
        self.cutoffs = cutoffs

    @staticmethod
    def random(all_nodes: list[Node], all_seminodes: list[Seminode]):
        play = {
            node: random.randint(0, len(node.moves) - 1)
            for node in all_nodes
            if len(node.moves) > 0
        }

        cutoffs = {
            seminode: random.randint(1, STEPS + 1) * MIN_STEP
            for seminode in all_seminodes
        }

        return PartialStrategy(play, cutoffs)

    def breed(self, other: PartialStrategy):
        play = {
            node: random.choice([self.play[node], other.play[node]])
            for node in self.play
        }
        cutoffs = {
            seminode: int(
                linear_interpolation(
                    self.cutoffs[seminode], other.cutoffs[seminode], random.random()
                )
            )
            for seminode in self.cutoffs
        }
        return PartialStrategy(play, cutoffs)

    def mutate(self):
        # mutate play
        play = {**self.play}
        cutoffs = {**self.cutoffs}
        if random.random() >= 0.5:
            to_mutate = random.choice(list(play.keys()))
            play[to_mutate] = random.randint(0, len(to_mutate.moves) - 1)
        else:
            to_mutate = random.choice(list(cutoffs.keys()))
            cutoffs[to_mutate] = random.randint(1, STEPS + 1) * MIN_STEP
        return PartialStrategy(play, cutoffs)


class Strategy:
    def __init__(
        self,
        strats: dict[State, PartialStrategy] | None,
        all_nodes: list[Node],
        all_seminodes: list[Seminode],
    ):
        if strats is None:
            self.strats = {
                State(home_score, away_score): PartialStrategy.random(
                    all_nodes, all_seminodes
                )
                for home_score in range(0, LIMIT, MIN_STEP)
                for away_score in range(0, LIMIT, MIN_STEP)
            }
        else:
            self.strats = strats
        self.all_nodes = all_nodes
        self.all_seminodes: list[Seminode] = all_seminodes

    def breed(self, other):
        return Strategy(
            {
                state: self.strats[state].breed(other.strats[state])
                for state in self.strats
            },
            self.all_nodes,
            self.all_seminodes,
        )

    def __del__(self):
        for strat in self.strats.values():
            del strat

    def mutate(self):
        return Strategy(
            {state: self.strats[state].mutate() for state in self.strats},
            self.all_nodes,
            self.all_seminodes,
        )

    def play_round(self, state: State) -> int:
        dice = 5
        score = 0
        strat = self.strats[state]
        while True:
            seed = random.random()
            for node, prob in self.all_seminodes[dice].links:
                seed -= prob
                if seed <= 0:
                    break

            if node not in strat.play:
                return 0

            move: Move = node.moves[strat.play[node]]
            score += move.score
            dice -= move.dice_consumed
            if dice == -1:
                dice = 5
            assert dice >= 0
            if score >= strat.cutoffs[self.all_seminodes[dice]]:
                return score

    def play_single_game(self, other: Strategy):
        state = State(0, 0)

        rounds = 1
        while True:
            state.home += self.play_round(state)
            if state.finished():
                return True, rounds
            state.away += other.play_round(state)
            if state.finished():
                return False, rounds

            rounds += 1

    def compete(self, other: Strategy):
        # tiebreaker
        score = random.randint(0, 1) - 0.5

        score += sum(self.play_single_game(other)[0] for _ in range(100))
        score -= sum(other.play_single_game(self)[0] for _ in range(100))
        return score > 0
