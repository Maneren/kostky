import itertools
from .strategy import Strategy
from .game import generate_all_nodes
import random
import pickle
import multiprocessing as mp

seminodes = generate_all_nodes()
POP_SIZE = 20
HALF_POP_SIZE = POP_SIZE // 2
QUARTER_POP_SIZE = POP_SIZE // 4


def select_better(a: Strategy, b: Strategy) -> Strategy:
    return a if a.compete(b) else b


def crossbreed_and_mutate(a: Strategy, b: Strategy) -> list[Strategy]:
    return [a.breed(b), b.breed(a).mutate(), a.breed(b), b.breed(a).mutate()]


population = list(
    itertools.starmap(Strategy, [(None, seminodes) for _ in range(POP_SIZE)])
)
print("Population created")

# for generation in range(1):
#     print(f"Generation {generation}")
#
#     random.shuffle(population)
#     print("Population shuffled")
#
#     # selection
#     parents = list(
#         itertools.starmap(
#             select_better, zip(population[:HALF_POP_SIZE], population[HALF_POP_SIZE:])
#         )
#     )
#     print("Parents selected")
#
#     # breed
#     new_population = [
#         child
#         for bunch in itertools.starmap(
#             crossbreed_and_mutate,
#             zip(parents[:QUARTER_POP_SIZE], parents[QUARTER_POP_SIZE:]),
#         )
#         for child in bunch
#     ]
#     print("Children bred")
#
#     # grow
#     population = new_population
#
#     if generation % 10 == 0:
#         with open(f"gen {generation}", "wb") as file:
#             pickle.dump(population, file)
#
#         # measure
#         print(
#             "average game length:",
#             sum(population[1].play_single_game(population[0])[1] for _ in range(20))
#             / 20,
#         )

with mp.Pool() as pool:
    population = pool.starmap(Strategy, [(None, seminodes) for _ in range(POP_SIZE)])
    print("Population created")

    for generation in range(10):
        print(f"Generation {generation}")

        random.shuffle(population)
        print("Population shuffled")

        # selection
        parents = pool.starmap(
            select_better, zip(population[:HALF_POP_SIZE], population[HALF_POP_SIZE:])
        )
        print("Parents selected")

        # breed
        new_population = [
            child
            for bunch in pool.starmap(
                crossbreed_and_mutate,
                zip(parents[:QUARTER_POP_SIZE], parents[QUARTER_POP_SIZE:]),
            )
            for child in bunch
        ]
        print("Children bred")

        population = new_population

        if generation % 10 == 0:
            with open(f"gen {generation}", "wb") as file:
                pickle.dump(population, file)

            # measure
            print(
                "average game length:",
                sum(population[1].play_single_game(population[0])[1] for _ in range(20))
                / 20,
            )
