# This is a sample Python script.
from matplotlib import pyplot as plt

from scipy.optimize import minimize, LinearConstraint

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from dejmps import *
from utility import epr_pair
from swapping import *
from resources import *
import numpy as np

def get_data(starting_fid, target_fid):
    initial_pair = epr_pair(starting_fid, 0, (1-starting_fid), 0)
    eta = 1
    p_2 = 0.97
    reached_fidelity = starting_fid
    pairs = [initial_pair]
    while reached_fidelity < target_fid:
        print("Reached fidelity: " + str(reached_fidelity))
        print("Current state:", pairs[-1])
        next_pair, N = dejmps(pairs[-1], pairs[-1], eta, p_2)
        pairs.append(next_pair)
        reached_fidelity = next_pair.a

    return pairs

def plot_data(pairs):
    """
    Plot the data as a curve where on the x-axis we have the index of the pair and on the y-axis we have the fidelity,
    i.e. its "a" field.
    """
    x = range(len(pairs))
    y = [pair.a for pair in pairs]
    plt.xlabel("Number of iterations")
    plt.ylabel("Fidelity")
    # set an x-ticks every 1 iterations
    plt.xticks(range(0, len(pairs), 1))
    # mark each point with a dot
    plt.plot(x, y, '-')
    plt.plot(x, y, 'o')

    # put a grid for better readability
    plt.grid(True)

    plt.show()

def get_cost_per_link(x, eta, p_2):
    target_fid = x[0]
    min_fid = x[1]
    # print(x, eta, p_2)
    if min_fid >= target_fid:
        return 1000000000
    if min_fid >= 1 or target_fid >= 1 or min_fid <= 0.5 or target_fid <= 0.5:
        return 1000000000
    return get_efficiency(target_fid, min_fid, start_fid=target_fid, eta=eta, p_2=p_2)

def get_optimal_fidelities(eta, p_2):
    # create an array of 2-element arrays, each containing the initial guess for the optimization.
    # the first element is the target fidelity, the second is the minimum fidelity
    # sample the guesses in the multi-interval [0.5, 1]x[0.5, 1]
    guesses = [0.5001, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, 0.675, 0.7, 0.725, 0.75, 0.775, 0.8, 0.825, 0.85, 0.875, 0.9, 0.925, 0.95, 0.975, 0.9999]
    guesses_cpy = guesses.copy()
    initial_guesses = []
    for i, guess in enumerate(guesses):
        for j in range(i+1, len(guesses_cpy)):
            initial_guesses.append([guesses_cpy[j], guess])
    # print(initial_guesses)
    current_best = None
    # set a constraint for x[0] > x[1] using LinearConstraint, and also impose that 0.5<x[0]<=1 and 0.5<x[1]<=1
    cons = LinearConstraint([[1, -1], [0, 1], [1, 0]], [0, 0.5001, 0.5001], [np.inf, 1, 1])
    for guess in initial_guesses:
        # print("Trying guess:", guess)
        # print(get_cost_per_swap(guess, eta, p_2))
        res = minimize(get_cost_per_link, x0=guess, args=(eta, p_2), constraints=cons, method='SLSQP')
        if current_best is None or res.fun < current_best.fun or (res.fun == current_best.fun and res.x[0] > current_best.x[0]):
            current_best = res
            # print("New best:", current_best)
    # print("I AM OUT OF HERE")
    res = current_best
    pair = epr_pair(res.x[0], (1 - res.x[0]) / 3, (1 - res.x[0]) / 3, (1 - res.x[0]) / 3)
    L = get_max_num_swaps(pair, target_fid=res.x[1], eta=eta, p_2=p_2)
    swapped_pair = swap_k_times(pair, L, eta, p_2)
    resources, purif_rounds = compute_resources(target_fid=res.x[0], initial_pair=swapped_pair, eta=eta, p_2=p_2)
    res["L"] = L
    res["K"] = purif_rounds
    res["resources"] = resources

    return res

