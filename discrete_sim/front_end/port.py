"""
This module implements the Port class, which has the same semantic as in omnet++, except that
every port is an object and can does not have to be input or output only.
"""


class Port:

    def __init__(self, name, parent):
        self.name = name
        self.connected_port = None
        self.forwarded_input_port = None
        self.forwarded_output_port = None
        self.parent = parent
        self.subscribed_ports = []
        self.is_subscribed = False

    def connect(self, port):
        if self.is_subscribed:
            raise ValueError("Cannot connect a port that is already subscribed to another port")
        if port.connected_port is not None:
            raise ValueError("Cannot connect a port that is already connected")
        if self.forwarded_output_port:
            raise ValueError("Cannot connect a port that is forwarding output")

        self.connected_port = port
        port.connected_port = self

    def subscribe_to(self, port):
        if self.connected_port is not None:
            raise ValueError("Cannot subscribe a port that is already connected")
        if port.forwarded_output_port:
            raise ValueError("Cannot subscribe to a port that is forwarding output")
        if port.connected_port is not None:
            raise ValueError("Cannot subscribe to a port that is already connected")

        port.subscribed_ports.append(self)
        self.is_subscribed = True

    def disconnect(self, port):
        self.connected_port = None
        port.connected_port = None

    def forward_input(self, port):
        self.forwarded_input_port = port

    def forward_output(self, port):
        self.forwarded_output_port = port

    def tx_output(self, message):

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

        if self.forwarded_input_port:
            self.forwarded_input_port.tx_input(message)
        elif self.parent.is_listening:
            self.parent.sim_context.connector.schedule_port_input(self, message)
        else:
            # do nothing, the mesaage is lost
            pass
