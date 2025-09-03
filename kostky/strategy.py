from __future__ import annotations

import random

from .consts import LIMIT, MIN_STEP, STEPS
from .game import Move, Node, Seminode, State


def linear_interpolation(a, b, k):
    return a * (1 - k) + b * k


class PartialStrategy:
    play: dict[Node, Move]
    cutoffs: dict[int, int]

    def __init__(self, play: dict[Node, Move], cutoffs: dict[int, int]):
        self.play = play
        self.cutoffs = cutoffs

    @staticmethod
    def random(all_seminodes: list[Seminode]):
        play = {
            node: random.choice(node.moves)
            for seminode in all_seminodes
            for node, _ in seminode.links
            if node.moves
        }

        cutoffs = {
            seminode.number_of_dice: random.randint(1, STEPS + 1) * MIN_STEP
            for seminode in all_seminodes
        }

        return PartialStrategy(play, cutoffs)

    def breed(self, other: PartialStrategy):
        play = {
            node: random.choice((self.play[node], other.play[node]))
            for node in self.play
        }
        cutoffs = {
            number_of_dice: int(
                linear_interpolation(
                    self.cutoffs[number_of_dice],
                    other.cutoffs[number_of_dice],
                    random.random(),
                )
            )
            for number_of_dice in self.cutoffs
        }
        return PartialStrategy(play, cutoffs)

    def mutate(self):
        # mutate play
        play = self.play.copy()
        cutoffs = self.cutoffs.copy()
        if random.random() >= 0.5:
            to_mutate = random.choice(list(play.keys()))
            play[to_mutate] = random.choice(to_mutate.moves)
        else:
            to_mutate = random.randint(1, 6)
            cutoffs[to_mutate] = random.randint(1, STEPS + 1) * MIN_STEP
        return PartialStrategy(play, cutoffs)


class Strategy:
    strats: dict[State, PartialStrategy]
    all_seminodes: list[Seminode]

    def __init__(
        self,
        strats: dict[State, PartialStrategy] | None,
        all_seminodes: list[Seminode],
    ):
        if strats is None:
            self.strats = {
                State(home_score, away_score): PartialStrategy.random(all_seminodes)
                for home_score in range(0, LIMIT, MIN_STEP)
                for away_score in range(0, LIMIT, MIN_STEP)
            }
        else:
            self.strats = strats

        self.all_seminodes = all_seminodes

    def breed(self, other: Strategy):
        return Strategy(
            {
                state: strat.breed(other.strats[state])
                for state, strat in self.strats.items()
            },
            self.all_seminodes,
        )

    def mutate(self):
        return Strategy(
            {state: strat.mutate() for state, strat in self.strats.items()},
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
            if score >= strat.cutoffs[dice]:
                return score

    def play_single_game(self, other: Strategy) -> tuple[bool, int]:
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