def l_swaps_k_dejmps(initial_pair, l, k, eta, p_2):
    """
    Perform l swaps followed by k dejmps operations on the initial pair.
    """
    pair = initial_pair
    pair = swap_k_times(pair, l, eta, p_2)
    print("After " + str(l) + " swaps:", pair)
    for i in range(k):
        pair = dejmps(pair, pair, eta, p_2)[0]
    return pair

def plot_optimization():
    etas = np.arange(0.9875, 1., 0.00125)
    print(etas)
    results = [get_optimal_fidelities(etas[i], etas[i]) for i in range(len(etas))]

    # we plot the results as a dotted line where on the x-axis we have the eta value and on the y-axis we have the
    # "fun" value of the optimization, i.e. the number of EPR pairs needed on average for each swap operation
    x = etas
    y = [res.fun for res in results]
    plt.xlabel("Eta (CNOT and MEAS accuracy)")
    plt.ylabel("Resources [pairs/link]")
    # set an x-ticks every 1 iterations
    plt.xticks(np.arange(0.9875, 1., 0.00125))
    # mark each point with a dot
    plt.plot(x, y, '-')
    plt.plot(x, y, 'o')
    # put a grid for better readability
    plt.grid(True)
    # on each dot we write L and K
    for i in range(len(results)):
        plt.annotate("L=" + str(results[i]["L"]) + ", K=" + str(results[i]["K"]) + ", F_w=" + str(results[i].x[0]),
                     (x[i], y[i]))
    # set plot title
    plt.title("Resources per link as a function of quantum noise")

    # set the plot width so that the x labels do not overlap
    plt.gcf().autofmt_xdate()

    plt.show()


def get_minimum_initial_fidelity(eta, p_2):
    """
    Applies a binary search on the initial fidelity to find
    the minimum initial fidelity (in interval ]0.5, 1[) so that DEJMPS gives a positive
    fidelity gain, with a precision of 0.01.
    """
    # initial fidelity bounds
    min_fid = 0.5
    max_fid = 0.75
    # precision
    prec = 0.01

    # while the bounds are not close enough
    while abs(max_fid - min_fid) > prec:
        # compute the fidelity for the middle point
        mid_fid = (min_fid + max_fid) / 2
        initial_pair = epr_pair(a=mid_fid, b=(1 - mid_fid) / 3, c=(1 - mid_fid) / 3, d=(1 - mid_fid) / 3)
        pair = dejmps(initial_pair, initial_pair, eta, p_2)[0]
        mid_fid_dejmps = pair.a
        # if the fidelity is negative, we update the lower bound
        if mid_fid_dejmps <= mid_fid:
            min_fid = mid_fid
        # otherwise we update the upper bound
        else:
            max_fid = mid_fid

    return max_fid

