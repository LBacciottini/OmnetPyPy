from discrete_sim import SimpleModule, Message, sim_log
from projects.qnum_initial.messages import EntanglementRequestPacket, FlowsInformationPacket


class RequestGenerator(SimpleModule):
    """
    This class models a Random Generator for Entanglement Requests belonging to one or more registered flows
    """

    def __init__(self, name, identifier, flow_descriptors):
        port_names = ["rg0"]

        self.flow_descriptors = self._sanitize_flow_descriptors(flow_descriptors)
        # dict of flow descriptors, indexed by flow_id, each one containing the following fields (for now):
        # - flow_id
        # - source_id
        # - destination_id
        # - path (list of node identifiers)
        # - success_probs (list of success probabilities for each link in the path)
        # - request_rate (average, Poisson process)

        self.memos = {}  # dictionary of self messages, one for each flow

        self.generators = {}  # dictionary of independent RNGs, one for each flow

        super().__init__(name, identifier, port_names)

    @staticmethod
    def _sanitize_flow_descriptors(flow_descriptors):
        """
        Sanitize the flow_descriptors parameter, transforming it into a dictionary indexed by flow_id
        """
        if isinstance(flow_descriptors, list):
            flow_descriptors_dict = {}
            for flow_descriptor in flow_descriptors:
                flow_descriptors_dict[flow_descriptor['flow_id']] = flow_descriptor
        elif isinstance(flow_descriptors, dict):
            flow_descriptors_dict = flow_descriptors
        else:
            raise ValueError("flow_descriptors must be a list or a dictionary")

        # check if the dictionary is well-formed
        for flow_id, flow_descriptor in flow_descriptors_dict.items():
            if 'flow_id' not in flow_descriptor:
                raise ValueError("flow_descriptor must contain a flow_id key")
            elif flow_descriptor['flow_id'] != flow_id:
                raise ValueError("flow_id in flow_descriptor does not match the key in the dictionary")

        return flow_descriptors_dict

    def initialize(self, step=0):
        if step == 0:
            """
            define K self messages, where K is the number of registered flows
            Also use K independent RNGs, and schedule the first message for each flow as independent
            Poisson processes
            """

            for i, flow_descriptor in enumerate(self.flow_descriptors.values()):
                self.memos[flow_descriptor['flow_id']] = Message(["request"], header=flow_descriptor['flow_id'])
                self.generators[flow_descriptor['flow_id']] = i+1  # we use the index as the generator number
                next_interarrival_time = self._next_interarrival_time(flow_descriptor['flow_id'])
                self.schedule_message(message=self._get_self_message(flow_descriptor['flow_id']),
                                      delay=next_interarrival_time)

        elif step == 3:
            # here we are sure that all modules have been initialized
            # we can now send the flows information
            flow_desc_cpy = [flow_desc.__copy__() for flow_desc in self.flow_descriptors.values()]
            message = FlowsInformationPacket(flows=flow_desc_cpy)
            self.send(message, port_name="rg0")
            # all subscribed ports will receive a copy of the message

    def _get_self_message(self, flow_id):
        """
        Return the self message for the given flow_id
        """
        return self.memos[flow_id]

    def _next_interarrival_time(self, flow_id):
        """
        Return the next interarrival time for the given flow_id
        """
        flow_descriptor = self.flow_descriptors[flow_id]
        generator = self.generators[flow_id]
        average_time = self.sim_context.time_unit_factor / flow_descriptor['request_rate']
        return self.sim_context.rng.expovariate(lambd=average_time, generator=generator)

    def handle_message(self, message, port_name):

        if port_name is None:  # self message, we need to generate a request for the flow
            flow_id = message.header

            sim_log.debug(f"Request generated for flow {flow_id}", time=self.sim_context.time())
            destination = self.flow_descriptors[flow_id]['path'][0]  # we assume to be attached
            # to the first node on the path
            request_pkt = EntanglementRequestPacket(destination=destination, flow_id=flow_id)
            self.send(message=request_pkt, port_name="rg0")

            # schedule the next request arrival
            next_interarrival_time = self._next_interarrival_time(flow_id)
            self.schedule_message(message=self._get_self_message(flow_id),
                                  delay=next_interarrival_time)

    def set_flow_request_rate(self, flow_id, request_rate):
        for flow_descriptor in self.flow_descriptors:
            if flow_descriptor['flow_id'] == flow_id:
                flow_descriptor['request_rate'] = request_rate
                return True
        return False
