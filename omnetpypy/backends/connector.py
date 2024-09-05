"""
This module implements the Connector class, which is an interface to the simulation engine.
Connectors provide a set of functions to interact with the simulation engine,
such as starting and stopping the simulation, adding and removing entities from the simulation,
supporting event generation and management.
"""
import os
from abc import abstractmethod
import abc
import pandas as pd


class Connector(abc.ABC):
    r"""
    This class is an interface to the simulation engine.
    This is an abstract class, and it is meant to be subclassed by connectors to specific simulation engines.

    Parameters
    ----------
    simulation : :class:`~omnetpypy.simulation.Simulation`
        The simulation object that describes the simulation configuration and its context. Used for example to access
        the random number generators for the simulation.
    metrics : list of :class:`~omnetpypy.utilities.FutureMetric` or None, optional
        A list of metrics to be recorded during the simulation.
    output_dir : str, optional
        The output directory where the simulation data will be stored. Default is `None`, which means that the
        simulation data will not be stored.
    repetition : int, optional
        The repetition index of the simulation. Default is 0.


    Attributes
    ----------
    simulation : :class:`~omnetpypy.front_end.simulation.Simulation`
        The simulation object that describes the simulation configuration and its context. Used for example to access
        the random number generators for the simulation.
    metrics : list of :class:`~omnetpypy.utilities.FutureMetric` or None
        A list of metrics to be collected during the simulation. If ``None``, no metrics will be collected.
    output_dir : str
        The output directory where the simulation data will be stored.
    repetition : int
        The repetition index of the simulation.
    """

    def __init__(self, simulation, metrics=None, output_dir=None, repetition=0):
        self.simulation = simulation
        self.metrics = metrics

        self.output_dir = output_dir
        # check if the output directory exists, if not create it
        if output_dir is not None and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.repetition = repetition

        # allocate a dict of numpy dataframes indexed by metric name
        if metrics is not None:
            metrics_numbers_str = [metric for metric in metrics if metric.type == "number" or metric.type == "str"]
            metrics_dict = [metric for metric in metrics if metric.type == "dict"]
            self.metrics_dict = metrics_dict
            self.metrics_data = {metric.name: pd.DataFrame(columns=["sample", "timestamp"]) for metric in metrics_numbers_str}
            self.metrics_columns = {metric.name: ["sample", "timestamp"] for metric in metrics_numbers_str}
            for metric in metrics_dict:
                self.metrics_data[metric.name] = pd.DataFrame(columns=metric.columns)
                self.metrics_columns[metric.name] = metric.columns

            self.metrics_headers = {metric.name: False for metric in metrics}
        else:
            self.metrics_data = {}
            self.metrics_dict = []
            self.metrics_columns = {}

    @abstractmethod
    def start_simulation(self, until=None):
        """
        Start the simulation.

        Parameters
        ----------
        until : float or None, optional
            The simulation time at which the simulation should stop.
            If None, the simulation will run until there are no more events to process.
        """
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def add_entity(self, entity):
        r"""
        Add an entity to the simulation.

        Parameters
        ----------
        entity : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
            The simulation entity to be added to the simulation.
        """
        entity.set_sim_context(self.simulation)

        # check if entity has property sub_modules
        if hasattr(entity, "sub_modules"):
            for _, entity in entity.sub_modules.items():
                self.add_entity(entity)

    @abstractmethod
    def get_time(self):
        r"""
        Return the current simulation time. The time unit is determined by the simulation configuration.
        """
        raise NotImplementedError("to be implemented by subclasses")

    def random(self):
        r"""
        Return the random number generator instantiated for the current
        simulation.

        Returns
        -------
        :class:`~omnetpypy.utilities.MultiRandom`
            A random number generator that supports multiple independent streams, powered by an independent seed
            for each stream.
        """
        return self.simulation.rng

    @abstractmethod
    def schedule_port_input(self, port, message):
        r"""
        Schedule the event of a message received by a port.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The port that receives the message.
        message : :class:`~omnetpypy.front_end.message.Message`
            The message that received by the port.
        """
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def schedule_self_message(self, message, entity, at=None, delay=None):
        r"""
        Schedule a self message to be processed by an entity.

        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be processed.
        entity : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
            The entity that will process the message.
        at : float or None, optional
            The simulation time at which the message should be processed.
            If None, the ``delay`` parameter will be used.
        delay : float or None, optional
            The time delay from the current simulation time at which the message should be processed.
            If None, the ``at`` parameter will be used.
        """
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def is_scheduled(self, message, entity):
        r"""
        Check if a message is scheduled as a self message for an entity.

        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be checked.
        entity : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
            The entity to check, that should receive the self message.
        """
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def cancel_scheduled(self, message, entity):
        r"""
        Cancel a scheduled self message for an entity.
        If the message is not scheduled, nothing happens.
        """
        raise NotImplementedError("to be implemented by subclasses")

    def record_metric(self, metric, value):
        """
        Record a metric value for the current simulation.

        Parameters
        ----------
        metric : str
            The name of the metric to be recorded.
        value : float
            The value of the metric to be recorded.
            If value is a dict or a list and the output file format is csv,
            it will be turned into a string and stored as is under the "sample" column.
        """
        if self.metrics is not None and self.output_dir is not None:
            # add the value to the metric dataframe by simply appending a new row using loc

            if metric in self.metrics_data:

                index_dict = -1
                for i, metric_dict in enumerate(self.metrics_dict):
                    if metric_dict.name == metric:
                        index_dict = i
                        break
                is_dict = True if index_dict != -1 else False

                if not is_dict:
                    self.metrics_data[metric].loc[len(self.metrics_data[metric].index)] = [value, self.get_time()]

                else:
                    assert isinstance(value, dict), "The value of a dict metric must be a dict"
                    assert set(value.keys()) == set(self.metrics_dict[index_dict].columns).difference({"timestamp"}), \
                        "The keys of the dict value must match the columns of the metric"
                    assert "timestamp" not in value.keys(), "The key 'timestamp' is reserved for the timestamp"
                    assert all([isinstance(value[key], (int, float, str)) for key in value.keys()]), \
                        "The values of the dict must be int, float or str"

                    # get the row as a list of values whose keys are ordered alphabetically
                    value["timestamp"] = self.get_time()

                    self.metrics_data[metric].loc[len(self.metrics_data[metric].index)] = value

                # append the metrics to the output file if the dataframes are too big
                if len(self.metrics_data[metric].index) > 1000:
                    self.dump_metric(metric)

        elif self.metrics is None:
            raise Exception("No metrics have been defined for this simulation")

    def dump_metric(self, metric):
        """
        Dump the metric data to the temporary output file for this repetition.

        Parameters
        ----------
        metric : str
            The name of the metric to be dumped.
        """
        if self.metrics is not None and self.output_dir is not None:
            if metric in self.metrics_data:
                if not self.metrics_headers[metric]:
                    self.metrics_data[metric].to_csv(f"{self.output_dir}/.{metric}_vector_rep{self.repetition}.csv", mode="w", header=True, index=False)
                    self.metrics_headers[metric] = True
                else:
                    self.metrics_data[metric].to_csv(f"{self.output_dir}/.{metric}_vector_rep{self.repetition}.csv", mode="a", header=False, index=False)

                self.metrics_data[metric] = pd.DataFrame(columns=self.metrics_columns[metric])

        elif self.metrics is None:
            raise Exception("No metrics have been defined for this simulation")

