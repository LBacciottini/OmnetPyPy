from discrete_sim import SimpleModule


class RequestGenerator(SimpleModule):
    """
    This class models a Random Generator for Entanglement Requests belonging to one or more registered flows
    """

    def __init__(self, name, identifier, flow_descriptors):
        port_names = ["rg0"]

        self.flow_descriptors = flow_descriptors
        # array of flow descriptors, each one containing the following fields:
        # - flow_id
        # - source_id
        # - destination_id
        # - request_rate (average, Poisson process)

        super().__init__(name, identifier, port_names)

    def initialize(self, step=0):
        if step == 0:
            # TODO: Write here things to be initialized at the beginning of the simulation
            # usually you can retrieve parameters by looking at self.parent attributes (parent is the compound module
            # containing this module)

            """
            TODO: define K self messages, where K is the number of registered flows
            Also get K independent RNGs, and schedule the first message for each flow
            """

            pass

    def handle_message(self, message, port_name):
        # TODO: Write here the code to handle the messages received by the module (also scheduled self messages)

        """
        TODO: for each message received, send out a request and schedule the next message for that flow
        """

        pass

    def set_flow_request_rate(self, flow_id, request_rate):
        for flow_descriptor in self.flow_descriptors:
            if flow_descriptor['flow_id'] == flow_id:
                flow_descriptor['request_rate'] = request_rate
                return True
        return False
