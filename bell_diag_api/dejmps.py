__all__ = ["dejmps"]

from bell_diag_api.utility import epr_pair


# compute N
def calculate_success_probability(a_1, b_1, c_1, d_1, a_2, b_2, c_2, d_2, eta, p_2):
    numerator = (
        4 * (a_1 + a_2 * b_1 + b_2 * b_1 + b_1 * c_2 + a_2 * c_1 + b_2 * c_1 + c_2 * c_1 + b_1 * d_2 + c_1 * d_2 + a_2 * d_1 + b_2 * d_1
             + c_2 * d_1 + d_2 * d_1)
        + 4 * p_2 ** 2 * (
            a_2 * a_1 + a_1 * b_2 + a_2 * b_1 + b_2 * b_1 - a_1 * c_2 - b_1 * c_2 - a_2 * c_1 - b_2 * c_1 + c_2 * c_1 - a_1 * d_2 - b_1 * d_2
            + c_1 * d_2 - a_2 * d_1 - b_2 * d_1 + c_2 * d_1 + d_2 * d_1
        )
        - 16 * eta * p_2**2 * (
            a_2 * a_1 + a_1 * b_2 + a_2 * b_1 + b_2 * b_1 - a_1 * c_2 - b_1 * c_2 - a_2 * c_1  
            - b_2 * c_1 + c_2 * c_1 - a_1 * d_2   - b_1 * d_2 + c_1 * d_2 - a_2 * d_1 - b_2 * d_1  
          + c_2 * d_1 + d_2 * d_1  
        )
        + 16 * eta**2 * p_2**2 * (
            a_2 * a_1  + a_1 * b_2  + a_2 * b_1  + b_2 * b_1  - a_1 * c_2 
            - b_1 * c_2  - a_2 * c_1  - b_2 * c_1  + c_2 * c_1  - a_1 * d_2 
            - b_1 * d_2  + c_1 * d_2  - a_2 * d_1  - b_2 * d_1  + c_2 * d_1 
            + d_2 * d_1 
        )
    )

    denominator = 8

    success_probability = numerator / denominator

    return success_probability


def calculate_a_prime(a_1, b_1, c_1, d_1, a_2, b_2, c_2, d_2, eta, p_2, N):
    numerator = (
        a_1 + a_2 * b_1 + b_2 * b_1 + b_1 * c_2 + a_2 * c_1 + b_2 * c_1 + c_2 * c_1 + b_1 * d_2 + c_1 * d_2 + a_2 * d_1 + b_2 * d_1
        + c_2 * d_1 + d_2 * d_1
        + p_2 ** 2 * (
            7 * a_2 * a_1 - a_1 * b_2 - a_2 * b_1 + 7 * b_2 * b_1 - a_1 * c_2 - b_1 * c_2 - a_2 * c_1 - b_2 * c_1 - c_2 * c_1
            - a_1 * d_2 - b_1 * d_2 - c_1 * d_2 - a_2 * d_1 - b_2 * d_1 - c_2 * d_1 - d_2 * d_1
            - 16 * a_2 * a_1 * eta - 16 * b_2 * b_1 * eta + 16 * a_2 * c_1 * eta + 16 * b_2 * d_1 * eta
            + 16 * a_2 * a_1 * eta ** 2 + 16 * b_2 * b_1 * eta ** 2 - 16 * a_2 * c_1 * eta ** 2 - 16 * b_2 * d_1 * eta ** 2
        )
    )

    denominator = 8 * N

    a_prime = numerator / denominator

    return a_prime


def calculate_b_prime(a_1, b_1, c_1, d_1, a_2, b_2, c_2, d_2, eta, p_2, N):
    numerator = (
        a_1 + a_2 * b_1 + b_2 * b_1 + b_1 * c_2 + a_2 * c_1 + b_2 * c_1 + c_2 * c_1 +
        b_1 * d_2 + c_1 * d_2 + a_2 * d_1 + b_2 * d_1 + c_2 * d_1 + d_2 * d_1 +
        p_2 ** 2 * (
            -a_2 * a_1 - a_1 * b_2 - a_2 * b_1 - b_2 * b_1 - a_1 * c_2 - b_1 * c_2 -
            a_2 * c_1 - b_2 * c_1 - c_2 * c_1 - a_1 * d_2 - b_1 * d_2 + 7 * c_1 * d_2 -
            a_2 * d_1 - b_2 * d_1 + 7 * c_2 * d_1 - d_2 * d_1 + 16 * b_1 * c_2 * eta +
            16 * a_1 * d_2 * eta - 16 * c_1 * d_2 * eta - 16 * c_2 * d_1 * eta -
            16 * b_1 * c_2 * eta ** 2 - 16 * a_1 * d_2 * eta ** 2 +
            16 * c_1 * d_2 * eta ** 2 + 16 * c_2 * d_1 * eta ** 2
        )
    )
    b_prime = numerator / (8 * N)
    return b_prime

