"""
This module implements the Connector class, which is an interface to the simulation engine.
Connectors provide a set of functions to interact with the simulation engine,
such as starting and stopping the simulation, adding and removing entities from the simulation,
supporting event generation and management.
"""
from abc import abstractmethod
import abc
import pandas as pd


class Connector(abc.ABC):
    """
    This class is an interface to the simulation engine.
    This is an abstract class, and it is meant to be subclassed by connectors to specific simulation engines.

    Parameters
    ----------
    simulation : Simulation
        The simulation object that describes the simulation configuration.
    """

    def __init__(self, simulation, metrics=None):
        self.simulation = simulation
        self.metrics = metrics

        # allocate a dict of numpy dataframes indexed by metric name
        if metrics is not None:
            self.metrics_data = {metric.name: pd.DataFrame(columns=["sample", "timestamp"]) for metric in metrics}
        else:
            self.metrics_data = {}

    @abstractmethod
    def start_simulation(self, until=None):
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def add_entity(self, entity):
        entity.set_sim_context(self.simulation)

        # check if entity has property sub_modules
        if hasattr(entity, "sub_entities"):
            for _, entity in entity.sub_entities.items():
                self.add_entity(entity)

    @abstractmethod
    def get_time(self):
        raise NotImplementedError("to be implemented by subclasses")

    def random(self):
        """
        Return the MultiRandom random number generator instantiated for the current simulation.

        Returns
        -------
        MultiRandom
            A random number generator that supports multiple independent streams.
        """
        return self.simulation.rng

    @abstractmethod
    def schedule_port_input(self, port, message):
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def schedule_self_message(self, message, entity, at=None, delay=None):
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def is_scheduled(self, message, entity):
        raise NotImplementedError("to be implemented by subclasses")

    @abstractmethod
    def cancel_scheduled(self, message, entity):
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
        """
        if self.metrics is not None:
            # add the value to the metric dataframe by simply appending a new row using loc

            if metric in self.metrics_data:
                self.metrics_data[metric].loc[len(self.metrics_data[metric].index)] = [value, self.get_time()]
            # otherwise we ignore the emitted metric

        else:
            raise Exception("No metrics have been defined for this simulation")

