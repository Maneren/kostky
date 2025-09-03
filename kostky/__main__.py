import gc

from .utils import split_in_half
from .strategy import Strategy
from .game import generate_all_nodes
import random
import pickle
import multiprocessing as mp

seminodes = generate_all_nodes()
POP_SIZE = 128
HALF_POP_SIZE = POP_SIZE // 2
QUARTER_POP_SIZE = POP_SIZE // 4


def select_better_strategy(a: Strategy, b: Strategy) -> Strategy:
    return a if a.compete(b, seminodes) else b


def crossbreed_and_mutate(a: Strategy, b: Strategy) -> list[Strategy]:
    return [a.breed(b), b.breed(a).mutate(), a.breed(b), b.breed(a).mutate()]


with mp.Pool(8) as pool:
    population = pool.starmap(Strategy, [(None, seminodes) for _ in range(POP_SIZE)])
    print("Population created")

    for generation in range(51):
        print(f"Generation {generation}")

        random.shuffle(population)
        print("Population shuffled")

        # selection
        parents = pool.starmap(
            select_better_strategy,
            zip(*split_in_half(population)),
        )
        print("Parents selected")

        random.shuffle(parents)
        print("Parents shuffled")

        # breed
        child_groups = pool.starmap(
            crossbreed_and_mutate,
            zip(*split_in_half(parents)),
        )
        print("Children bred")

        population = [child for group in child_groups for child in group]
        print("New generation created")

        print(f"Garbage collected: {gc.collect()}")

        if (generation + 1) % 10 == 0:
            with open(f"gen {generation}", "wb") as file:
                pickle.dump(population, file)

            # measure
            print(
                "average game length:",
                sum(population[1].play_single_game(population[0])[1] for _ in range(20))
                / 20,
            )
