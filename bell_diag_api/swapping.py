from bell_diag_api.utility import epr_pair

__all__ = ['swap', 'get_max_num_swaps_werner', "swap_k_times", "concatenate_swaps", "get_max_num_swaps"]


def concatenate_swaps(initial_fid, num_swaps, eta, p_2):
    # compute the resulting fidelity after L swaps. We assume Werner states
    # as input, so the resulting state is also a Werner state
    return 0.25 + 0.75 * (p_2*(4*eta*eta - 1)/3)**(num_swaps) * ((4*initial_fid - 1)/3)**(num_swaps + 1)


def swap(pair_a, pair_b, eta, p_2):
    a_1, b_1, c_1, d_1 = pair_a
    a_2, b_2, c_2, d_2 = pair_b
    # compute the resulting pair after a swap. We assume Bell-diagonal states
    a_prime = p_2 * ( eta*eta * (a_1*a_2 + b_1*b_2 + c_1*c_2 + d_1*d_2) +
                      (1-eta)*(1-eta) * (a_1*b_2 + a_2*b_1 + c_1*d_2 + c_2*d_1) +
                      eta*(1-eta)*(a_1 + b_1)*(c_2 + d_2) + eta*(1-eta)*(a_2 + b_2)*(c_1 + d_1))  + (1-p_2)/4
    b_prime = p_2 * (eta*eta * (a_1*b_2 + a_2*b_1 + c_1*d_2 + c_2*d_1) +
                     (1-eta)*(1-eta) * (a_1*a_2 + b_1*b_2 + c_1*c_2 + d_1*d_2) +
                     eta*(1-eta) * (a_1 + b_1)*(c_2 + d_2) + eta*(1-eta) * (a_2 + b_2)*(c_1 + d_1)) + (1-p_2)/4
    c_prime = p_2 * (eta*eta * (a_1*c_2 + c_1*a_2 + b_1*d_2 + b_2*d_1) +
                     (1-eta)*(1-eta) * (a_1*d_2 + a_2*d_1 + b_1*c_2 + b_2*c_1) +
                     eta*(1-eta) * (a_1*a_2 + b_1*b_2 + c_1*c_2 + d_1*d_2 + a_1*b_2 + a_2*b_1 + c_1*d_2 + c_2*d_1)) + (1-p_2)/4
    d_prime = p_2 * (eta*eta * (a_1*d_2 + a_2*d_1 + b_1*c_2 + b_2*c_1) +
                     (1-eta)*(1-eta) * (a_1*c_2 + c_1*a_2 + b_1*d_2 + b_2*d_1) +
                     eta*(1-eta) * (a_1*a_2 + b_1*b_2 + c_1*c_2 + d_1*d_2 + a_1*b_2 + a_2*b_1 + c_1*d_2 + c_2*d_1)) + (1-p_2)/4
    return epr_pair(a_prime, b_prime, c_prime, d_prime)


def get_max_num_swaps_werner(initial_fid, target_fid, eta, p_2):
    # compute the maximum number of swaps needed to reach the target fidelity
    num_swaps = 1
    cur_fid = initial_fid
    while swap(initial_fid, num_swaps, eta, p_2) < target_fid:
        num_swaps += 1
    return num_swaps


def swap_k_times(initial_pair, num_swaps, eta, p_2):
    # compute the resulting pair after k swaps
    cur_pair = initial_pair
    for i in range(num_swaps):
        cur_pair = swap(cur_pair, initial_pair, eta, p_2)
    return cur_pair


def get_max_num_swaps(initial_pair, target_fid, eta, p_2):
    # compute the maximum number of swaps needed to reach the target fidelity
    num_swaps = 0
    cur_fid = initial_pair.a
    last_pair = initial_pair
    while last_pair.a >= target_fid:
        num_swaps += 1
        last_pair = swap_k_times(initial_pair, num_swaps, eta, p_2)
        # print("num_swaps: ", num_swaps, "last_pair.a: ", last_pair.a)
    return num_swaps - 1