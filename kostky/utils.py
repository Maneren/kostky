import functools
from math import floor
from operator import mul
from typing import Iterable


@functools.cache
def factorial(x):
    if x < 0:
        raise ValueError("negative factorial!")

    return 1 if x == 0 else factorial(x - 1) * x


def product(iterable: Iterable[int]) -> int:
    return functools.reduce(mul, iterable)


def dot_product(a: Iterable[int], b: Iterable[int]) -> int:
    return sum(x * y for x, y in zip(a, b))


def lerp(a: int, b: int, k: float) -> int:
    return floor(a * (1 - k) + b * k)


def split_in_half[T](list: list[T]) -> tuple[list[T], list[T]]:
    return list[: len(list) // 2], list[len(list) // 2 :]
