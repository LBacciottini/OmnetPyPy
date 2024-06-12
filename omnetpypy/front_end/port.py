r"""
This module implements the :class:`~omnetpypy.front_end.port.Port` class.
Every port is an object that can receive and send messages. Ports are the interface of modules with the outside world.

Ports have the same semantic as in omnet++, except that
every port is an object itself and does not have to be input or output only.
"""


class Port:
    r"""
    This class represents a port in the simulation model.
    Ports are the interface of modules with the outside world.
    Every port is an object that can receive and send messages.

    Parameters
    ----------
    name : str
        The name of the port. This name should be unique within the parent module.
    parent : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
        The parent entity of the port, i.e., the entity to which the port belongs.

    Attributes
    ----------
    name : str
        The name of the port.
    connected_port : :class:`~omnetpypy.front_end.port.Port` or None
        The remote port to which this port is connected. If ``None``, the port is not connected.
        See also :meth:`~omnetpypy.front_end.port.Port.connect`.
    forwarded_input_port : :class:`~omnetpypy.front_end.port.Port` or None
        The remote port to which the input of this port is forwarded. If ``None``, the port does not forward input.
        See also :meth:`~omnetpypy.front_end.port.Port.forward_input`.
    forwarded_output_port : :class:`~omnetpypy.front_end.port.Port` or None
        The remote port to which the output of this port is forwarded. If ``None``, the port does not forward output.
        See also :meth:`~omnetpypy.front_end.port.Port.forward_output`.
    parent : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
        The parent entity of the port.
    subscribed_ports : list of :class:`~omnetpypy.front_end.port.Port`
        The list of ports that are subscribed to this port.
        Every subscribed port receives a copy of each message sent to this port.
    is_subscribed : bool
        A flag indicating whether this port is subscribed to another port.
        See also :meth:`~omnetpypy.front_end.port.Port.subscribe_to`.
    """

    def __init__(self, name, parent):
        self.name = name
        self.connected_port = None
        self.forwarded_input_port = None
        self.forwarded_output_port = None
        self.parent = parent
        self.subscribed_ports = []
        self.is_subscribed = False

    def connect(self, port):
        r"""
        Connect this port to another remote port.
        The output of this port will be fed as input to the other port, and vice versa.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The remote port to which this port will be connected.

        Raises
        ------
        ValueError
            If this port is already connected to another port,
            if the remote port is already connected to another port,
            if this port is already subscribed to another port,
            or if this port output is already forwarded to another port.
        """
        if self.is_subscribed:
            raise ValueError("Cannot connect a port that is already subscribed to another port")
        if port.connected_port is not None:
            raise ValueError("Cannot connect to a remote port that is already connected")
        if self.connected_port is not None:
            raise ValueError("Cannot connect a port that is already connected")
        if self.forwarded_output_port:
            raise ValueError("Cannot connect a port that is forwarding output")

        self.connected_port = port
        port.connected_port = self

    def subscribe_to(self, port):
        r"""
        Subscribe this port to another remote port.
        This port will receive a copy of each message sent to the remote port.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The remote port to which this port will be subscribed.

        Raises
        ------
        ValueError
            If this port is already connected to another port,
            if the remote port is already connected to another port,
            or if the remote port is forwarding output
        """

        if self.connected_port is not None:
            raise ValueError("Cannot subscribe a port that is already connected")
        if port.forwarded_output_port:
            raise ValueError("Cannot subscribe to a port that is forwarding output")
        if port.connected_port is not None:
            raise ValueError("Cannot subscribe to a port that is already connected")

        port.subscribed_ports.append(self)
        self.is_subscribed = True

    def disconnect(self, port):
        r"""
        Disconnect this port from another remote port.
        If the two ports are not connected to any other port, this does nothing.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The remote port from which this port will be disconnected.

        Raises
        ------
        ValueError
            If this or the other port are connected to a third port and not mutually connected.
        """

        # check whether the two ports were actually connected
        if self.connected_port != port or port.connected_port != self:
            raise ValueError("The two ports are not connected")

        self.connected_port = None
        port.connected_port = None

    def forward_input(self, port):
        r"""
        Forward the input of this port to another remote port.
        The input of this port will be sent as input to the other port.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The remote port to which the input of this port will be forwarded.

        Raises
        ------
        ValueError
            If this port is already connected to another port,
            or if the remote port is already connected to another port,
        """

        if self.connected_port is not None:
            raise ValueError("Cannot forward input from a port that is already connected")
        if port.connected_port is not None:
            raise ValueError("Cannot forward input to a port that is already connected")

        self.forwarded_input_port = port

    def forward_output(self, port):
        r"""
        Forward the output of this port to another remote port.
        The output of this port will be sent as output to the other port.

        Parameters
        ----------
        port : :class:`~omnetpypy.front_end.port.Port`
            The remote port to which the output of this port will be forwarded.

        Raises
        ------
        ValueError
            If this port is already connected to another port,
            or if the remote port is already connected to another port,
        """

        if self.connected_port is not None:
            raise ValueError("Cannot forward input from a port that is already connected")
        if port.connected_port is not None:
            raise ValueError("Cannot forward input to a port that is already connected")

        self.forwarded_output_port = port

    def tx_output(self, message):
        r"""
        Send a message as output of this port.

        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be sent.
        """

        if self.forwarded_output_port:
            self.forwarded_output_port.tx_output(message)
        elif self.connected_port:
            self.connected_port.tx_input(message)
        elif len(self.subscribed_ports) > 0:
            for port in self.subscribed_ports:
                message_cpy = message.__copy__()
                port.tx_input(message_cpy)
        else:
            # do nothing, the mesaage is lost
            pass

    def tx_input(self, message):
        r"""
        Receive a message as input of this port.

        Parameters
        ----------
        message : :class:`~omnetpypy:front_end.message.Message`
            The message to be received.
        """

        if self.forwarded_input_port:
            self.forwarded_input_port.tx_input(message)
        elif self.parent.is_listening:
            self.parent.sim_context.connector.schedule_port_input(self, message)
        else:
            # do nothing, the mesaage is lost
            pass
