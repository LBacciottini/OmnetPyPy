r"""
This module contains a set of global configuration variables for the simulation,
such as the engine to use, and a set of functions to make the configuration more user-friendly.
"""

import csv

import pandas as pd
import pkg_resources

from omnetpypy import utilities, sim_log, parser
from omnetpypy.backends.simpy_connector import SimPyConnector


class Simulation:
    r"""
    This class is used to run a single simulation using the specified configuration. It takes care of reading the
    running the simulation and returning the recorded metrics. Users should not instantiate this class directly,
    but use the :class:`~omnetpypy.simulation.Experiment` to manage multiple simulations.

    All parameters are also stored as attributes.

    Parameters
    ----------
    engine : str
        The simulation engine to use. Only "simpy" is implemented at the moment.
    seed_set : list of int
        The seed set for the repetition.
    repetition : int
        The repetition index.
    metrics : list of :class:`~omnetpypy.utilities.FutureMetric`
        The list of metrics to collect.
    yaml_directory : str
        The path of the directory that contains all the yaml files.
    until : int or float
        The time until which the simulation will run.
    log_level : str
        The log level for the simulation. See :func:`~omnetpypy.sim_log.log_to_console`.
    time_unit : str
        The time unit for the simulation. See :func:`~omnetpypy.utilities.time_unit_factor`.
    output_dir : str
        The output directory for the simulation.
    global_params : dict
        A dictionary of global parameters. These parameters are available to all the entities in the simulation.


    Attributes
    ----------
    rng : :class:`~omnetpypy.utilities.MultiRandom`
        The random number generator for this simulation, already initialized. It is made available to all the entities
        in the simulation through the :class:`~omnetpypy.backends.connector.Connector`.
    connector : :class:`~omnetpypy.backends.Connector`
        The connector to the simulation engine. Its subclass depends on the chosen engine.
    network : :class:`~omnetpypy.front_end.compound_module.CompoundModule`
        The network to simulate, parsed from the YAML file "network.yaml".

    Raises
    ------
    NotImplementedError
        If the passed ``engine`` is not implemented.
    """

    def __init__(self, engine, seed_set, repetition, metrics, yaml_directory, until, log_level, time_unit, output_dir,
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
            self.connector = SimPyConnector(simulation=self, metrics=metrics, output_dir=output_dir,
                                            repetition=repetition)
        else:
            raise NotImplementedError("Engine not implemented")

        # parse yaml files
        self.network = parser.parse_yaml_directory(yaml_directory, self)

    def start(self):
        r"""
        start the simulation and collect the metrics.

        Returns
        -------
        dict
            A dictionary of dictionaries with the collected metrics.
        """
        self.connector.start_simulation(until=self.until)
        collected_data = {}
        # collect metrics
        for metric in self.metrics:
            if self.output_dir is not None:
                # dump the remaining samples in memory to the temporary file
                self.connector.dump_metric(metric.name)

                # compute the statistics we need
                filename = f"{self.output_dir}/.{metric.name}_vector_rep{self.repetition_idx}.csv"

                # check metric type
                if metric.type == "number":
                    collected_data[metric.name] = utilities.get_metrics_from_csv(metric, filename)
                else:
                    collected_data[metric.name] = {}

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
        r"""
        The factor to convert the simulation time unit to seconds.

        See Also
        --------
        :func:`~omnetpypy.utilities.time_unit_factor`

        Returns
        -------
        int or float
            The factor to convert the time unit to seconds.

        """
        return utilities.time_unit_factor(self.time_unit)


class Experiment:
    r"""
    This class is used to run a set of independent simulations using the same YAML configuration files.
    An instance of this class takes care of reading the configuration file, parsing it, running the simulations, and
    dumping the recorded metrics in the output files.

    Parameters
    ----------
    config_file : str
        The path to the configuration file, absolute or relative to the working directory.
        The configuration file is a YAML file with a rigid structure (see ``config`` attribute).

    Attributes
    ----------
    seed_sets : list of lists of int
        The seed sets for each repetition. Each repetition has a seed set of length "rngs_per_rep"
        from the configuration file.
    config : dict
        The configuration dictionary, directly parsed from the YAML configuration file.
        The dictionary has the following keys:

            - engine (``str``), optional:
                The simulation engine to use. Only "simpy" is supported at the moment.
                Defaults to "simpy".
            - repetitions (``int``), optional:
                The number of independent repetitions to run. Defaults to 1.
            - metrics (list of :class:`~omnetpypy.utilities.FutureMetric`), optional:
                The list of metrics to collect. Defaults to an empty list.
            - yaml_directory (``str``), optional:
                The path to the directory containing the yaml files to set the simulation.
                Relative to the configuration file directory. Defaults to "./" .
            - simulate_until (``float`` or `None`), optional:
                The time until which the simulation will run. If `None`, simulation runs as long as there are events.
                Defaults to `None`.
            - time_unit (``str``), optional:
                The time unit for the simulation. Defaults to "us" (microseconds).
            - log_level (``int`` or ``str``), optional:
                The log level for the simulation. See :func:`~omnetpypy.sim_log.set_log_level`.
                Defaults to ``logging.INFO``
            - output_dir (``str`` or `None`), optional:
                The output directory for the simulation, relative to the configuration file directory.
                Defaults to `None`, in which case no data will be stored.
        
    simulations_params : list of tuples
        The list of simulation parameters for each repetition. Each element of the list is a tuple with the
        following parameters:

            - engine (``str``):
                The simulation engine to use.
            - seed_set (list of int):
                The seed set for the repetition.
            - repetition (``int``):
                The repetition index.
            - metrics (list of :class:`~omnetpypy.utilities.FutureMetric`):
                The list of metrics to collect.
            - yaml_directory (``str``):
                The path to the directory containing the yaml files to set the simulation.
            - until (``float`` or `None`):
                The time until which the simulation will run. If `None`, simulation runs as long as there are events.
            - log_level (``int`` or ``str``):
                The log level for the simulation. See :func:`~omnetpypy.sim_log.set_log_level`.
            - time_unit (``str``):
                The time unit for the simulation.
            - output_dir (``str`` or `None`):
                The output directory for the simulation.
            - global_params (dict):
                A dictionary of global parameters.
                These parameters are available to all the entities in the simulation.

    output_dir : str or None
        The output directory for the simulation. If `None`, no data is stored.


    Examples
    --------
    >>> exp = Experiment(config_file="config.yaml")
    >>> exp.run_simulations()

    """

    def __init__(self, config_file):

        self.seed_sets = []

        # every repetition has its own seed set of length rngs_per_rep
        # seeds are taken from the seeds.csv file
        # with a single "seeds" column. We open and read the file here
        # but not all the seeds are used, only the first rngs_per_rep * repetitions

        self.config = parser.parse_yaml_file(config_file)

        # derive the configuration file directory from its path by removing everything after the last "/"
        config_dir = config_file[:config_file.rfind("/") + 1]

        engine = self.config.get("engine", "simpy")
        repetitions = self.config.get("repetitions", 1)
        yaml_path = config_dir + self.config.get("yaml_directory", "./")
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
        seeds_path = pkg_resources.resource_filename('omnetpypy', 'data/seeds.csv')

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
            metric_type = metric.get("type")
            collect = metric.get("collect", "number")

            all_collects = ["vector", "mean", "std", "min", "max", "median", "percentiles", "count", "var"]
            all_types = ["number", "str", "dict"]

            assert all([collect_type in all_collects for collect_type in collect]), f"collect must be one of {all_collects}"
            assert metric_type in all_types, f"type must be one of {all_types}"

            params_collect = {k: False for k in all_collects}

            true_params = {k: True for k in collect}
            params_collect.update(true_params)

            params = {"name": name,
                      "type": metric_type}
            params.update(params_collect)

            if metric_type != "number":
                assert len([k for k, v in params_collect.items() if v]) == 1 and params_collect["vector"], \
                    "only vector collect type must be set for nun-number typed metrics"

            columns = None
            if metric_type == "dict":
                columns = metric.get("columns")
                assert columns is not None, "columns must be provided for dict type metrics"
                assert isinstance(columns, list), "columns must be a list"
                assert all(isinstance(c, str) for c in columns), "columns must be a list of strings"
                assert len([k for k, v in params_collect.items() if v]) == 1 and params_collect["vector"], \
                    "only vector collect type must be True for dict type metrics"
                assert "timestamp" not in columns, "timestamp cannot be a column name, it is added automatically"

            params["columns"] = columns + ["timestamp"] if columns is not None else None

            metrics.append(utilities.FutureMetric(**params))

        if "output_dir" in self.config:
            output_dir = config_dir + self.config["output_dir"]
        else:
            output_dir = None
        self.output_dir = output_dir

        self.simulations_params = [(engine, self.seed_sets[i], i, metrics, yaml_path,
                                    until, log_level, time_unit, output_dir, global_params)
                                   for i in range(repetitions)]

    def run_simulations(self):
        r"""
        Run the simulations.
        """

        import multiprocessing

        max_processes = self.config.get("max_processes", 1)
        # check if max_processes is greater than the number of cpu cores
        if max_processes > 1:
            max_processes = min(multiprocessing.cpu_count(), max_processes)

        # if max_processes is 1, we just run the simulations sequentially
        if max_processes == 1:
            collected = []
            for sim_params in self.simulations_params:
                collected.append(_start_sim(sim_params))

        # run the simulations in parallel with a ProcessPoolExecutor
        else:
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

        out_dir = self.output_dir
        # write the data to csv, two files for each metric: "metric_name.csv" and "metric_name_vector.csv"
        if out_dir is not None:
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
