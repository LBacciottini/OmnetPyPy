"""
This module implements the SimpleModule abstract class.

The class has the same semantic as its homonym in omnet++, and it is meant to be subclassed by the user to define
its custom simulation modules.
"""
from abc import abstractmethod

from omnetpypy.front_end.sim_entity import SimulatedEntity


class SimpleModule(SimulatedEntity):
    r"""
    This class is an abstract class that represents a simple module in the simulation.
    Simple modules are the basic building blocks of the simulation model. They can send and receive messages
    through their ports, and they can be connected to other modules through channels connecting their ports.
    The behavior of a simple module is defined by how it handles incoming messages. The user should subclass this class
    to define custom simulation modules.

    Simple modules are also in charge of recording metrics samples. The user can call the method
    :meth:`~omnetpypy.front_ent.simple_module.SimpleModule.emit_metric` at any time to record a metric sample.

    See :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity` for inherited attributes.

    Parameters
    ----------
    name : str
        The name of the module. This name should be unique within the simulation.
    identifier : int
        The identifier of the module. This identifier should be unique within the simulation.
    port_names : list of str
        The names of the ports of the module.
    """

    def __init__(self, name, identifier, port_names):
        super().__init__(name, identifier, port_names)
        self.is_listening = True

    @abstractmethod
    def handle_message(self, message, port_name):
        r"""
        Handle a message received as input to a port.
        This method must be implemented by every subclass to define the behavior of the custom module.

        Parameters
        ----------
        message : :class:`~omnetpypy:front_end.message.Message`
            The message to be processed.
        port_name : str or None
            The name of the port on which the message was received.
            If ``None``, the message is a self message scheduled by this module.
        """
        pass

    def connect(self, local_port, remote_entity, remote_port, channel=None):
        r"""
        Connect a port of this module to a port of another remote entity.
        The output of a port will be fed as input to the other port
        (up to the intermediate actions of a channel, if any).

        Parameters
        ----------
        local_port : str
            The name of the local port to be connected.
        remote_entity : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
            The remote entity to which the port will be connected.
        remote_port : str
            The name of the remote port to be connected.
        channel : :class:`~omnetpypy.front_end.channel.Channel` or None, optional
            The channel through which the connection will be made, if any.
            If set, the local port is connected to the "A" port of the channel,
            and the "B" port of the channel is connected to the remote port.
        """

        if channel is not None:
            self.ports[local_port].connect(channel.ports["A"])
            channel.ports["B"].connect(remote_entity.ports[remote_port])
        else:
            self.ports[local_port].connect(remote_entity.ports[remote_port])

    def emit_metric(self, name, value):
        r"""
        Record a metric sample in the simulation context.
        The metric name must be defined in the main configuration file.

        Parameters
        ----------
        name : str
            The name of the metric.
            The metric name must be defined in the simulation configuration.
        value : Any
            The value of the metric sample
        """
        self.sim_context.connector.record_metric(name, value)
