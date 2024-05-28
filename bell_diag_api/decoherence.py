"""
Implement decoherence noises on Bell-diagonal states
"""
import math

from bell_diag_api.utility import epr_pair


def depolarize(pair, p):
    # apply depolarizing noise to a Bell-diagonal pair
    a, b, c, d = pair
    return epr_pair((1-p)*a + p/4, (1-p)*b + p/4, (1-p)*c + p/4, (1-p)*d + p/4)


def depolarize_rate(pair, rate, time):
    # apply depolarizing noise to a Bell-diagonal pair
    p = 1 - math.e**(-rate*time)
    return depolarize(pair, p)


# test that the functions preserve the trace

def test_depolarize():
    # generate 100 different Bell-diagonal pairs
    a_values = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.995]
    pairs = [epr_pair(a, (1-a)/3, (1-a)/3, (1-a)/3) for a in a_values]
    p = 0.1
    for pair in pairs:
        new_pair = depolarize(pair, p)
        assert math.isclose(sum(new_pair), 1, rel_tol=1e-9), f"Pair {pair} was depolarized to {new_pair}"

