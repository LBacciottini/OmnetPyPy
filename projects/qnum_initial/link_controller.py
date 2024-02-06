from discrete_sim import SimpleModule, Message
from projects.qnum_initial.messages import RoutablePacket, EntanglementGenPacket


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
            self.schedule_message(self._trigger_msg, delay=self.t_clock)

    def _attempt_entanglement(self):

        # In this first implementation, we update the flow probabilities right before each attempt, because we have
        # perfect, real-time information on the queues at the adjacent nodes. In future implementations, we will use a
        # more realistic approach where we update the flow probabilities at regular intervals with reduced information.
        self._update_flow_probabilities()

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
            self.send(EntanglementGenPacket(flow_id=flow_id, lle_id=self._cur_lle_id), "lc0")
            self.send(EntanglementGenPacket(flow_id=flow_id, lle_id=self._cur_lle_id), "lc1")
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
        node_right = self.ports["lc0"].connected_port.parent.ports["B"].connected_port.parent
        node_left = self.ports["lc1"].connected_port.parent.ports["A"].connected_port.parent

        pass

    def _update_flow_probabilities(self):
        """
        Update the flow probabilities based on the information on the queues at the adjacent nodes.
        """
        # First implementation: use _get_queues_info to get the queues status and update the flow probabilities based
        # on the number of requests in the queues.
        # TODO
        pass

    def handle_message(self, message, port_name):

        if port_name is not None and isinstance(message, RoutablePacket):
            # if this is not the destination, forward the packet on the other port
            if message.destination != self.identifier:
                self.send(message, "lc1" if port_name == "lc0" else "lc0")
                return

        elif port_name is None:  # self message, we need to attempt entanglement
            if "header" not in message.meta or message.meta["header"] != self._trigger_msg.meta["header"]:
                raise ValueError("Unknown self message received")
            self._attempt_entanglement()



