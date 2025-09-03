from __future__ import annotations

import random

from .utils import lerp

from .consts import LIMIT, MIN_STEP, STEPS
from .game import Move, Node, Seminode, State


def random_cutoff() -> int:
    return random.randint(1, STEPS + 1) * MIN_STEP


class PartialStrategy:
    play: dict[Node, Move]
    cutoffs: list[int]

    def __init__(
        self, play: dict[Node, Move], cutoffs: list[int]
    ):
        self.play = play
        self.cutoffs = cutoffs

    @staticmethod
    def random(seminodes: list[Seminode]) -> PartialStrategy:
        play = {
            node: random.choice(node.moves)
            for seminode in seminodes
            for node, _ in seminode.links
            if node.moves
        }

        cutoffs = [-1, *(random_cutoff() for _ in range(1, 7))]

        return PartialStrategy(play, cutoffs)

    def breed(self, other: PartialStrategy) -> PartialStrategy:
        play = {
            node: self.play[node]
            if random.random() >= 0.5
            else other.play[node]  # random.choice((self.play[node], other.play[node]))
            for node in self.play
        }
        cutoffs = [-1] + [
            lerp(
                cutoff,
                other_cutoff,
                random.random(),
            )
            for cutoff, other_cutoff in zip(self.cutoffs, other.cutoffs)
        ]
        return PartialStrategy(play, cutoffs)

    def mutate(self) -> PartialStrategy:
        play = self.play.copy()
        cutoffs = self.cutoffs.copy()
        if random.random() >= 0.5:
            to_mutate = random.choice(list(play.keys()))
            play[to_mutate] = random.choice(to_mutate.moves)
        else:
            cutoffs[random.randint(1, 6)] = random_cutoff()
        return PartialStrategy(play, cutoffs)


class Strategy:
    strats: dict[State, PartialStrategy]

    def __init__(
        self,
        strats: dict[State, PartialStrategy] | None = None,
        seminodes: list[Seminode] | None = None,
    ):
        if strats is None:
            assert seminodes is not None
            self.strats = {
                State(home_score, away_score): PartialStrategy.random(seminodes)
                for home_score in range(0, LIMIT, MIN_STEP)
                for away_score in range(0, LIMIT, MIN_STEP)
            }
        else:
            self.strats = strats

    def breed(self, other: Strategy):
        return Strategy(
            {
                state: strat.breed(other.strats[state])
                for state, strat in self.strats.items()
            },
        )

    def mutate(self):
        return Strategy(
            {state: strat.mutate() for state, strat in self.strats.items()},
        )

    def play_round(self, state: State, seminodes: list[Seminode]) -> int:
        dice = 6
        score = 0
        strat = self.strats[state]
        while True:
            seed = random.random()
            for node, prob in seminodes[dice - 1].links:
                seed -= prob
                if seed <= 0:
                    break

            if node not in strat.play:
                return 0

            move = strat.play[node]
            score += move.score
            dice -= move.dice_consumed
            if dice == 0:
                dice = 6
            assert dice > 0
            if score >= strat.cutoffs[dice]:
                return score

    def play_single_game(self, other: Strategy, seminodes: list[Seminode]) -> bool:
        state = State(0, 0)

        while True:
            state.home += self.play_round(state, seminodes)
            if state.finished():
                return True
            state.away += other.play_round(state, seminodes)
            if state.finished():
                return False


    def compete(self, other: Strategy, seminodes: list[Seminode]):
        # tiebreaker
        score = random.randint(0, 1) - 0.5

        score += sum(self.play_single_game(other, seminodes) for _ in range(100))
        score -= sum(other.play_single_game(self, seminodes) for _ in range(100))
        return score > 0