def get_maximum_initial_fidelities(eta, p_2):
    """
    Applies a binary search on the initial fidelity to find
    the maximum initial fidelity (in interval ]0.5, 1[) so that DEJMPS gives a positive
    fidelity gain, with a precision of 0.01.
    """
    # initial fidelity bounds
    min_fid = 0.75
    max_fid = 1
    # precision
    prec = 0.01

    # while the bounds are not close enough
    while abs(max_fid - min_fid) > prec:
        # compute the fidelity for the middle point
        mid_fid = (min_fid + max_fid) / 2
        initial_pair = epr_pair(a=mid_fid, b=(1 - mid_fid) / 3, c=(1 - mid_fid) / 3, d=(1 - mid_fid) / 3)
        pair = dejmps(initial_pair, initial_pair, eta, p_2)[0]
        mid_fid_dejmps = pair.a
        # if the fidelity is negative, we update the lower bound
        if mid_fid_dejmps <= mid_fid:
            max_fid = mid_fid
        # otherwise we update the upper bound
        else:
            min_fid = mid_fid

    return min_fid


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # pairs = get_data(0.8, 0.95)
    # plot_data(pairs)

    eta_0 = 0.995
    p_2_0 = 0.995
    # res = get_optimal_fidelities(eta, p_2)
    # print(res)

    """
    plot_optimization()


    initial_a = 0.988
    pair = epr_pair(initial_a, (1 - initial_a) / 3, (1 - initial_a) / 3, (1 - initial_a) / 3)
    print("Initial Werner state:", pair)

    for i in range(100):
        print("Iteration", i, ":", pair)
        pair = l_swaps_k_dejmps(pair, 3, 2, eta, p_2)

    print("Final pair:", pair)


    initial_pair = epr_pair(a=0.9739456119270604, b=0.002789595457938228, c=0.0031755469472000797, d=0.020089245667801497)
    target_fid = initial_pair.a
    """
    """
    # Compute dejmps fidelity gain for different starting fidelities
    initial_fids = np.arange(0.525, 1.001, 0.02)
    dejmps_fids = []

    for initial_fid in initial_fids:
        initial_pair = epr_pair(a=initial_fid, b=(1-initial_fid)/3, c=(1-initial_fid)/3, d=(1-initial_fid)/3)
        pair = dejmps(initial_pair, initial_pair, eta, p_2)[0]
        dejmps_fids.append(pair.a)

    # compute the gains
    gains_0 = [dejmps_fids[i] - initial_fids[i] for i in range(len(initial_fids))]
    """


    # set a list of 4 values for eta and p_2 ranging from 0.95 to 0.995
    etas_p2s = [(0.97, 0.97), (0.98, 0.98), (0.99, 0.99), (0.995, 0.995)]

    # get the minimum and maximum initial fidelity F_min and F_max for each eta and p_2
    min_fids = []
    max_fids = []
    for eta, p2 in etas_p2s:
            min_fids.append(get_minimum_initial_fidelity(eta, p2))
            max_fids.append(get_maximum_initial_fidelities(eta, p2))
            print("eta =", eta, "p_2 =", p2, "min_fid =", min_fids[-1], "max_fid =", max_fids[-1])

    # set a range of 20 points between F_min and F_max for each eta and p_2
    initial_fids = []
    for i in range(len(etas_p2s)):
        initial_fids.append(np.arange(min_fids[i], max_fids[i] + 0.0001, (max_fids[i] - min_fids[i]) / 20))

    # compute the fidelity gain for each eta and p_2, for each initial fidelity
    dejmps_fids = []
    for i in range(len(etas_p2s)):
        dejmps_fids.append([])
        for initial_fid in initial_fids[i]:
            initial_pair = epr_pair(a=initial_fid, b=(1-initial_fid)/3, c=(1-initial_fid)/3, d=(1-initial_fid)/3)
            pair = dejmps(initial_pair, initial_pair, etas_p2s[i][0], etas_p2s[i][1])[0]
            dejmps_fids[i].append(pair.a)

    # compute the gains
    gains = []
    for i in range(len(etas_p2s)):
        gains.append([dejmps_fids[i][j] - initial_fids[i][j] for j in range(len(initial_fids[i]))])

    # plot the fidelity gain for each eta and p_2. Each curve has a label corresponding to the eta and p_2 values
    for i in range(len(etas_p2s)):
        plt.plot(initial_fids[i], gains[i], label="eta = p_2 = " + str(etas_p2s[i][1]))
    plt.xlabel("Initial fidelity (Pre DEJMPS)")
    plt.ylabel("Fidelity gain (After DEJMPS)")

    # highlight the optimal initial fidelity for each eta and p_2
    for i in range(len(etas_p2s)):
        max_gain = max(gains[i])
        max_gain_index = gains[i].index(max_gain)
        plt.plot(initial_fids[i][max_gain_index], max_gain, 'ro', color='black')

    # add a title
    plt.title("DEJMPS Fidelity gain on different initial fidelities")

    # add a soft grid
    plt.grid(color='grey', linestyle='-', linewidth=0.25, alpha=.5)

    plt.legend()
    #plt.show()
    # save as pdf
    plt.savefig("dejmps_fidelity_gain.pdf", bbox_inches='tight')




