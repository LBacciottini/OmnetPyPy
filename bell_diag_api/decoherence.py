"""
Implement decoherence noises on Bell-diagonal states
"""
import math

from bell_diag_api.utility import epr_pair


def depolarize(pair, p):
    # apply depolarizing noise to a Bell-diagonal pair
    a, b, c, d = pair
    return epr_pair((1-p)*a + p/3, (1-p)*b + p/3, (1-p)*c + p/3, (1-p)*d + p/3)


def depolarize_rate(pair, rate, time):
    # apply depolarizing noise to a Bell-diagonal pair
    p = 1 - math.e**(-rate*time)
    return depolarize(pair, p)
