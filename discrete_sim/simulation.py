r"""This module contains a set of global configuration variables for the simulation,
such as the engine to use, and a set of functions to make the configuration more user-friendly."""

import csv

import pandas as pd
import pkg_resources

from discrete_sim import utilities, sim_log, parser
from discrete_sim.backends.simpy_connector import SimPyConnector


class Simulation:
    """
    This class is a container for the simulation configuration parameters.
    It represents a simulation configuration, and it can be used to store the configuration of a repetition
    """

    def __init__(self, engine, seed_set, repetition, metrics, yaml_path, until, log_level, time_unit):
        self.engine = engine
        self.seed_set = seed_set
        self.repetition_idx = repetition
        self.until = until
        self.log_level = log_level
        self.time_unit = time_unit

        self.rng = utilities.MultiRandom(seeds=seed_set)
        self.connector = None

        # set log level
        sim_log.log_to_console(level=self.log_level)

        self.metrics = metrics
        # list of Metrics

        if engine == "simpy":
            self.connector = SimPyConnector(simulation=self, metrics=metrics)
        else:
            raise NotImplementedError("Engine not implemented")

        # parse topology yaml file
        self.network = parser.parse_topology(yaml_path, self)

    def start(self):
        self.connector.start_simulation(until=self.until)
        collected_data = {}
        # collect metrics
        for metric in self.metrics:
            # retrieve the data from the connector
            data = self.connector.metrics_data[metric.name]

            # compute the statistics we need
            collected_data[metric.name] = utilities.get_metrics(metric, data)

        return collected_data

    def time(self):
        """
        Return the current simulation time.

        Returns
        -------
        int or float
            The current simulation time.

        """
        return self.connector.get_time()

    @property
    def time_unit_factor(self):
        """
        Return the factor to convert the time unit to seconds.

        Returns
        -------
        int or float
            The factor to convert the time unit to seconds.

        """
        return utilities.time_unit_factor(self.time_unit)


class Experiment:
    """
    This class is a container for the experiment configuration parameters.
    It represents an experiment configuration, and it can be used to store the configuration of a set of
    simulated repetitions
    """

    def __init__(self, config_file):

        self.seed_sets = []

        # every repetition has its own seed set of length rngs_per_rep
        # seeds are taken from the seeds.csv file
        # with a single "seeds" column. We open and read the file here
        # but not all the seeds are used, only the first rngs_per_rep * repetitions

        self.config = parser.parse_config(config_file)

        engine = self.config.get("engine", "simpy")
        repetitions = self.config.get("repetitions", 1)
        yaml_path = self.config.get("topology_file", "topology.yaml")
        rngs_per_rep = self.config.get("num_rngs", 1)
        until = self.config.get("simulate_until", None)
        log_level = self.config.get("log_level", "info")
        time_unit = self.config.get("time_unit", "us")

        # set log level
        sim_log.log_to_console(level=log_level)

        # so we iterate over the first rngs_per_rep * repetitions seeds
        # and we store them in a list of lists, where each list of seeds
        # is the seed set for a repetition
        seeds_path = pkg_resources.resource_filename(__name__, 'seeds.csv')

        with open(seeds_path, "r") as f:
            reader = csv.reader(f)
            # use the reader sequentially on the first rngs_per_rep * repetitions rows
            for _ in range(repetitions):
                self.seed_sets.append([])
                for _ in range(rngs_per_rep):
                    self.seed_sets[-1].append(int(next(reader)[0]))

        metrics_raw = self.config.get("metrics", [])
        metrics = []

        for metric in metrics_raw:  # set up metric collection
            name = metric.get("name")
            types = metric.get("type")

            all_types = ["vector", "mean", "std", "min", "max", "median", "percentiles", "count", "var"]
            params = {k: False for k in all_types}

            true_params = {k: True for k in types}
            params.update(true_params)

            params["name"] = name

            metrics.append(utilities.FutureMetric(**params))

        self.simulations_params = [(engine, self.seed_sets[i], i, metrics, yaml_path, until, log_level, time_unit)
                                   for i in range(repetitions)]

    def run_simulations(self):

        import multiprocessing

        max_processes = self.config.get("max_processes", 1)
        # check if max_processes is greater than the number of cpu cores
        if max_processes > 1:
            max_processes = min(multiprocessing.cpu_count(), max_processes)

        # run the simulations in parallel with a ProcessPoolExecutor
        with multiprocessing.Pool(max_processes) as pool:
            collected = pool.map(_start_sim, self.simulations_params)

            # every element of collected is a dictionary of dictionaries with the same keys.
            # we want to merge them into a single dictionary, where the values
            # are lists, except for the "name" key and the "vector" key, because the latter
            # is a pandas DataFrame and we will return a single merged DataFrame

            # first we create a dictionary
            merged = {}

            # now we iterate over the collected data
            for metric in collected[0].keys():
                merged[metric] = {}

            # now we iterate over the collected data
            for data in collected:
                for metric in data.keys():
                    for key, value in data[metric].items():
                        if key != "vector":
                            if key not in merged[metric]:
                                merged[metric][key] = []
                            merged[metric][key].append(value)
                        else:
                            # we merge the dataframes
                            if key not in merged[metric]:
                                merged[metric][key] = pd.DataFrame()
                            merged[metric][key] = pd.concat([merged[metric][key], value], axis=0)

            out_dir = self.config.get("output_dir", "output")
            # write the data to csv, two files for each metric: "metric_name.csv" and "metric_name_vector.csv"
            for metric in merged.keys():
                if "vector" in merged[metric].keys():
                    merged[metric]["vector"].to_csv(f"{out_dir}/{metric}_vector.csv", index=False)
                    del merged[metric]["vector"]
                df = pd.DataFrame(merged[metric])
                df.to_csv(f"{out_dir}/{metric}.csv", index=False)


def _start_sim(sim_params):
    # defined here to be picklable
    engine, seed_set, repetition, metrics, yaml_path, until, log_level = sim_params
    sim = Simulation(engine, seed_set, repetition, metrics, yaml_path, until, log_level)
    return sim.start()
