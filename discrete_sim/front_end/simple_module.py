"""
This class implements the SimpleModule class, with the same semantic as in omnet++
"""
from abc import abstractmethod

from discrete_sim.front_end.sim_entity import SimulatedEntity


class SimpleModule(SimulatedEntity):

    def __init__(self, name, identifier, port_names):
        super().__init__(name, identifier, port_names)
        self.is_listening = True

    @abstractmethod
    def handle_message(self, message, port_name):
        pass

    def connect(self, local_port, remote_entity, remote_port, channel=None):
        """
        Connect a port of this module to a port of another remote entity.

        Parameters
        ----------
        local_port : str
            The name of the local port to be connected.
        remote_entity : SimulatedEntity
            The remote entity to which the port will be connected.
        remote_port : str
            The name of the remote port to be connected.
        channel : Channel or None, optional
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
        """
        Record a metric sample in the simulation context.

        Parameters
        ----------
        name : str
            The name of the metric
        value
            The value of the metric sample
        """
        self.sim_context.connector.record_metric(name, value)
