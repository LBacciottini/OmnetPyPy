from discrete_sim import SimpleModule, sim_log
import projects.qnum_finite_mem.messages as messages
from projects.qnum_finite_mem.queues import RequestQueue, LLEManager


class QuantumNode(SimpleModule):
    """
    This class models a Quantum Repeater along a repeater chain

    Parameters
    ----------
    name : str
        The name of the module
    identifier : int
        The identifier of the module
    storage_qbits_per_port : int or None, optional
        The number of  storage qubits available on each port. If None, the module will assume an infinite storage
        capacity. Default is None.
    """

    def __init__(self, name, identifier, storage_qbits_per_port=None):

        port_names = ["q0", "q1", "rg0"]
        # first dilemma: do we use separate channels for classical packets  (c0, c1 ports) ?
        # rg0 is used to attach the RequestGenerator

        super().__init__(name, identifier, port_names)
        self.flows_info = None
        self.lle_manager = LLEManager(port_names=["q0", "q1"])
        self.req_queue = RequestQueue()
        self.storage_qbits_per_port = storage_qbits_per_port

    def initialize(self, step=0):
        if step == 0:
            # TODO: Write here things to be initialized at the beginning of the simulation
            # usually you can retrieve parameters by looking at self.parent attributes (parent is the compound module
            # containing this module)
            pass

    def handle_message(self, message, port_name):

        if isinstance(message, messages.FlowsInformationPacket):
            self._handle_flows_information(message)
            return

        if port_name == "rg0":
            # we have to handle a newly generated request
            self._handle_new_request(message)
            return

        if isinstance(message, messages.EntanglementRequestPacket):
            self._handle_entanglement_request(message, port_name)
            return

        if isinstance(message, messages.EntanglementGenPacket):
            self._handle_new_lle(message, port_name)
            return

    def _handle_flows_information(self, message):
        """
        This method is called when a FlowsInformationPacket is received
        """
        # among all flows, we only keep those that are relevant to this node
        # (i.e. the flows where the current node is part of the path)
        relevant_flows = {}
        for flow in message.flows:
            if self.name in flow["path"]:
                relevant_flows[flow["flow_id"]] = flow

        flow_info = {}
        for flow_id in relevant_flows:
            flow = relevant_flows[flow_id]
            next_port = "q0" if flow["direction"] == "downstream" else "q1"
            if self.name != flow["destination"]:
                next_hop = flow["path"][flow["path"].index(self.name) + 2]
            else:
                next_hop = None
            # next hop in the path, +2 because the path includes the link controllers

            flow_info[flow_id] = {
                "request_rate": flow["request_rate"],
                "next_port": next_port,
                "source": flow["source"],
                "destination": flow["destination"],
                "next_hop": next_hop
            }

        self.flows_info = flow_info

        """
        sim_log.debug(f"{self.name} received flows information with {len(relevant_flows)} relevant flows.",
                      time=self.sim_context.time())
        """

    def _handle_entanglement_request(self, message, port_name):
        """
        This method is called when an EntanglementRequestPacket is received
        """

        # check if we are the flow destination. In this case we are happy
        flow_id = message.flow_id

        assert flow_id in self.flows_info, f"Flow {flow_id} not found in the flows information"
        assert port_name != self.flows_info[flow_id]["next_port"], "Received a request from the wrong port"

        # first thing: check whether the request's LLE is still available, it might have been dropped due to storage
        # qubit shortage
        lle, lle_time = self.lle_manager.peek_from_req(request=message, raise_error=False)
        if lle is None:
            # the lle has been dropped because of storage qubit shortage. We have to drop the request
            return

        if self.name == self.flows_info[flow_id]["destination"]:
            # we are the destination, we are done :)
            # pop the lle the request refers to from the available lles and emit 1
            lle, lle_time = self.lle_manager.pop_from_req(request=message, raise_error=True)
            self.emit_metric(name="throughput", value=1)
            """
            sim_log.debug(f"Request {message.req_id} satisfied for flow {flow_id}. Here is node {self.name}",
                          time=self.sim_context.time())
            """
            return

        assert self.name != self.flows_info[flow_id]["source"], "The source of a flow was forwarded a request"

        # we have to check whether we have a lle to swap with the request
        # if so, we swap, update the message information and forward the request to the next node
        next_port = self.flows_info[flow_id]["next_port"]
        if self.lle_manager.is_empty(port_name=next_port, flow_id=flow_id):
            # just append the request to the corresponding queue
            self.req_queue.add_request(message, self.sim_context.time())
            return

        # there is at least a lle for this flow that can be swapped with the request
        # pop the lle for the request
        peeked = self.lle_manager.peek_lle(port_name=next_port, flow_id=flow_id,
                                           policy=LLEManager.YOUNGEST)
        lle, lle_time = self.lle_manager.pop_from_req(request=message, raise_error=True)

        # pop the youngest suitable lle
        other_lle, other_lle_time = self.lle_manager.pop_lle(port_name=next_port, flow_id=flow_id,
                                                             policy=LLEManager.YOUNGEST)
        # update request
        wait_time = self.sim_context.time() - other_lle_time
        message.update_request(lle_id=other_lle.lle_id, wait_time=wait_time,
                               destination=self.flows_info[flow_id]["next_hop"])
        # send the message
        self.send(message, port_name=next_port)

        # emit queueing time for the request (only intermediate repeater)
        if self.name == "qn1":
            self.emit_metric("queuing_time", 0.0)

    def _handle_new_request(self, message):
        flow_id = message.flow_id

        # if we are not the source we ignore the request
        if flow_id not in self.flows_info or self.name != self.flows_info[flow_id]["source"]:
            return

        """
        sim_log.debug(f"Request generated for flow {flow_id}. Here is node {self.name} with a queue empty? {self.req_queue.is_empty()}",
                      time=self.sim_context.time())
        """

        # we are the source, we have to check whether we have a lle to associate with the request
        # if so, we associate the lle and send the request to the next node
        next_port = self.flows_info[flow_id]["next_port"]
        if self.lle_manager.is_empty(port_name=next_port, flow_id=flow_id):
            # just append the request to the corresponding queue
            self.req_queue.add_request(message, self.sim_context.time())
            return

        # there is at least an lle for this flow that can be assigned to the request
        # pop the lle
        lle, lle_time = self.lle_manager.pop_lle(port_name=next_port, flow_id=message.flow_id,
                                                 policy=LLEManager.YOUNGEST)
        # update request
        message.update_request(lle_id=lle.lle_id, wait_time=None,
                               destination=self.flows_info[flow_id]["next_hop"])
        # send the message
        self.send(message, port_name=next_port)

    def _handle_new_lle(self, message, port_name):
        """
        This method is called when an EntanglementGenPacket is received
        """
        flow_id = message.flow_id
        # we have to check whether there is a request to be swapped with this lle
        # if so, we swap, update the message information and forward the request to the next node

        # self._check_queues_size()

        if self.req_queue.is_empty(flow_id=flow_id):  # no requests for this flow :(
            # append
            self.add_lle(message, port_name)
            return

        # there is at least a request for this flow
        # check whether the new lle is in the flow direction (i.e., it can be swapped with the request lle)
        next_port = self.flows_info[flow_id]["next_port"]
        if port_name != next_port:
            # we just append the new lle
            self.add_lle(message, port_name)
            return

        # now we are sure that the new lle is in the flow direction we were waiting for and there is a request for it

        # pop the request from the queue
        request, request_time = self.req_queue.pop_request(flow_id, policy=RequestQueue.OLDEST)

        # Now we have to check whether we are the source of the flow
        if self.name == self.flows_info[flow_id]["source"]:
            # in this case we just have to associate the new lle to the request and send it to the next node
            request.update_request(lle_id=message.lle_id, wait_time=None,
                                   destination=self.flows_info[flow_id]["next_hop"])
            self.send(request, port_name=next_port)
            return

        # we are not the source, we have to pop the lle associated with the request
        # pop lle associated to the popped request
        other_lle, other_lle_time = self.lle_manager.pop_from_req(request=request, raise_error=True)

        # swap the lles
        # update the request message by adding the swapped lle wait time
        wait_time = self.sim_context.time() - other_lle_time

        # update the request message
        request.update_request(lle_id=message.lle_id, wait_time=wait_time,
                               destination=self.flows_info[flow_id]["next_hop"])
        # send the message
        self.send(request, port_name=next_port)

        # emit queueing time for the request (only intermediate repeater)
        if self.name == "qn1":
            self.emit_metric("queuing_time", self.sim_context.time() - request_time)

    def add_lle(self, lle, port_name):
        """
        Add an LLE to the manager. If there are no free storage qubits, we try to pop the oldest lle for the same flow
        and replace it with the new one. If there are no lles for the same flow, we pop the oldest lle
        for that port and replace it with the new one.

        Parameters
        ----------
        lle : EntanglementGenPacket
            The LLE to add
        port_name : str
            The name of the port on which the LLE is available
        """

        if self.storage_qbits_per_port is not None:
            if self.lle_manager.length(port_name) >= self.storage_qbits_per_port:
                # we have to pop the oldest lle for the same flow
                # if there are no lles for the same flow, we pop the oldest lle for that port
                # if there are no lles for that port, we raise an error
                lle_to_pop, _ = self.lle_manager.pop_lle(port_name=port_name, flow_id=lle.flow_id,
                                                      policy=LLEManager.OLDEST)
                if lle_to_pop is None:
                    # we have to pop the oldest lle for that port
                    lle_to_pop, _ = self.lle_manager.pop_lle(port_name=port_name, policy=LLEManager.OLDEST)
                    if lle_to_pop is None:
                        raise ValueError("No LLEs available for popping")

                # now we have to check whether the popped lle is associated with a request
                # if so, we have to drop the request
                request, _ = self.req_queue.pop_from_lle(lle_to_pop, raise_error=False)
                self.lle_manager.add_lle(lle, port_name, self.sim_context.time())
                return

        self.lle_manager.add_lle(lle, port_name, self.sim_context.time())