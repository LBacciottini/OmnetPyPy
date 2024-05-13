from discrete_sim import SimpleModule, sim_log, Message
import projects.qnum_congestion_ctrl_aqm_bidir.messages as messages
from projects.qnum_congestion_ctrl_aqm_bidir.aqm_controller import PIController
from projects.qnum_congestion_ctrl_aqm_bidir.congestion_controller import WindowCongestionController, \
    RateCongestionController
from projects.qnum_congestion_ctrl_aqm_bidir.queues import RequestQueue, LLEManager
from projects.qnum_congestion_ctrl_aqm_bidir.utility import sanitize_flow_descriptors


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

        port_names = ["q0", "q1"]
        # first dilemma: do we use separate channels for classical packets  (c0, c1 ports) ?
        # rg0 is used to attach the RequestGenerator

        super().__init__(name, identifier, port_names)
        self.flows_info = None
        self.lle_manager = LLEManager(port_names=["q0", "q1"])
        self.req_queue = RequestQueue()
        self.storage_qbits_per_port = storage_qbits_per_port

        ################################
        # CONGESTION CONTROL VARIABLES #
        ################################
        self.congestion_controller = RateCongestionController()

        self.cur_req_ids = {}  # dictionary of current request ids, one for each flow, indexed by flow_id, used to
        # keep track of which id assign to the next generated request for each flow
        self.timeout_trigger_msg = Message(["timeout control trigger"], header="timeout control trigger")
        self.timeout_trigger_period = 20000  # us
        self.last_update_time = 0
        ################################
        # END OF CONGESTION CONTROL    #
        ################################

        ################################
        # ACTIVE QUEUE MGMT VARIABLES  #
        ################################
        self.aqm_controllers = None
        self.AQM_T_sampling_times = None
        self.AQM_update_msgs = None
        ################################
        # END OF AQM VARIABLES         #
        ################################

        ################################
        # NEW FLOW GENERATION          #
        ################################
        self.new_flow_trigger_msg = Message(["new flow trigger"], header="new flow trigger")
        self.new_flow_trigger_period = 8000000  # us
        self.delete_phase = False
        ################################
        # END OF NEW FLOW GENERATION    #
        ################################

        ################################
        # NEW REQUEST GENERATION       #
        ################################
        self.new_request_trigger_msgs = {}
        self.increase_request_rate_trigger_msgs = {}
        ################################
        # END OF NEW REQUEST GENERATION #
        ################################

    def initialize(self, step=0):
        if step == 0:
            # usually you can retrieve parameters by looking at self.parent attributes (parent is the compound module
            # containing this module)

            # access global parameters and get the flows information
            flow_descriptors = self.sim_context.global_params["flow_descriptors"]
            flow_descriptors = sanitize_flow_descriptors(flow_descriptors)
            # dict of flow descriptors, indexed by flow_id, each one containing the following fields (for now):
            # - flow_id
            # - source
            # - destination
            # - path (list of node names, including source and destination)
            # - success_probs (list of success probabilities for each link in the path)
            # - direction (upstream or downstream)

            message = messages.FlowsInformationPacket(destination=self.name, flows=flow_descriptors)
            self._handle_flows_information(message)

            self.schedule_message(self.timeout_trigger_msg, delay=self.timeout_trigger_period)

            self.aqm_controllers = {
                "upstream": PIController(),
                "downstream": PIController()
            }
            aqm_params = self.sim_context.global_params["aqm_params"]
            self.AQM_T_sampling_times = {
                "upstream": (self.aqm_controllers["upstream"].set_parameters(**aqm_params))*self.sim_context.time_unit_factor,
                "downstream": (self.aqm_controllers["downstream"].set_parameters(**aqm_params))*self.sim_context.time_unit_factor
            }
            self.AQM_update_msgs = {
                "upstream": Message(["downstream"], header="update AQM downstream"),
                "downstream": Message(["upstream"], header="update AQM upstream")
            }

            for direction in ["upstream", "downstream"]:
                self._schedule_aqm_update(direction)

            self.schedule_message(self.new_flow_trigger_msg, delay=self.new_flow_trigger_period)

    def _schedule_aqm_update(self, direction):
        """
        Schedule the next AQM update for the given direction
        """
        self.schedule_message(self.AQM_update_msgs[direction], delay=self.AQM_T_sampling_times[direction])

    def handle_message(self, message, port_name):

        if isinstance(message, messages.FlowsInformationPacket) and message.destination == self.name:
            self._handle_flows_information(message)
            return

        if isinstance(message, messages.FlowDeletionPacket) and message.destination == self.name:
            self._handle_flow_deletion(message)
            return

        if "header" in message.meta and message.meta["header"] == "initialize requests":
            # we generate the first requests for each flow for which we are the source
            for flow_id in self.flows_info:
                if self.name == self.flows_info[flow_id]["source"]:
                    if not isinstance(self.congestion_controller, RateCongestionController):
                        self.generate_request(flow_id)
                    else:
                        # schedule the next request generation
                        self.schedule_message(self.new_request_trigger_msgs[flow_id],
                                              delay=self.congestion_controller.get_inter_request_gap(flow_id=flow_id))
                        # schedule the next increase in the flow rate
                        self.schedule_message(self.increase_request_rate_trigger_msgs[flow_id],
                                              delay=self.congestion_controller.estimated_rtt[flow_id])
            return

        if "header" in message.meta and message.meta["header"] == "new flow trigger":
            self._generate_new_flow()
            self.schedule_message(self.new_flow_trigger_msg, delay=self.new_flow_trigger_period)
            return

        if "header" in message.meta and message.meta["header"] == "new requests trigger":

            if message.fields[0] not in self.flows_info:
                # the flow has been deleted
                del self.new_request_trigger_msgs[message.fields[0]]
                return

            self.generate_request(flow_id=message.fields[0])
            delay = self.congestion_controller.get_inter_request_gap(flow_id=message.fields[0])
            self.schedule_message(message, delay=delay)
            return

        if "header" in message.meta and message.meta["header"] == "increase flow rate trigger":
            if not isinstance(self.congestion_controller, RateCongestionController):
                raise ValueError("The global rate increase period is set but the congestion controller"
                                 "is not a RateCongestionController")

            if message.fields[0] not in self.flows_info:
                # the flow has been deleted
                del self.increase_request_rate_trigger_msgs[message.fields[0]]
                return

            flow_id = message.fields[0]
            self.congestion_controller.increase_congestion_knob(flow_id=message.fields[0],
                                                                current_time=self.sim_context.time())
            # get estimated rtt
            rtt = self.congestion_controller.estimated_rtt[flow_id]
            # schedule the next increase for the estimated rtt

            self.schedule_message(message, delay=rtt)
            return

        if port_name is None and message.meta["header"].startswith("update AQM"):
            direction = message.fields[0]
            current_q_len = self.req_queue.weighted_length(direction=direction)
            self.aqm_controllers[direction].update(q=current_q_len)
            self._schedule_aqm_update(direction)
            return

        if isinstance(message, messages.RoutablePacket) and message.destination != self.name:
            # if this is not the destination, forward the packet on the other port
            self.send(message, "q1" if port_name == "q0" else "q0")
            return

        if isinstance(message, messages.EntanglementRequestPacket):
            self._handle_entanglement_request(message, port_name)
            return

        if isinstance(message, messages.EntanglementGenPacket):
            self._handle_new_lle(message, port_name)
            return

        if isinstance(message, messages.EntanglementGenAcknowledgement):
            self._handle_req_ack(message, port_name)
            return

        if "header" in message.meta and message.meta["header"] == "timeout control trigger":
            self.collect_timeouts()
            return

        else:
            raise ValueError(f"Unknown message received: {message} at node {self.name}")

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
            if self.name == flow["source"] or self.name == flow["destination"]:
                self.congestion_controller.setup_congestion_control(flow, current_time=self.sim_context.time())
                self.cur_req_ids[flow_id] = 0 if self.name == flow["source"] else 100000  # avoid conflicts
                self.new_request_trigger_msgs[flow_id] = Message([flow_id], header="new requests trigger")
                self.increase_request_rate_trigger_msgs[flow_id] = Message([flow_id], header="increase flow rate trigger")
            else:
                next_hop = None
            # next hop in the path, +2 because the path includes the link controllers

            flow_info[flow_id] = {
                "next_port": next_port,
                "source": flow["source"],
                "destination": flow["destination"],
                "success_probs": flow["success_probs"],
                "direction": flow["direction"],
                "path": flow["path"]
            }

        was_init = False
        if self.flows_info is None:
            self.flows_info = flow_info
            was_init = True
        else:
            self.flows_info.update(flow_info)

        sim_log.debug(f"{self.name} received flows information with {len(relevant_flows)} relevant flows.",
                      time=self.sim_context.time())

        # we generate the first requests for each flow for which we are the source
        # but we wait for a little time to let the other nodes initialize
        if was_init:
            self.schedule_message(Message(["initialize requests"], header="initialize requests"), delay=10)
        else:
            for flow_id in flow_info:
                if self.name == flow_info[flow_id]["source"] or self.name == flow_info[flow_id]["destination"]:
                    if not isinstance(self.congestion_controller, RateCongestionController):
                        self.generate_request(flow_id)
                    else:
                        # schedule the next request generation
                        self.schedule_message(self.new_request_trigger_msgs[flow_id],
                                              delay=self.congestion_controller.get_inter_request_gap(flow_id=flow_id))
                        # schedule the next increase in the flow rate
                        self.schedule_message(self.increase_request_rate_trigger_msgs[flow_id],
                                              delay=self.congestion_controller.estimated_rtt[flow_id])

    def _handle_flow_deletion(self, message):
        """
        This method is called when a FlowDeletionPacket is received
        """
        flow_id = message.flow_id
        if flow_id in self.flows_info:

            # if we are the source of the flow, we have to delete the flow from the congestion controller
            # and cancel the scheduled messages
            if self.name == self.flows_info[flow_id]["source"]:
                self.congestion_controller.delete_flow(flow_id)

            # delete all requests in the queue for the flow and all the LLEs
            self.req_queue.delete_requests(flow_id)
            self.lle_manager.delete_lles(flow_id)

            # delete the flow information
            del self.flows_info[flow_id]
            sim_log.debug(f"Flow {flow_id} deleted at node {self.name}", time=self.sim_context.time())
        else:
            sim_log.error(f"Flow {flow_id} not found at node {self.name}", time=self.sim_context.time())
            raise ValueError(f"Flow {flow_id} not found at node {self.name}")


    def generate_request(self, flow_id):
        """
        Generate a request for the given flow_id
        """
        # generate a new request
        req_id = self.cur_req_ids[flow_id]
        self.cur_req_ids[flow_id] += 1

        # check whether we are the source or the destination of the flow
        if self.name == self.flows_info[flow_id]["source"]:
            direction = "upstream"
        else:
            direction = "downstream"

        destination = self._next_hop(flow_id=flow_id, direction=direction)
        assert destination is not None, "Destination not found"
        request_pkt = messages.EntanglementRequestPacket(destination=destination, flow_id=flow_id, req_id=req_id,
                                                         lle_id=None, gen_time=self.sim_context.time())

        # set the success probabilities as a meta field
        request_pkt.meta["success_probs"] = self.flows_info[flow_id]["success_probs"][:]

        request_pkt.meta["direction"] = direction

        # send the request to ourselves
        self._handle_new_request(request_pkt)

        # let the congestion controller know that a new request has been generated
        self.congestion_controller.handle_new_request_in_flight(req_id=req_id, flow_id=flow_id,
                                                                current_time=self.sim_context.time())


    def collect_timeouts(self):
        """
        Collect the timeouts for the requests in flight and update the congestion windows for the involved flows
        """
        self.congestion_controller.collect_timeouts(self.sim_context.time())
        self.schedule_message(self.timeout_trigger_msg, delay=self.timeout_trigger_period)

        if self.last_update_time + 20000 <= self.sim_context.time():
            self.last_update_time = self.sim_context.time()
            # log some simulation updates for the user
            sim_log.debug(f"Node {self.name} has currently {len(self.req_queue)} requests in queue and {len(self.lle_manager)} LLEs",
                          time=self.sim_context.time())
            # for all flows of which we are the source, we log the current generation probability
            for flow_id in self.flows_info:
                if self.name == self.flows_info[flow_id]["source"] and isinstance(self.congestion_controller, RateCongestionController):
                    p_gen = self.congestion_controller.get_inter_request_gap(flow_id=flow_id)
                    sim_log.debug(f"Node {self.name} has an IRG = {p_gen} us for flow {flow_id}",
                                  time=self.sim_context.time())

    def _generate_new_flow(self, num_flows=3):
        """
        Generate a new flow by copying the first one of which this node is the source
        """
        # if total number of flows is equal or greater than 13, we delete the last num_flows flows for which we are the source
        if len(self.flows_info) >= 13:
            self.delete_phase = True

        if len(self.flows_info) == 4 and self.delete_phase:
            self.delete_phase = False

        if self.delete_phase:
            flow_ids = list(self.flows_info.keys())
            # sort the flow_ids in descending order
            flow_ids.sort(reverse=True)
            to_delete = num_flows
            for f_id in flow_ids:
                if self.name == self.flows_info[f_id]["source"] and to_delete > 0:
                    # delete flow message
                    flow = self.flows_info[f_id]
                    for destination in flow["path"]:
                        del_flow_info = messages.FlowDeletionPacket(destination=destination, flow_id=f_id)
                        if destination == self.name:
                            self._handle_flow_deletion(del_flow_info)
                            continue
                        if flow["direction"] == "upstream":
                            self.send(del_flow_info, port_name="q1")
                        else:
                            self.send(del_flow_info, port_name="q0")
                    to_delete -= 1
            return


        # we just copy the first flow for which we are the source
        flow_id = None
        for f_id in self.flows_info:
            if self.name == self.flows_info[f_id]["source"]:
                flow_id = f_id
                break

        if flow_id is None:
            return

        flow = self.flows_info[flow_id]

        for _ in range(num_flows):
            new_flow = flow.copy()
            if new_flow["direction"] == "upstream":
                new_flow["flow_id"] = len(self.flows_info)
            else:
                new_flow["flow_id"] = len(self.flows_info) + num_flows
            self.flows_info[new_flow["flow_id"]] = new_flow

            # send the new flow information to the other nodes
            for destination in new_flow["path"]:
                new_flow_info = messages.FlowsInformationPacket(destination=destination, flows=[new_flow])

                if destination == self.name:
                    self._handle_flows_information(new_flow_info)
                    continue

                # it will be routed to the destination node
                if new_flow["direction"] == "upstream":
                    self.send(new_flow_info, port_name="q1")
                else:
                    self.send(new_flow_info, port_name="q0")

            sim_log.debug(f"Node {self.name} generated a new flow {new_flow['flow_id']}",
                          time=self.sim_context.time())

    def _handle_entanglement_request(self, message, port_name):
        """
        This method is called when an EntanglementRequestPacket is received
        """

        flow_id = message.flow_id

        assert flow_id in self.flows_info, f"Flow {flow_id} not found in the flows information"
        assert port_name != self.flows_info[flow_id]["next_port"], "Received a request from the wrong port"

        """
        sim_log.debug(f"Request {message.req_id} received for flow {flow_id}. Here is node {self.name}",
                      time=self.sim_context.time())
        """

        # first of all we pop the first success probability from the request meta because it won't be used anymore
        message.meta["success_probs"].pop(0)

        # first thing: check whether the request's LLE is still available, it might have been dropped due to storage
        # qubit shortage
        lle, lle_time = self.lle_manager.peek_from_req(request=message, raise_error=False)
        if lle is None:
            # the lle has been dropped because of storage qubit shortage. We have to drop the request
            return

        # emit the queue size metric
        if self.name == "qn2":
            self.emit_metric("queue_size", self.req_queue.weighted_length(direction="upstream"))

        # now let's check whether we should mark the request as congested
        if not message.is_congested():
            direction = message.meta["direction"]
            aqm = self.aqm_controllers[direction]
            marking_prob = aqm.get_marking_probability()
            # use the i-th random number generator offered by the sim_context
            # to check whether the request should be marked as congested


            if self.sim_context.rng.random(generator=flow_id) < marking_prob:
                message.mark_congested()



        if self.name == self.flows_info[flow_id]["destination"]:
            # we are the destination, we are done :)
            # pop the lle the request refers to from the available lles and emit 1
            lle, lle_time = self.lle_manager.pop_from_req(request=message, raise_error=True)
            self.emit_metric(name="throughput", value=1)

            self.emit_metric("latency", self.sim_context.time() - message.gen_time)

            # generate and send the acknowledgement
            destination = self.flows_info[flow_id]["source"]
            ack = messages.EntanglementGenAcknowledgement(req_id=message.req_id, flow_id=flow_id,
                                                          destination=destination,
                                                          congested=message.is_congested(),
                                                          gen_time=message.gen_time)
            self.send(ack, port_name=port_name)

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
            raise ValueError(f"New request for which we are not the source: {message} at node {self.name}")

        """
        sim_log.debug(f"Request generated for flow {flow_id}. Here is node {self.name} with a queue empty? {self.req_queue.is_empty()}",
                      time=self.sim_context.time())
        """

        # now let's check whether we should mark the request as congested
        if not message.is_congested():
            direction = message.meta["direction"]
            aqm = self.aqm_controllers[direction]
            marking_prob = aqm.get_marking_probability()
            # use the i-th random number generator offered by the sim_context
            # to check whether the request should be marked as congested

            if self.sim_context.rng.random(generator=flow_id) < marking_prob:
                message.mark_congested()



        # we are the source, we have to check whether we have a lle to associate with the request
        # if so, we associate the lle and send the request to the next node
        next_port = "q1" if message["direction"] == "upstream" else "q0"

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

        # first of all we have to check whether the flow is still active
        if flow_id not in self.flows_info:
            # the flow has been deleted
            # do nothing
            return

        if (not message.is_owner) or self.req_queue.is_empty(flow_id=flow_id):  # no requests for this flow :(
            # append
            self.add_lle(message, port_name)
            """# if flow is upstream and port_name is q1 we raise an error
            if self.flows_info[flow_id]["direction"] == "upstream" and port_name == "q1":
                print("Maybe About to raise error. The interested queue is", self.req_queue._requests)
                print("The LLE msg is ", message)
                raise ValueError(f"{self.name} Received a new lle for flow {flow_id} on {port_name} for which there are no requests")
            # if flow is downstream and port_name is q0 we raise an error
            if self.flows_info[flow_id]["direction"] == "downstream" and port_name == "q0":
                print("About to raise error. The interested queue is", self.req_queue._requests)
                print("The LLE msg is ", message)
                raise ValueError(f"{self.name} Received a new lle for flow {flow_id} on {port_name} for which there are no requests")"""
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

    def _handle_req_ack(self, message, port_name):
        """
        This method is called when an EntanglementGenAcknowledgement is received
        """
        flow_id = message.flow_id

        if flow_id not in self.flows_info:
            sim_log.warning(f"Received an acknowledgement for a flow not in the flows information: {message} at node {self.name}",
                            time=self.sim_context.time())
            return

        # first we check whether we are the source of the flow, otherwise we throw an error
        if self.name != self.flows_info[flow_id]["source"]:
            raise ValueError(f"Received an acknowledgement for a flow for which we are not"
                             f"the source: {message} at node {self.name}")

        num_new_requests = self.congestion_controller.handle_ack(req_id=message.req_id, flow_id=flow_id,
                                                                 mark_congested=message.congested,
                                                                 current_time=self.sim_context.time(),
                                                                 time_sent=message.gen_time)

        # emit the congestion window for flow 0
        if flow_id == 0 and isinstance(self.congestion_controller, WindowCongestionController):
            self.emit_metric("congestion_window", self.congestion_controller.get_congestion_window(flow_id))

        elif flow_id == 0 and isinstance(self.congestion_controller, RateCongestionController):
            self.emit_metric("IRG", self.congestion_controller.get_inter_request_gap(flow_id))

        # we generate new requests for the flow
        for _ in range(num_new_requests):
            self.generate_request(flow_id)

    def _next_hop(self, flow_id, direction):
        """
        Return the next hop for the given flow and direction
        """
        if direction == "upstream" and self.name != self.flows_info[flow_id]["destination"]:
            return self.flows_info[flow_id]["path"][self.flows_info[flow_id]["path"].index(self.name) + 1]
        elif direction == "downstream" and self.name != self.flows_info[flow_id]["source"]:
            return self.flows_info[flow_id]["path"][self.flows_info[flow_id]["path"].index(self.name) - 1]
        else:
            return None
