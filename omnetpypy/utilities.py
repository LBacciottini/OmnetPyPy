"""
A set of utility classes and functions that are used across the package.
"""

import random
from numpy.random import default_rng

__all__ = ['MultiRandom', 'FutureMetric', 'get_metrics', 'get_metrics_from_csv', 'time_unit_factor']

from collections import namedtuple


class MultiRandom(random.Random):
    r"""
    This class is a wrapper around the standard library :class:`random.Random` class,
    that allows to use multiple random number generators with different seeds.

    Parameters
    ----------
    seeds : list or int
        A list of seeds for the random number generators.
        The length of the list determines the number of generators. If a single integer is provided,
        a single generator is created.
    """

    def __init__(self, seeds=44):
        if isinstance(seeds, int):
            seeds = [seeds]
        if len(seeds) == 0:
            super().__init__()
            self._generators = [self]
        else:
            self._generators = [random.Random() for _ in seeds]
            self.numpy_generators = [default_rng(seed=seed) for seed in seeds]
            for g, s in zip(self._generators, seeds):
                g.seed(s)

    def __len__(self):
        return len(self._generators)

    def random(self, generator=0):
        r"""
        Return the next random floating point number uniformly distributed in the range [0.0, 1.0).
        
        Parameters
        ----------
        generator : int, optional
            The index of the generator to use. Defaults to 0.
        
        Returns
        -------
        float
            The next random floating point number.
        
        See Also
        --------
        :meth:`random.Random.random`
        """
        return self._generators[generator].random()

    def randint(self, a, b, generator=0):
        r"""
        Return the next random integer N such that a <= N <= b.

        Parameters
        ----------
        a : int
            The lower bound of the random integer.
        b : int
            The upper bound of the random integer.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        int
            The next random integer.

        See Also
        --------
        :meth:`random.Random.randint`
        """
        return self._generators[generator].randint(a, b)

    def choice(self, seq, generator=0):
        r"""
        Return a random element from the non-empty sequence ``seq``.

        Parameters
        ----------
        seq : iterable
            A non-empty sequence.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        object
            A random element from the sequence.

        See Also
        --------
        :meth:`random.Random.choice`
        """
        return self._generators[generator].choice(seq)

    def choices(self, sequence, weights=None, cum_weights=None, k=1, generator=0):
        r"""
        Return a k sized list of elements chosen from the population with replacement.

        Parameters
        ----------
        sequence : iterable
            A non-empty sequence.
        weights : list, optional
            A list of weights to be used in the selection. If ``None``, the weights are assumed to be equal.
            The relative weights determine the probability of selecting each element.
        cum_weights : list, optional
            A list of cumulative weights to be used in the selection. If ``None``, the weights are assumed to be equal.
            The relative weights determine the probability of selecting each element.
        k : int, optional
            The number of elements to choose. Defaults to 1.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        list
            A list of k elements chosen from the population.

        See Also
        --------
        :meth:`random.Random.choices`
        """
        return self._generators[generator].choices(sequence, weights=weights, cum_weights=cum_weights, k=k)

    def shuffle(self, x, generator=0):
        r"""
        Shuffle the sequence x in place.

        Parameters
        ----------
        x : iterable
            The sequence to shuffle.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        See Also
        --------
        :meth:`random.Random.shuffle`
        """
        return self._generators[generator].shuffle(x)

    def sample(self, population, k, generator=0):
        r"""
        Return a k length list of unique elements chosen from the population sequence or set.

        Parameters
        ----------
        population : iterable
            A non-empty sequence or set.
        k : int
            The number of unique elements to choose.
        generator : int, optional
            The index of the generator to use. Defaults to 0.


        Returns
        -------
        list
            A list of unique elements chosen from the population.


        See Also
        --------
        :meth:`random.Random.sample`
        """
        return self._generators[generator].sample(population, k)

    def uniform(self, a, b, generator=0):
        r"""
        Return a random floating point number N such that a <= N <= b for a <= b and b <= N <= a for b < a.

        Parameters
        ----------
        a : float
            The lower bound of the random number.
        b : float
            The upper bound of the random number.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.


        See Also
        --------
        :meth:`random.Random.uniform`

        """
        return self._generators[generator].uniform(a, b)

    def geometric(self, p, size=None, generator=0):
        r"""
        Return a random integer N from a geometric distribution.

        This is the only method that uses the numpy random number generator (:class:`numpy.random.Generator`) instead
        of the standard library random number generator (:class:`random.Random`).

        Parameters
        ----------
        p : float
            The probability of success.
        size : int or tuple of ints or None, optional
            The shape of the output. If None, a single value is returned.
        generator : int, optional
            The index of the generator to use. Defaults to 0.


        See Also
        --------
        :meth:`numpy.random.Generator.geometric`
        """
        return self.numpy_generators[generator].geometric(p, size)

    def triangular(self, low=0.0, high=0.0, mode=None, generator=0):
        r"""
        Return a random floating point number N such that low <= N <= high and with the specified mode between bounds.

        Parameters
        ----------
        low : float
            The lower bound of the random number.
        high : float
            The upper bound of the random number.
        mode : float or None, optional
            The mode of the distribution. If None, the mode is the midpoint between the bounds.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        See Also
        --------
        :meth:`random.Random.triangular`
        
        """
        return self._generators[generator].triangular(low, high, mode)

    def normalvariate(self, mu=0.0, sigma=1.0, generator=0):
        r"""
        Return a random floating point number N from a normal (Gaussian) distribution.

        Parameters
        ----------
        mu : float
            The mean of the distribution.
        sigma : float
            The standard deviation of the distribution.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.normalvariate`
        """
        return self._generators[generator].normalvariate(mu, sigma)

    def lognormvariate(self, mu=0.0, sigma=1.0, generator=0):
        r"""
        Return a random floating point number N from a lognormal distribution.

        Parameters
        ----------
        mu : float
            The mean of the distribution.
        sigma : float
            The standard deviation of the distribution.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.lognormvariate`
        """
        return self._generators[generator].lognormvariate(mu, sigma)

    def gauss(self, mu=0.0, sigma=1.0, generator=0):
        r"""
        Return a random floating point number N from a normal (Gaussian) distribution.

        Parameters
        ----------
        mu : float
            The mean of the distribution.
        sigma : float
            The standard deviation of the distribution.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.gauss`
        """
        return self._generators[generator].gauss(mu, sigma)

    def expovariate(self, lambd=1.0, generator=0):
        r"""
        Return a random floating point number N from a normal (Gaussian) distribution.

        Parameters
        ----------
        lambd : float
            The rate of the exponential distribution.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.expovariate`
        """
        return self._generators[generator].expovariate(lambd)

    def vonmisesvariate(self, mu, kappa, generator=0):
        r"""
        Return a random floating point number N from a von Mises distribution.

        Parameters
        ----------
        mu : float
            The mean of the distribution.
        kappa : float
            The concentration of the distribution.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.vonmisesvariate`
        """
        return self._generators[generator].vonmisesvariate(mu, kappa)

    def gammavariate(self, alpha, beta, generator=0):
        r"""
        Return a random floating point number N from a gamma distribution.

        Parameters
        ----------
        alpha : float
            The shape of the distribution. Can be any positive number.
        beta : float
            The scale of the distribution. Can be any positive number.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.gammavariate`
        """
        return self._generators[generator].gammavariate(alpha, beta)

    def betavariate(self, alpha, beta, generator=0):
        r"""
        Return a random floating point number N from a beta distribution.

        Parameters
        ----------
        alpha : float
            The first shape parameter of the distribution. Can be any positive number.
        beta : float
            The second shape parameter of the distribution. Can be any positive number.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.betavariate`
        """
        return self._generators[generator].betavariate(alpha, beta)

    def paretovariate(self, alpha, generator=0):
        r"""
        Return a random floating point number N from a Pareto distribution.

        Parameters
        ----------
        alpha : float
            The shape of the distribution. Can be any positive number.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.parentovariate`
        """
        return self._generators[generator].paretovariate(alpha)

    def weibullvariate(self, alpha, beta, generator=0):
        r"""
        Return a random floating point number N from a Weibull distribution.

        Parameters
        ----------
        alpha : float
            The shape of the distribution. Can be any positive number.
        beta : float
            The scale of the distribution. Can be any positive number.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        Returns
        -------
        float
            The next random floating point number.

        See Also
        --------
        :meth:`random.Random.weibullvariate`
        """
        return self._generators[generator].weibullvariate(alpha, beta)

    def getstate(self, generator=0):
        r"""
        Return the internal state of the random number generator.

        Parameters
        ----------
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        See Also
        --------
        :meth:`random.Random.getstate`
        """
        return self._generators[generator].getstate()

    def setstate(self, state, generator=0):
        r"""
        Set the internal state of the random number generator.

        Parameters
        ----------
        state : tuple
            The internal state of the random number generator.
        generator : int, optional
            The index of the generator to use. Defaults to 0.

        See Also
        --------
        :meth:`random.Random.setstate`

        """
        self._generators[generator].setstate(state)


