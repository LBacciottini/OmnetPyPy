from discrete_sim import SimpleModule, Message, sim_log
from projects.qnum_initial.messages import RoutablePacket, EntanglementGenPacket, FlowsInformationPacket


class LinkController(SimpleModule):
    """
    This class models a Link Controller, placed in the middle of a link.
    """

    def __init__(self, name, identifier, t_clock):
        port_names = ["lc0", "lc1", "rg0"]

        super().__init__(name, identifier, port_names)
        self.t_clock = t_clock

        self._flow_probabilities = {}
        # dictionary of flow probabilities, one for each flow, indexed by flow_id. They must sum to 1.

        self._flow_attempt_probabilities = {}
        # dictionary of flow attempt probabilities, one for each flow, indexed by flow_id. They must NOT sum to 1.

        self._trigger_msg = Message(["trigger attempt"], header="trigger")

        self._cur_lle_id = 0

    def initialize(self, step=0):
        if step == 0:
            """
            Schedule the first attempt to entangle the flows
            """
            first_attempt_time = self.sim_context.rng.random(generator=0) * self.t_clock
            self.schedule_message(self._trigger_msg, delay=first_attempt_time)

    def _attempt_entanglement(self):

        # In this first implementation, we update the flow probabilities right before each attempt, because we have
        # perfect, real-time information on the queues at the adjacent nodes. In future implementations, we will use a
        # more realistic approach where we update the flow probabilities at regular intervals with reduced information.
        self._update_flow_probabilities()

        queues_info = self._get_queues_info()

        # check whether the queues are empty. if so, we don't attempt entanglement
        if queues_info[0].is_empty():
            self.schedule_message(self._trigger_msg, delay=self.t_clock)
            return

        # first we pick a flow to attempt entanglement for using the flow probabilities
        rng = self.sim_context.rng
        # we pick the flow_id using the flow probabilities and the default rng (generator = 0)
        flow_id = rng.choices(sequence=list(self._flow_probabilities.keys()),
                              weights=list(self._flow_probabilities.values()),
                              k=1,
                              generator=0)[0]

        # now we flip a coin to decide if the entanglement attempt is successful
        success = rng.random(generator=0) < self._flow_attempt_probabilities[flow_id]

        # if the attempt is successful, we send an entanglement generation message to the nodes on the other side
        if success:
            self.send(EntanglementGenPacket(flow_id=flow_id, lle_id=self._cur_lle_id, sender_name=self.name), "lc0")
            self.send(EntanglementGenPacket(flow_id=flow_id, lle_id=self._cur_lle_id, sender_name=self.name), "lc1")
            self._cur_lle_id += 1

        # we schedule the next attempt
        self.schedule_message(self._trigger_msg, delay=self.t_clock)

    def _get_queues_info(self):
        """
        Get the information on request queues stored on adjacent nodes available to this link controller.
        """

        # The first implementation is a magic trick where we crawl the network to find references to the adjacent
        # nodes and we directly access their queues. In future implementations, we will use a more realistic approach
        # where we send messages to the adjacent nodes asking for their queue status.
        # TODO

        # veeeeeery ugly and unsafe
        node_right = self.ports["lc1"].connected_port.parent.ports["B"].connected_port.parent
        node_left = self.ports["lc0"].connected_port.parent.ports["A"].connected_port.parent

        return node_left.req_queue, node_right.req_queue

    def _update_flow_probabilities(self):
        """
        Update the flow probabilities based on the information on the queues at the adjacent nodes.
        """
        # First implementation: use _get_queues_info to get the queues status and update the flow probabilities based
        # on the number of requests in the queues.
        # TODO
        pass

    def handle_message(self, message, port_name):

        if isinstance(message, FlowsInformationPacket):
            sim_log.debug(f"{self.name} received flows information with {len(message.flows)} flows.",
                          time=self.sim_context.time())
            self._handle_flows_information(message)
            return

        if port_name is not None and port_name != "rg0" and isinstance(message, RoutablePacket):
            # if this is not the destination, forward the packet on the other port
            if message.destination != self.identifier:
                self.send(message, "lc1" if port_name == "lc0" else "lc0")
                return

        elif port_name is None:  # self message, we need to attempt entanglement
            if "header" not in message.meta or message.meta["header"] != self._trigger_msg.meta["header"]:
                raise ValueError("Unknown self message received")
            self._attempt_entanglement()

    def _handle_flows_information(self, message):
        for flow in message.flows:
            if self.name not in flow["path"]:
                continue
            flow_id = flow["flow_id"]
            self._flow_probabilities[flow_id] = 1 / len(message.flows)  # begin with equal probabilities for all flows

            # find our position on the flow path
            path = flow["path"]
            idx = path.index(self.name)
            # the path is node0---(link_first_half)---link_controller---(link_second_half)---node1...
            # the link controller is attached to link_first_half and link_second_half
            # find link position (first + second halves are one link) on the path that this link controller controls
            link_pos = int((idx - 1) / 2)
            # get the success probability for the link
            success_prob = flow["success_probs"][link_pos]
            # update the flow probabilities
            self._flow_attempt_probabilities[flow_id] = success_prob


