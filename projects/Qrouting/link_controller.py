from discrete_sim import SimpleModule, Message, sim_log
from projects.qnum_congestion_ctrl_aqm_fidelity import messages
from projects.Qrouting.messages import RoutablePacket, EntanglementGenPacket
from projects.qnum_congestion_ctrl_aqm_fidelity.utility import sanitize_flow_descriptors


class LinkController(SimpleModule):
    """
    This class models a Link Controller, placed in the middle of a link.
    """

    def __init__(self, name, identifier):
        port_names = ["lc0", "lc1"]

        super().__init__(name, identifier, port_names)
        self.t_clock = None

        self.attempt_probability = None
        # dictionary of flow attempt probabilities, one for each flow, indexed by flow_id. They must NOT sum to 1.

        self._trigger_msg = Message(["trigger attempt"], header="trigger")

        self._cur_lle_id = 0

    def initialize(self, step=0):
        if step == 0:
            """
            Schedule the first LLEG attempt.
            """
            self.t_clock = self.sim_context.global_params["lleg_attempt_period"]
            first_attempt_time = self.sim_context.rng.random(generator=0) * self.t_clock
            self.schedule_message(self._trigger_msg, delay=first_attempt_time)

            # access global parameters and get the attempt probability and the routing table
            self.attempt_probability = self.sim_context.global_params["lleg_prob"]

    def _attempt_entanglement(self):

        queue_info = self._get_queue_info()

        # check whether the queues are empty. if so, we don't attempt entanglement
        if queue_info.is_empty():
            self.schedule_message(self._trigger_msg, delay=self.t_clock)
            return

        rng = self.sim_context.rng
        link_idx = int(self.name[2])+int(self.name[4])

        # now we flip a coin to decide if the entanglement attempt is successful
        success = rng.random(generator=link_idx + 1) < self.attempt_probability

        # if the attempt is successful, we send an entanglement generation message to the nodes on the other side
        if success:
            lle_id = self.name + "-" + str(self._cur_lle_id)
            self.send(EntanglementGenPacket(lle_id=lle_id, sender_name=self.name), "lc0")
            self.send(EntanglementGenPacket(lle_id=lle_id, sender_name=self.name), "lc1")
            self._cur_lle_id += 1

        # we schedule the next attempt
        self.schedule_message(self._trigger_msg, delay=self.t_clock)

    def _get_queue_info(self):
        """
        Get the information on request queues stored on adjacent nodes available to this link controller.
        """

        # The first implementation is a magic trick where we crawl the network to find references to the adjacent
        # nodes and we directly access their queues. In future implementations, we will use a more realistic approach
        # where we send messages to the adjacent nodes asking for their queue status.

        # veeeeeery ugly and unsafe
        node_left = self.ports["lc0"].connected_port.parent.ports["A"].connected_port.parent

        return node_left.req_queue

    def handle_message(self, message, port_name):

        if port_name is not None and isinstance(message, RoutablePacket):
            # if this is not the destination, forward the packet on the other port
            if message.destination != self.name:
                # print(f"{self.name} forwarding message {message} to {port_name} at time {self.sim_context.time()}")
                self.send(message, "lc1" if port_name == "lc0" else "lc0")
                return

        elif port_name is None:  # self message, we need to attempt entanglement
            if "header" not in message.meta or message.meta["header"] != self._trigger_msg.meta["header"]:
                raise ValueError("Unknown self message received")
            self._attempt_entanglement()




