"""
This module implements the CompoundModule class, with the same semantic as in omnet++
"""
from omnetpypy.front_end.sim_entity import SimulatedEntity


class CompoundModule(SimulatedEntity):

    def __init__(self, name, identifier, port_names, **kwargs):
        super().__init__(name, identifier, port_names)

        # additional attributes based on kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.sub_entities = {}

    def add_sub_entity(self, module):
        if module.name in self.sub_entities:
            raise Exception("A submodule with the same name already exists")
        self.sub_entities[module.name] = module
        module.parent = self

    def get_sub_entity(self, name):
        # SHOULD NEVER BE USED IN A SIMULATION
        return self.sub_entities[name]

    def forward_input(self, port_container, port_submodule):
        self.ports[port_container].forward_input(port_submodule)

    def forward_output(self, port_submodule, port_container):
        self.ports[port_submodule].forward_output(port_container)

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

    def schedule_message(self, message, at=None, delay=None):
        raise Exception("CompoundModule does not support scheduling messages")

    def handle_message(self, message, port_name):
        raise Exception("CompoundModule does not support handling messages")

    def send(self, message, port_name):
        raise Exception("CompoundModule does not support sending messages")

    def cancel_scheduled(self, message):
        raise Exception("CompoundModule does not support cancelling messages")

    def is_scheduled(self, message):
        raise Exception("CompoundModule does not support checking if a message is scheduled")