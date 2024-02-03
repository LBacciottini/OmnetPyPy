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

    def connect(self, port):
        self.connected_port = port
        port.connected_port = self

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
