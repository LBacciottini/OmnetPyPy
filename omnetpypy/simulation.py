r"""This module contains a set of global configuration variables for the simulation,
such as the engine to use, and a set of functions to make the configuration more user-friendly."""

import csv

import pandas as pd
import pkg_resources

from omnetpypy import utilities, sim_log, parser
from omnetpypy.backends.simpy_connector import SimPyConnector


class Simulation:
    """
    This class is a container for the simulation configuration parameters.
    It represents a simulation configuration, and it can be used to store the configuration of a repetition
    """

    def __init__(self, engine, seed_set, repetition, metrics, yaml_path, until, log_level, time_unit, output_dir,
                 global_params):
        self.engine = engine
        self.seed_set = seed_set
        self.repetition_idx = repetition
        self.until = until
        self.log_level = log_level
        self.time_unit = time_unit
        self.output_dir = output_dir

        self.global_params = global_params.copy()
        # dictionary of global parameters

        self.rng = utilities.MultiRandom(seeds=seed_set)
        self.connector = None

        # set log level
        sim_log.log_to_console(level=self.log_level)

        self.metrics = metrics
        # list of Metrics

        if engine == "simpy":
            self.connector = SimPyConnector(simulation=self, metrics=metrics, output_dir=output_dir, repetition=repetition)
        else:
            raise NotImplementedError("Engine not implemented")

        # parse topology yaml file
        self.network = parser.parse_topology(yaml_path, self)

    def start(self):
        self.connector.start_simulation(until=self.until)
        collected_data = {}
        # collect metrics
        for metric in self.metrics:
            # dump the remaining samples in memory to the temporary file
            self.connector.dump_metric(metric.name)

            # compute the statistics we need
            filename = f"{self.output_dir}/.{metric.name}_vector_rep{self.repetition_idx}.csv"
            collected_data[metric.name] = utilities.get_metrics_from_csv(metric, filename)

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

        global_params = self.config.get("global_params", {})

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

        output_dir = self.config.get("output_dir", "output")

        self.simulations_params = [(engine, self.seed_sets[i], i, metrics, yaml_path,
                                    until, log_level, time_unit, output_dir, global_params)
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

            out_dir = self.config.get("output_dir", "output")
            # write the data to csv, two files for each metric: "metric_name.csv" and "metric_name_vector.csv"
            for metric in merged.keys():
                # we write the statistics to a file if merged[metric] is not empty
                if merged[metric]:
                    df = pd.DataFrame(merged[metric])
                    df.to_csv(f"{out_dir}/{metric}.csv", index=False)

            for metric in merged.keys():
                # we open the temporary files and merge them into a single file. We add a "repetition" column
                max_reps = self.config.get("repetitions", 1)
                for i in range(max_reps):
                    if i == 0:
                        with open(f"{out_dir}/.{metric}_vector_rep{i}.csv", "r") as f:
                            # add the repetition column
                            df = pd.read_csv(f)
                            if max_reps > 1:
                                df["repetition"] = i
                            df.to_csv(f"{out_dir}/{metric}_vector.csv", index=False)

                    else:
                        with open(f"{out_dir}/.{metric}_vector_rep{i}.csv", "r") as f:
                            # add the repetition column
                            df = pd.read_csv(f)
                            if max_reps > 1:
                                df["repetition"] = i
                            df.to_csv(f"{out_dir}/{metric}_vector.csv", mode="a", header=False, index=False)
            # remove the temporary files
            import os
            for metric in merged.keys():
                for i in range(self.config.get("repetitions", 1)):
                    os.remove(f"{out_dir}/.{metric}_vector_rep{i}.csv")


def _start_sim(sim_params):
    # defined here to be picklable
    engine, seed_set, repetition, metrics, yaml_path, until, log_level, time_unit, output_dir, global_params = sim_params
    sim = Simulation(engine, seed_set, repetition, metrics, yaml_path, until, log_level, time_unit, output_dir, global_params)
    return sim.start()
