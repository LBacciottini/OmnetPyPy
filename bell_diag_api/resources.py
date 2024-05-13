from bell_diag_api.dejmps import *
from bell_diag_api.utility import epr_pair
from functools import reduce


def compute_resources(target_fid, start_fid=None, initial_pair=None, eta=1, p_2=1):
    if start_fid is not None:
        initial_pair = epr_pair(start_fid, (1-start_fid)/3, (1-start_fid)/3, (1-start_fid)/3)
    else:
        start_fid = initial_pair.a
    reached_fidelity = start_fid
    pairs = [initial_pair]
    N_values = []
    iterations = 0
    while reached_fidelity < target_fid and iterations < 20:
        # print("Reached fidelity: " + str(reached_fidelity))
        # print("Current state:", pairs[-1])
        next_pair, N = dejmps(pairs[-1], pairs[-1], eta, p_2)
        pairs.append(next_pair)
        N_values += [N]
        reached_fidelity = next_pair.a
        iterations += 1

    if iterations == 20:
        return 100000000000, 100000000000

    res_list = [2/N for N in N_values]
    # multiply all elements in the list
    total_resources = reduce(lambda x, y: x*y, res_list)
    return total_resources, len(N_values)


def compute_resources_rounds(n_rounds, start_fid=None, initial_pair=None, eta=1, p_2=1):

    if start_fid is not None:
        initial_pair = epr_pair(start_fid, (1-start_fid)/3, (1-start_fid)/3, (1-start_fid)/3)
    else:
        start_fid = initial_pair.a
    reached_fidelity = start_fid
    pairs = [initial_pair]
    N_values = []
    iterations = 0
    while iterations < n_rounds:
        # print("Reached fidelity: " + str(reached_fidelity))
        # print("Current state:", pairs[-1])
        next_pair, N = dejmps(pairs[-1], pairs[-1], eta, p_2)
        pairs.append(next_pair)
        N_values += [N]
        reached_fidelity = next_pair.a
        iterations += 1

    res_list = [2/N for N in N_values]
    # multiply all elements in the list
    total_resources = reduce(lambda x, y: x*y, res_list)
    return total_resources, reached_fidelity, pairs[-1]


def distill_until(pair, target_fid, eta, p_2):
    reached_fidelity = pair.a
    iterations = 0
    while reached_fidelity < target_fid and iterations < 20:
        # print("Reached fidelity: " + str(reached_fidelity))
        # print("Current state:", pairs[-1])
        next_pair, N = dejmps(pair, pair, eta, p_2)
        pair = next_pair
        reached_fidelity = next_pair.a
        iterations += 1

    if iterations == 20:
        return 100000000000, 100000000000

    return pair, iterations