.. _config_file:

Configuration YAML File
=======================

This file is **mandatory** and it is crucial. It is used to specify the main configuration of the simulation.

The file is a dictionary with the following keys:

        - engine (``str``), optional:
            The simulation engine to use. Only "simpy" is supported at the moment.
            Defaults to "simpy".
        - global_params (``dict``), optional:
            A dictionary with global parameters to be used in the simulation. Defaults to an empty dictionary.
            These parameters can be accessed by any entity in the simulation using the
            :func:`~omnetpypy.sim_utils.get_global_param` function.
        - log_level (``int`` or ``str``), optional:
            The log level for the simulation. See :func:`~omnetpypy.sim_log.set_log_level`.
            Defaults to "info".
        - metrics (``list`` of ``dict``), optional:
            The list of metrics to collect. Defaults to an empty list. Each metric is a dictionary with the following keys:

                - "name" (``str``): The name of the metric.
                - "type" (``str``): The type of the metric. It can be "number", "str", or "dict".
                  "number" is a scalar metric, "str" is a string metric, and "dict" is a dictionary metric with custom
                  columns.
                - "collect" (``list``). What to collect. It can contain "mean", "std", "var", "min", "max", "percentiles",
                  "vector". The most common type is "vector", which collects all samples in the dedicated
                  "./{output_dir}/{metric name}_vector.csv". All other values are scalar aggregates, all stored in
                  "./{output_dir}/{metric name}.csv". The percentiles are 0, 25, 50, 75, 100.
                  The format of these output files is described below in the `output_dir` parameter.
                - "columns" (``list``). The columns to collect for the metric. Only used for "dict" metrics.
                  Every time a sample is collected, the values in this list are collected as columns in the output file.
                  Every sample must be a dictionary with all these columns as keys. The value "timestamp" is reserved
                  and will be automatically added to the columns and managed by the system.

        - num_processes (``int``), optional:
            The number of Python parallel processes to use to run the simulations. Defaults to 1.
            Different repetitions will be run in parallel processes.
        - num_rngs (``int``), optional:
            The number of independent random number generators (RNGs) to use in the simulation. Defaults to 1.
            A different seed will be used for each RNG at every repetition.
        - output_dir (``str`` or `None`), optional:
            The output directory for the simulation, relative to the configuration file directory.
            Defaults to `None`, in which case no data will be stored.

            Aggregated metric data is stored (for each metric) in a csv files named "./{output_dir}/{metric name}.csv".
            This file contains the metric values for each repetition (one repetition per row), where the columns
            are the metric values for each repetition. For example:

            .. code-block::

                mean, std, var, min, max
                0.1, 0.01, 0.001, 0.05, 0.15
                0.2, 0.02, 0.004, 0.1, 0.5
                [...]

            In case the metric "collected" field also contains "vector", then all samples (and their collection timestamp)
            are stored in a separate file named "./{output_dir}/{metric name}_vector.csv". Samples from all repetitions are stored
            in this file, with a dedicated column for the repetition number. For example:

            .. code-block::

                sample, timestamp, repetition
                0.1, 100, 0
                0.2, 200, 0
                0.15, 100, 1
                [...]

            or, in case of a "dict" metric with custom columns:

            .. code-block::

                column1, column2, column3, timestamp, repetition
                0.1, 0.01, 0.001, 100, 0
                0.2, 0.02, 0.004, 200, 0
                0.15, 0.015, 0.00225, 100, 1
                [...]


            While the simulations are running, some temporary csv files will also be stored in the output directory.
        - repetitions (``int``), optional:
            The number of independent repetitions to run. Defaults to 1.
        - simulate_until (``float`` or `None`), optional:
            The time until which the simulation will run. If `None`, simulation runs as long as there are events.
            Defaults to `None`.
        - time_unit (``str``), optional:
            The time unit for the simulation. Defaults to "us" (microseconds). Other options are "ms" (milliseconds),
            "ns" (nanoseconds), "s" (seconds).
        - yaml_directory (``str``), optional:
            The path to the directory containing all other yaml files to set the simulation
            (see the :ref:`YAML files documentation <yaml_formats>`).
            The path is relative to this configuration file directory. Defaults to "./" .