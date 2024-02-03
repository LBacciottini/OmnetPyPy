from discrete_sim.front_end.port import Port


class SimulatedEntity:
    """
    A simulated entity is any active entity belonging to the simulation, such as modules and channels.
    Every entity may have a set of ports, and must keep a reference to the simulation context.
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
        self.sim_context = sim_context

    def handle_message(self, message, port_name):
        """
        Process a message received as input to a port.

        Parameters
        ----------
        message : Message
            The message to be processed.
        port_name : Port
            The port from which the message was received.
        """
        pass

    def schedule_message(self, message, at=None, delay=None):
        # this sends a self message to the module at the specified time
        self.sim_context.connector.schedule_self_message(entity=self, message=message, at=at, delay=delay)

    def is_scheduled(self, message):
        return self.sim_context.connector.is_scheduled(message, self)

    def send(self, message, port_name):
        self.ports[port_name].tx_output(message)

    def cancel_scheduled(self, message):
        self.sim_context.connector.cancel_scheduled(message, self)

    def initialize(self, step=0):
        pass