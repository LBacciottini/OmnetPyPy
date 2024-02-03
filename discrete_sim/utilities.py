"""
A set of utility classes and functions that are used across the package.
"""

import random

__all__ = ['MultiRandom', 'FutureMetric']

from collections import namedtuple


class MultiRandom(random.Random):
    """
    This class is a wrapper around the standard library random.Random class,
    that allows to use multiple random number generators with different seeds.

    Parameters
    ----------
    seeds : list or int
        A list of seeds for the random number generators.
        The length of the list determines the number of generators.
    """

    def __init__(self, seeds=44):
        if isinstance(seeds, int):
            seeds = [seeds]
        if len(seeds) == 0:
            super().__init__()
            self._generators = [self]
        else:
            self._generators = [random.Random() for _ in seeds]
            for g, s in zip(self._generators, seeds):
                g.seed(s)

    def __len__(self):
        return len(self._generators)

    def random(self, generator=0):
        return self._generators[generator].random()

    def randint(self, a, b, generator=0):
        return self._generators[generator].randint(a, b)

    def choice(self, seq, generator=0):
        return self._generators[generator].choice(seq)

    def shuffle(self, x, generator=0):
        return self._generators[generator].shuffle(x)

    def sample(self, population, k, generator=0):
        return self._generators[generator].sample(population, k)

    def uniform(self, a, b, generator=0):
        return self._generators[generator].uniform(a, b)

    def triangular(self, low=0.0, high=0.0, mode=None, generator=0):
        return self._generators[generator].triangular(low, high, mode)

    def normalvariate(self, mu=0.0, sigma=1.0, generator=0):
        return self._generators[generator].normalvariate(mu, sigma)

    def lognormvariate(self, mu=0.0, sigma=1.0, generator=0):
        return self._generators[generator].lognormvariate(mu, sigma)

    def gauss(self, mu=0.0, sigma=1.0, generator=0):
        return self._generators[generator].gauss(mu, sigma)

    def expovariate(self, lambd=1.0, generator=0):
        return self._generators[generator].expovariate(lambd)

    def vonmisesvariate(self, mu, kappa, generator=0):
        return self._generators[generator].vonmisesvariate(mu, kappa)

    def gammavariate(self, alpha, beta, generator=0):
        return self._generators[generator].gammavariate(alpha, beta)

    def betavariate(self, alpha, beta, generator=0):
        return self._generators[generator].betavariate(alpha, beta)

    def paretovariate(self, alpha, generator=0):
        return self._generators[generator].paretovariate(alpha)

    def weibullvariate(self, alpha, beta, generator=0):
        return self._generators[generator].weibullvariate(alpha, beta)

    def getstate(self, generator=0):
        return self._generators[generator].getstate()

    def setstate(self, state, generator=0):
        self._generators[generator].setstate(state)


FutureMetric = namedtuple("FutureMetric", ["name", "vector", "mean", "median", "std", "var", "min", "max",
                               "count", "percentiles"])
"""
A type that describes one of the metrics to collect during simulations. The fields, apart from the name, are booleans
indicating the statistics to collect for the metric. Such fields are:
- vector: the list of values of the metric
- mean: the mean of the values
- median: the median of the values
- std: the standard deviation of the values
- var: the variance of the values
- min: the minimum value
- max: the maximum value
- count: the number of samples
- percentiles: the percentiles of the values (1, 5, 25, 75, 95, 99)
"""


def get_metrics(metric, df):
    """
    Compute the statistics for a metric and return them as a dictionary.

    Parameters
    ----------
    metric : FutureMetric
        The metric to collect.
    df : pandas.DataFrame
        The sampled data of the metric.

    Returns
    -------
    dict
        A dictionary containing the requested statistics for the metric.
    """

    # always use only the samples column and convert result to float

    final = {}
    if metric.vector:
        final["vector"] = df
    if metric.mean:
        final["mean"] = df['sample'].mean()
    if metric.median:
        final["median"] = df['sample'].median()
    if metric.std:
        final["std"] = df['sample'].std()
    if metric.var:
        final["var"] = df['sample'].var()
    if metric.min:
        final["min"] = df['sample'].min()
    if metric.max:
        final["max"] = df['sample'].max()
    if metric.count:
        final["count"] = df['sample'].count()
    if metric.percentiles:
        quantiles_df = df['sample'].quantile([0.01, 0.05, 0.25, 0.75, 0.95, 0.99])
        final["percentiles"] = quantiles_df.to_dict()

    return final
