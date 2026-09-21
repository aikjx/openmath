"""Independent small convolution checks; run directly with Python."""
import random
from goldbach_directions import binary_convolution


def direct(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i+j] += x*y
    return out


def main():
    rng = random.Random(20260920)
    cases = [([0], [0]), ([1], [1]), ([1]*300, [1]*300),
             ([0, 0, 1, 1, 0, 1], [0, 0, 1, 1, 0, 1])]
    cases += [([rng.randrange(2) for _ in range(rng.randrange(1, 40))],
               [rng.randrange(2) for _ in range(rng.randrange(1, 40))])
              for _ in range(100)]
    for a, b in cases:
        assert binary_convolution(a, b) == direct(a, b)
    print('104 exact convolution checks passed, including carry boundary')


if __name__ == '__main__':
    main()
