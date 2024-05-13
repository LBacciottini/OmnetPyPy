
__all__ = ['epr_pair']

from collections import namedtuple

# expressed in diagonal elements of the density matrix (a, b, c, d) in Bell basis
epr_pair = namedtuple('epr_pair', ['a', 'b', 'c', 'd'])


def get_werner_state(fidelity):
    """
    Generate a Werner state representation with given fidelity

    Parameters
    ----------
    fidelity : float
        The fidelity of the Werner state

    Returns
    -------
    epr_pair
        The Werner state expressed in the Bell basis
    """
    w = 1 - (4*fidelity - 1)/3
    return epr_pair(1-w, w/3, w/3, w/3)