from discrete_sim import SimpleModule, Message, sim_log
from projects.qnum_congestion_ctrl.messages import EntanglementRequestPacket, FlowsInformationPacket


class RequestGenerator(SimpleModule):
    """
    This class models a Random Generator for Entanglement Requests belonging to one or more registered flows
    """

    def __init__(self, name, identifier, flow_descriptors):
        port_names = ["rg0"]

        self.flow_descriptors = self._sanitize_flow_descriptors(flow_descriptors)
        # dict of flow descriptors, indexed by flow_id, each one containing the following fields (for now):
        # - flow_id
        # - source
        # - destination
        # - path (list of node names, including source and destination)
        # - success_probs (list of success probabilities for each link in the path)
        # - request_rate (average, Poisson process)
        # - direction (upstream or downstream)

        self.memos = {}  # dictionary of self messages, one for each flow

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
        if step == 3:
            # here we are sure that all modules have been initialized
            # we can now send the flows information
            flow_desc_cpy = [flow_desc.copy() for flow_desc in self.flow_descriptors.values()]
            message = FlowsInformationPacket(flows=flow_desc_cpy)
            self.send(message, port_name="rg0")
            sim_log.debug(f"Here Request Generator. Sent flows information {message}",
                          time=self.sim_context.time())
            # all subscribed ports will receive a copy of the message

    def _get_self_message(self, flow_id):
        """
        Return the self message for the given flow_id
        """
        return self.memos[flow_id]

    def handle_message(self, message, port_name):
        raise NotImplementedError("RequestGenerator does not handle messages")
