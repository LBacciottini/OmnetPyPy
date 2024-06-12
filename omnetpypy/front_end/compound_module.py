"""
This module implements the :meth:`~omnetpypy.front_end.compound_module.CompoundModule` class.
Compound modules are non-atomic modules that contain other modules and channels.
They do not come with a behavior, but they can be used to organize the simulation model with a hierarchical structure.
Their behavior is intrinsically defined by the behavior of their submodules and how they are connected.

Compund Modules have the same semantic as in omnet++
"""
from omnetpypy.front_end.sim_entity import SimulatedEntity


class CompoundModule(SimulatedEntity):
    r"""
    This class represents a compound module in the simulation model.
    Compound modules are non-atomic modules that contain other modules and channels.
    They do not come with a behavior, but they can be used to organize the simulation model with a hierarchical
    structure. Their behavior is intrinsically defined by the behavior of their submodules and how they are connected.

    See :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity` for inherited attributes.
    All kwargs passed to the constructor are also stored as attributes of the module.

    Parameters
    ----------
    name : str
        The name of the module. This name should be unique within the simulation.
    identifier : int
        The identifier of the module. This identifier should be unique within the simulation.
    port_names : list of str
        The names of the ports of the module.
    **kwargs
        Additional, arbitrary attributes of the module, passed as keyword arguments.

    Attributes
    ----------
    sub_modules : dict of :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
        The sub-entities of the module, indexed by their names.
    """

    def __init__(self, name, identifier, port_names, **kwargs):
        super().__init__(name, identifier, port_names)

        # additional attributes based on kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.sub_modules = {}

    def add_sub_module(self, module):
        r"""
        Add a submodule to this compound module.

        Parameters
        ----------
        module : :class:`~omnetpypy:front_end.sim_entity.SimulatedEntity`
            The submodule to be added.

        Raises
        ------
        Exception
            If a submodule with the same name already exists.
        """
        if module.name in self.sub_modules:
            raise Exception("A submodule with the same name already exists")
        self.sub_modules[module.name] = module
        module.parent = self

    def get_sub_module(self, name):
        r"""
        Get a submodule by its name.

        Parameters
        ----------
        name : str
            The name of the submodule to be retrieved.

        Returns
        -------
        :class:`~omnetpypy:front_end.sim_entity.SimulatedEntity`
            The submodule with the given name.
        """
        return self.sub_modules[name]

    def forward_input(self, port_container, port_submodule):
        r"""
        Forward the input of a port of this module to a port of a submodule.

        Parameters
        ----------
        port_container : str
            The name of the port of this module that will forward the input.
        port_submodule : :class:`~omnetpypy:front_end.port.Port`
            The port of the submodule that will receive the input.

        See Also
        --------
        :meth:`~omnetpypy.front_end.port.Port.forward_input`
        """
        self.ports[port_container].forward_input(port_submodule)

    def forward_output(self, port_submodule, port_container):
        r"""
        Forward the output of a port of a submodule to a port of this module.

        Parameters
        ----------
        port_submodule : str
            The name of the port of the submodule that will forward the output.
        port_container : :class:`~omnetpypy:front_end.port.Port`
            The port of this module that will receive the output.

        See Also
        --------
        :meth:`~omnetpypy.front_end.port.Port.forward_output`
        """
        self.ports[port_submodule].forward_output(port_container)

    def connect(self, local_port, remote_entity, remote_port, channel=None):
        r"""
        Connect a port of this module to a port of another remote entity.

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

        See Also
        --------
        :meth:`~omnetpypy.front_end.port.Port.connect`
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