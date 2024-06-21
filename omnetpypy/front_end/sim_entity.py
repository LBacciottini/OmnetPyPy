from omnetpypy.front_end.port import Port


class SimulatedEntity:
    r"""
    A simulated entity is any active entity belonging to the simulation, such as modules and channels.
    Every entity may have a set of ports, and must keep a reference to the simulation context.
    
    Parameters
    ----------
    name : str
        The name of the entity. Must be unique within the simulation.
    identifier : int
        The unique identifier of the entity. Must be unique within the simulation.
    port_names : list of str
        The names of the ports of the entity.
    
    Attributes
    ----------
    name : str
        The name of the entity.
    identifier : int
        The unique identifier of the entity.
    sim_context : :class:`~omnetpypy.front_end.simulation.Simulation`
        The simulation where the entity is running. Used to access simulation variables like random number generators
        and the current simulation time.
    parent : :class:`~omnetpypy.front_end.sim_entity.SimulatedEntity`
        The parent entity of the current entity. If the entity is a top-level entity, the parent is None.
    is_listening : bool
        A flag indicating whether the entity is listening for incoming messages.
    ports : dict of :class:`~omnetpypy.front_end.port.Port`
        The ports of the entity, indexed by their names.
    """

    def __init__(self, name, identifier, port_names):
        self.name = name
        self.identifier = identifier
        self.sim_context = None
        self.parent = None

        self.is_listening = False
        # if the entity is listening, the connector will call the handle_message method when a message is received

        self.ports = {port_name: Port(port_name, parent=self) for port_name in port_names}

    def set_sim_context(self, sim_context):
        r"""
        Set the simulation context of the entity. Automatically called when the entity is added to the simulation.

        Parameters
        ----------
        sim_context : :class:`~omnetpypy.front_end.simulation.Simulation`
            The simulation context where the entity is running.
        """
        self.sim_context = sim_context

    def handle_message(self, message, port_name):
        r"""
        Process a message received as input to a port.

        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be processed.
        port_name : str or None
            The name of the port on which the message was received.
            If ``None``, the message was sent by the entity itself (self message).
        """
        pass

    def schedule_message(self, message, at=None, delay=None):
        r"""
        Schedule a self message to be received by this entity.
        Calls internally the method :meth:`~omnetpypy.front_end.simulation.Simulation.schedule_self_message`.
        
        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be processed.
        at : float or None, optional
            The simulation time at which the message should be processed.
            If ``None``, the ``delay`` parameter will be used.
        delay : float or None, optional
            The time delay from the current simulation time at which the message should be processed.
            If ``None``, the ``at`` parameter will be used.
        """
        # this sends a self message to the module at the specified time
        self.sim_context.connector.schedule_self_message(entity=self, message=message, at=at, delay=delay)

    def is_scheduled(self, message):
        r"""
        Check if a message is scheduled as a self message for this entity.
        Calls internally the method :meth:`~omnetpypy.front_end.simulation.Simulation.is_scheduled`.
        
        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be checked.
        """
        return self.sim_context.connector.is_scheduled(message, self)

    def send(self, message, port_name):
        r"""
        Send a message out on a specified port.
        Calls internally the method :meth:`~omnetpypy.front_end.port.Port.tx_output`.
        
        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be sent.
        port_name : str
            The name of the port on which the message should be sent.
        """
        self.ports[port_name].tx_output(message)

    def cancel_scheduled(self, message):
        r"""
        Cancel a scheduled self message for this entity.
        Calls internally the method :meth:`~omnetpypy.front_end.simulation.Simulation.cancel_scheduled`.
        
        Parameters
        ----------
        message : :class:`~omnetpypy.front_end.message.Message`
            The message to be cancelled.
        """
        self.sim_context.connector.cancel_scheduled(message, self)

    def initialize(self, step=0):
        r"""
        Initialize the entity right before the beginning of the simulation.
        This method is automatically called by the simulation context.

        The method is called 5 times, once for each step from 0 to 4. The step number is passed as a parameter.

        Parameters
        ----------
        step : int, optional
            The initialization step number. Default is 0. This parameter is used to allow entities to perform
            different initialization actions at different steps, and synchronize with other entities.
            The steps are numbered from 0 to 4, and the entity has the guarantee that the previous steps have
            already been executed on all entities of the simulation.
        """
        pass