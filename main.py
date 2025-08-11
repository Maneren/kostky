from strategy import Strategy
from game import generate_all_nodes, Node, Seminode
import random
import pickle
import gc

# Get a list of all objects tracked by the garbage collector
all_objects = gc.get_objects()

print(f"Number of tracked objects: {len(all_objects)}")
seminodes, nodes = generate_all_nodes()
POP_SIZE = 40

population: list[Strategy] = [Strategy(None, nodes, seminodes) for _ in range(POP_SIZE)]
print("pop made")


for generation in range(200):
    parents = []
    new_population = []
    random.shuffle(population)

    # selection
    for a, b in zip(population[: POP_SIZE // 2], population[POP_SIZE // 2 :]):
        if a.compete(b):
            parents.append(a)
        else:
            parents.append(b)

    print(len(parents))
    # breed
    for a, b in zip(parents[: POP_SIZE // 4], parents[POP_SIZE // 4 :]):
        new_population.append(a.breed(b))
        new_population.append(b.breed(a).mutate())
        new_population.append(a.breed(b))
        new_population.append(b.breed(a).mutate())
    # ...

    # grow
    population = new_population

    all_objects = gc.get_objects()
    print(f"Number of tracked objects: {len(all_objects)}")
    del all_objects
    gc.collect()

    all_objects = gc.get_objects()
    print(f"Number of tracked left objects: {len(all_objects)}")
    del all_objects
    if generation % 10 == 0:
        with open(f"gen {generation}", "wb") as file:
            pickle.dump(population, file)

        # measure
        print(
            "average game length:",
            sum(population[1].play_single_game(population[0])[1] for _ in range(20))
            / 20,
        )