FutureMetric = namedtuple("FutureMetric", ["name", "vector", "mean", "median", "std", "var", "min", "max",
                               "count", "percentiles", "type", "columns"])
r"""
A type that describes the metrics to collect during simulations. The fields, apart from the name, are booleans
indicating the statistics to collect for the metric. Such fields are:

- vector: the complete list of samples of the metric 
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
    r"""
    Compute the statistics for a metric and return them as a dictionary.
    Not used in the current version of the package because it requires all samples to be loaded in memory.

    Parameters
    ----------
    metric : :class:`~omnetpypy.utilities.FutureMetric`
        The metric to collect.
    df : :class:`pandas.DataFrame`
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


def get_metrics_from_csv(metric, filename):
    r"""
    Compute the statistics for a metric and return them as a dictionary.

    Parameters
    ----------
    metric : :class:`~omnetpypy.utilities.FutureMetric`
        The metric to collect.
    filename : string
        The name of the file containing the sampled data of the metric.

    Returns
    -------
    dict
        A dictionary containing the requested statistics for the metric.
    """

    # compute the statistics without loading the whole file in memory
    # the csv_iterator is an iterator over the rows of the csv file
    # we use the first row to get the column names
    # and we use the second row to initialize the statistics
    # then we iterate over the remaining rows to update the statistics

    import csv
    import numpy as np

    # read the first row to get the column names
    with open(filename, "r") as csv_iterator:
        csv_reader = csv.reader(csv_iterator)
        header = next(csv_reader)
        sample_index = header.index("sample")

        # use metric to initialize the statistics (except for the vector, which is ignored for the moment)
        final = {}
        samples = 0
        if metric.mean:
            final["mean"] = 0
        if metric.median:
            final["median"] = []
        if metric.std:
            final["std"] = 0
        if metric.var:
            final["var"] = 0
        if metric.min:
            final["min"] = np.inf
        if metric.max:
            final["max"] = -np.inf
        if metric.count:
            final["count"] = 0
        if metric.percentiles:
            final["percentiles"] = []

        # iterate over the remaining rows to update the statistics. Median and percentiles are computed online using
        # a list with 10K elements at most and a smaller list that collects the samples for the median as the median of
        # the 10k elements. This is done to avoid loading the whole file in memory.
        median_samples = []
        median_temp = []

        percentiles_samples = []
        percentiles_temp = []

        max_elems = 100000

        for row in csv_reader:
            samples += 1
            sample = float(row[sample_index])
            if metric.mean:
                final["mean"] += sample
            if metric.median:
                median_temp.append(sample)
                if len(median_temp) > max_elems - 1:
                    median_samples.append(np.median(median_temp))
                    median_temp = []
            if metric.std:
                final["std"] += sample**2
            if metric.var:
                final["var"] += sample**2
            if metric.min:
                final["min"] = min(final["min"], sample)
            if metric.max:
                final["max"] = max(final["max"], sample)
            if metric.count:
                final["count"] += 1
            if metric.percentiles:
                percentiles_temp.append(sample)
                if len(percentiles_temp) > max_elems - 1:
                    percentiles_samples.append(np.percentile(percentiles_temp, [1, 5, 25, 75, 95, 99]))
                    percentiles_temp = []

    if samples > 0:
        # compute the final statistics
        if metric.mean:
            final["mean"] /= samples
        if metric.median:
            if len(median_samples) == 0 or len(median_temp) > (max_elems // 100):
                median_samples.append(np.median(median_temp))
            final["median"] = np.mean(median_samples)
        if metric.std:
            final["std"] = np.sqrt(final["std"] / samples - final["mean"]**2)
        if metric.var:
            final["var"] = final["var"] / samples - final["mean"]**2
        if metric.count:
            final["count"] = samples
        if metric.percentiles:
            if len(percentiles_samples) == 0 or len(percentiles_temp) > (max_elems // 100):
                percentiles_samples.append(np.percentile(percentiles_temp, [1, 5, 25, 75, 95, 99]))
            # compute the final percentiles as a list of the sample mean of the respective percentiles in the samples
            final["percentiles"] = [np.mean([x[i] for x in percentiles_samples]) for i in range(6)]

    return final


def time_unit_factor(unit):
    r"""
    Return the factor to convert a time unit to seconds. For example, if the unit is "ms", the factor is 1e-3.

    Parameters
    ----------
    unit : str
        The time unit to convert. Can be one of the following:

            - "s" for seconds
            - "ms" for milliseconds
            - "us" for microseconds
            - "ns" for nanoseconds
    """

    if unit == "s":
        return 1
    elif unit == "ms":
        return 1e3
    elif unit == "us":
        return 1e6
    elif unit == "ns":
        return 1e9
    else:
        raise ValueError("Invalid time unit")