def calculate_c_prime(a_1, b_1, c_1, d_1, a_2, b_2, c_2, d_2, eta, p_2, N):
    numerator = (
        a_1 + a_2 * b_1 + b_2 * b_1 + b_1 * c_2 + a_2 * c_1 + b_2 * c_1 + c_2 * c_1 +
        b_1 * d_2 + c_1 * d_2 + a_2 * d_1 + b_2 * d_1 + c_2 * d_1 + d_2 * d_1 +
        p_2 ** 2 * (
            -a_2 * a_1 - a_1 * b_2 - a_2 * b_1 - b_2 * b_1 - a_1 * c_2 - b_1 * c_2 -
            a_2 * c_1 - b_2 * c_1 + 7 * c_2 * c_1 - a_1 * d_2 - b_1 * d_2 - c_1 * d_2 -
            a_2 * d_1 - b_2 * d_1 - c_2 * d_1 + 7 * d_2 * d_1 +
            16 * a_1 * c_2 * eta - 16 * c_2 * c_1 * eta + 16 * b_1 * d_2 * eta - 16 * d_2 * d_1 * eta -
            16 * c_2 * a_1 * eta ** 2 + 16 * c_1 * c_2 * eta ** 2 - 16 * b_1 * d_2 * eta ** 2 + 16 * d_1 * d_2 * eta ** 2
        )
    )
    c_prime = numerator / (8 * N)
    return c_prime




def calculate_d_prime(a_1, b_1, c_1, d_1, a_2, b_2, c_2, d_2, eta, p_2, N):
    numerator = (
        a_1 + a_2 * b_1 + b_2 * b_1 + b_1 * c_2 + a_2 * c_1 + b_2 * c_1 + c_2 * c_1 +
        b_1 * d_2 + c_1 * d_2 + a_2 * d_1 + b_2 * d_1 + c_2 * d_1 + d_2 * d_1 +
        p_2 ** 2 * (
            -a_2 * a_1 + 7 * a_1 * b_2 + 7 * a_2 * b_1 - b_2 * b_1 - a_1 * c_2 - b_1 * c_2 -
            a_2 * c_1 - b_2 * c_1 - c_2 * c_1 - a_1 * d_2 - b_1 * d_2 - c_1 * d_2 -
            a_2 * d_1 - b_2 * d_1 - c_2 * d_1 - d_2 * d_1 - 16 * a_1 * b_2 * eta -
            16 * a_2 * b_1 * eta + 16 * b_2 * c_1 * eta + 16 * a_2 * d_1 * eta +
            16 * a_1 * b_2 * eta ** 2 + 16 * a_2 * b_1 * eta ** 2 -
            16 * b_2 * c_1 * eta ** 2 - 16 * a_2 * d_1 * eta ** 2
        )
    )
    d_prime = numerator / (8 * N)
    return d_prime


def dejmps(pair_a, pair_b, eta, p_2):
    N = calculate_success_probability(a_1=pair_a.a, b_1=pair_a.b, c_1=pair_a.c, d_1=pair_a.d,
                                      a_2=pair_b.a, b_2=pair_b.b, c_2=pair_b.c, d_2=pair_b.d,
                                      eta=eta, p_2=p_2)
    a_prime = calculate_a_prime(a_1=pair_a.a, b_1=pair_a.b, c_1=pair_a.c, d_1=pair_a.d,
                                a_2=pair_b.a, b_2=pair_b.b, c_2=pair_b.c, d_2=pair_b.d,
                                eta=eta, p_2=p_2, N=N)
    b_prime = calculate_b_prime(a_1=pair_a.a, b_1=pair_a.b, c_1=pair_a.c, d_1=pair_a.d,
                                a_2=pair_b.a, b_2=pair_b.b, c_2=pair_b.c, d_2=pair_b.d,
                                eta=eta, p_2=p_2, N=N)
    c_prime = calculate_c_prime(a_1=pair_a.a, b_1=pair_a.b, c_1=pair_a.c, d_1=pair_a.d,
                                a_2=pair_b.a, b_2=pair_b.b, c_2=pair_b.c, d_2=pair_b.d,
                                eta=eta, p_2=p_2, N=N)
    d_prime = calculate_d_prime(a_1=pair_a.a, b_1=pair_a.b, c_1=pair_a.c, d_1=pair_a.d,
                                a_2=pair_b.a, b_2=pair_b.b, c_2=pair_b.c, d_2=pair_b.d,
                                eta=eta, p_2=p_2, N=N)
    return epr_pair(a=a_prime, b=b_prime, c=c_prime, d=d_prime), N

