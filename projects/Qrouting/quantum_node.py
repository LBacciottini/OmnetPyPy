from bell_diag_api.decoherence import depolarize_rate
from bell_diag_api.swapping import swap
from bell_diag_api.utility import epr_pair, get_werner_state
from discrete_sim import SimpleModule, sim_log, Message
from projects.Qrouting.queues import RequestQueue, LLEManager
import projects.Qrouting.messages as messages


class QuantumNode(SimpleModule):
    """
    This class models a Quantum Repeater along a repeater chain

    Parameters
    ----------
    name : str
        The name of the module
    identifier : int
        The identifier of the module
    storage_qbits : int or None, optional
        The number of  storage qubits available. If None, the module will assume an infinite storage capacity.
        Default is None.
    num_ports : int, optional
        The number of ports of the device. Default is 2
    decoherence_rate : float, optional
        The decoherence rate of the quantum states. Default is 0.
    use_agent : bool, optional
        Whether to use the Q-routing agent for routing. Default is False. If False, the module will use the
        shortest path routing algorithm.
    """

    def __init__(self, name, identifier, storage_qbits=None, num_ports=2, decoherence_rate=0., use_agent=False):

        port_names = [f"q{i}" for i in range(num_ports)]

        super().__init__(name, identifier, port_names)
        self.lle_manager = LLEManager(port_names=port_names)
        self.req_queue = RequestQueue()
        self.storage_qbits = storage_qbits
        self.decoherence_rate = decoherence_rate

        self.routing_table = None
        self.distance_vector = None

        self.should_use_agent = use_agent
        if self.should_use_agent == "True" or self.should_use_agent == "true":
            self.should_use_agent = True
        elif self.should_use_agent == "False" or self.should_use_agent == "false":
            self.should_use_agent = False

        #################################
        # REQUEST GENERATION (ONLY qn0) #
        #################################
        if self.name == "qn0":
            self._request_gen_msg = Message(["generate request"], header="generate request")
            self._last_request_time = 0
            self._avg_interarrival_time = None
            self._next_request_id = 0

    def initialize(self, step=0):
        if step == 0:
            # usually you can retrieve parameters by looking at self.parent attributes (parent is the compound module
            # containing this module)

            # load the routing table
            for routing_dict in self.sim_context.global_params["routing_tables"]:
                if routing_dict["node"] == self.name:
                    self.routing_table = routing_dict["routing_table"]
                    break

            # load the distance vector
            for distance_dict in self.sim_context.global_params["distance_vectors"]:
                if distance_dict["node"] == self.name:
                    self.distance_vector = distance_dict["distance_vector"]
                    break

            if self.name == "qn0":
                # schedule the first request generation
                self.schedule_message(self._request_gen_msg, delay=5)

            sim_log.info(f"Node {self.name} initialized", time=self.sim_context.time())

    def handle_message(self, message, port_name):
        if isinstance(message, messages.RoutablePacket) and message.destination != self.name:
            # if this is not the destination, forward the packet on the other port
            next_port, _ = self._route_shortest_path(message.destination)
            self.send(message, next_port)
            return

        if message.meta["header"] == "generate request":
            # generate a new request
            self._generate_new_request()
            self._next_request_id += 1

            if self._avg_interarrival_time is None:
                self._avg_interarrival_time = self.sim_context.global_params["avg_request_interarrival_time"]

            # schedule the next request generation
            interarrival_time = self.sim_context.rng.expovariate(1/self._avg_interarrival_time)
            self.schedule_message(self._request_gen_msg, delay=interarrival_time)
            return

        if isinstance(message, messages.EntanglementRequestPacket):
            self._handle_entanglement_request(message, port_name)
            return

        if isinstance(message, messages.EntanglementGenPacket):
            self._handle_new_lle(message, port_name)
            return

        else:
            raise ValueError(f"Unknown message received: {message} at node {self.name}")

    def _route_shortest_path(self, destination):
        """
        Get the port to which the message has to be forwarded based on the destination

        Parameters
        ----------
        destination : str
            The destination of the message

        Returns
        -------
        tuple
            The name of the port to which the message has to be forwarded and the next hop name
        """
        # check the routing table
        ret = None
        for routing_dict in self.routing_table:
            if ret is None and routing_dict["dest"] == "default":
                ret = "q" + str(routing_dict["port"])
            elif destination in routing_dict["dest"]:
                ret = "q" + str(routing_dict["port"])

        # now find the next hop in the distance vector
        next_hop = None
        for distance_dict in self.distance_vector:
            if "port" in distance_dict and distance_dict["port"] == ret:
                next_hop = distance_dict["node"]

        if ret is None or next_hop is None:
            raise ValueError(f"No valid route for destination {destination}")

        return ret, next_hop

    def _get_neighbor(self, port_name):
        """
        Get the name of the neighbor connected to the given port

        Parameters
        ----------
        port_name : str
            The name of the port

        Returns
        -------
        str
            The name of the neighbor connected to the given port
        """
        for distance_dict in self.distance_vector:
            if "port" in distance_dict and distance_dict["port"] == port_name:
                return distance_dict["node"]

    def _handle_entanglement_request(self, message, port_name):
        """
        This method is called when an EntanglementRequestPacket is received
        """

        # first thing: check whether the request's LLE is still available, it might have been dropped due to storage
        # qubit shortage
        lle, lle_time = self.lle_manager.peek_from_req(request=message, raise_error=False)
        if lle is None:
            # the lle has been dropped because of storage qubit shortage. We have to drop the request
            return

        if self.name == message.final_destination:
            # we are the destination, we just emit the metric and delete the request
            fidelity = message.meta["qstate"].a
            sim_log.info(f"Request {message.req_id} reached the destination {self.name} with fidelity {fidelity}",
                            time=self.sim_context.time())
            return

        next_port, next_hop = self.route_request(request=message)

        # pop the youngest suitable lle
        other_lle, other_lle_time = self.lle_manager.pop_lle(port_name=next_port,
                                                             policy=LLEManager.YOUNGEST)
        # if no lle is available, we have to append the request to the queue
        if other_lle is None:
            # just append the request to the corresponding queue
            self.req_queue.add_request(request=message, next_hop=next_hop, time=self.sim_context.time())
            return

        # update request
        wait_time = self.sim_context.time() - other_lle_time
        message.update_request(lle_id=other_lle.lle_id, wait_time=wait_time,
                               next_hop=next_hop)

        # decohere the quantum state described within the request
        self._decohere_state(message, wait_time)

        # send the message
        self.send(message, port_name=next_port)


    def _decohere_state(self, message, wait_time):
        # decohere the quantum state described within the request
        wait_time_seconds = wait_time / self.sim_context.time_unit_factor
        rate = message.meta["src_decoherence_rate"] + self.decoherence_rate
        new_state = depolarize_rate(message.meta["qstate"], rate, wait_time_seconds)
        other_pair = get_werner_state(fidelity=1.)
        new_state = swap(new_state, other_pair, eta=1., p_2=1.)
        message.meta["qstate"] = new_state


    def _generate_new_request(self):

        # initialize the epr pair state that will be tracked and updated after every swap
        epr_pair_initial = get_werner_state(fidelity=1.)

        final_destination = "qn5"

        message = messages.EntanglementRequestPacket(req_id=self._next_request_id,
                                                     final_destination=final_destination,
                                                     next_hop=None,
                                                     lle_id=None,
                                                     gen_time=self.sim_context.time()
                                                     )

        message.meta["qstate"] = epr_pair_initial
        message.meta["src_decoherence_rate"] = self.decoherence_rate

        # we are the source, we have to check whether we have a lle to associate with the request
        # if so, we associate the lle and send the request to the next node
        next_port, next_hop = self.route_request(request=message)

        message.update_request(next_hop=next_hop)

        message.meta["is_new_request"] = True

        """
        sim_log.debug(f"Request generated for flow {flow_id}. Here is node {self.name} with a queue empty? {self.req_queue.is_empty()}",
                      time=self.sim_context.time())
        """
        if self.lle_manager.is_empty(port_name=next_port):
            # just append the request to the corresponding queue

            self.req_queue.add_request(request=message, next_hop=next_hop, time=self.sim_context.time())
            return

        # there is at least an lle that can be assigned to the request
        # pop the lle
        lle, lle_time = self.lle_manager.pop_lle(port_name=next_port,
                                                 policy=LLEManager.YOUNGEST)

        assert lle is not None, "No LLE available for popping"

        # update request
        message.update_request(lle_id=lle.lle_id)

        # send the message
        self.send(message, port_name=next_port)


    def _handle_new_lle(self, message, port_name):
        """
        This method is called when an EntanglementGenPacket is received
        """
        # we have to check whether there is a request to be swapped with this lle
        # if so, we swap, update the message information and forward the request to the next node
        neighbor = self._get_neighbor(port_name)
        if self.req_queue.is_empty(next_hop=neighbor):  # no requests for this port :(
            # append
            self.add_lle(message, port_name)
            return

        # there is at least a request for this flow
        # now we are sure that the new lle is in the flow direction we were waiting for and there is a request for it

        # pop the request from the queue
        request, request_time = self.req_queue.pop_request(next_hop=neighbor, policy=RequestQueue.OLDEST)

        # Now we have to check whether we are the source of the flow
        if "is_new_request" in request.meta and request.meta["is_new_request"]:
            # in this case we just have to associate the new lle to the request and send it to the next node
            del request.meta["is_new_request"]
            request.update_request(lle_id=message.lle_id)

            self.send(request, port_name=port_name)
            return

        # we are not the source, we have to pop the lle associated with the request
        # pop lle associated to the popped request
        other_lle, other_lle_time = self.lle_manager.pop_from_req(request=request, raise_error=True)

        # swap the lles
        # update the request message by adding the swapped lle wait time
        wait_time = self.sim_context.time() - other_lle_time

        # update the request message
        request.update_request(lle_id=message.lle_id, wait_time=wait_time,
                               next_hop=neighbor)

        # decohere the quantum state described within the request
        self._decohere_state(request, wait_time)

        sim_log.info(f"Request {request.req_id} swapped at node {self.name} with fidelity {request.meta['qstate'].a}",
                     time=self.sim_context.time())

        # send the message
        self.send(request, port_name=port_name)

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

        if self.storage_qbits is not None:
            if self.lle_manager.length(port_name) >= self.storage_qbits:
                # we have to pop the oldest lle for the same flow
                # if there are no lles for the same flow, we pop the oldest lle for that port
                # if there are no lles for that port, we raise an error
                lle_to_pop, _ = self.lle_manager.pop_lle(port_name=port_name,
                                                        policy=LLEManager.OLDEST)

                if lle_to_pop is None:
                    raise ValueError("No LLEs available for popping")

                # now we have to check whether the popped lle is associated with a request
                # if so, we have to drop the request
                request, _ = self.req_queue.pop_from_lle(lle_to_pop, raise_error=False)
                if request is not None:
                    # the request has been dropped
                    sim_log.warning(f"Request {request.req_id} dropped at node {self.name} due to storage qubit shortage",
                                    time=self.sim_context.time())
                self.lle_manager.add_lle(lle, port_name, self.sim_context.time())
                return

        self.lle_manager.add_lle(lle, port_name, self.sim_context.time())

    def peek_neighbor_queue(self, port_name):
        """
        Peek the request queue of the neighbor connected to the given port

        Parameters
        ----------
        port_name : str
            The name of the port

        Returns
        -------
        RequestQueue
            The request queue of the neighbor connected to the given port
        """
        neighbor = self._get_neighbor(port_name)
        # Here we do a trick and we access the neighbor from the simualtion context
        return self.sim_context.network.get_sub_entity(neighbor).req_queue

    def peek_neighbor_distance(self, port_name, destination):
        """
        Peek the distance from a neighbor connected to the given port and the given destination

        Parameters
        ----------
        port_name : str
            The name of the port
        destination : str
            The destination

        Returns
        -------
        int
            The distance to the neighbor connected to the given port
        """
        neighbor = self._get_neighbor(port_name)
        neighbor_entity = self.sim_context.network.get_sub_entity(neighbor)
        return neighbor_entity.distance_to_destination(destination)

    def distance_to_destination(self, destination):
        """
        Get the distance to the given destination

        Parameters
        ----------
        destination : str
            The destination

        Returns
        -------
        int
            The distance to the destination
        """
        if destination is None:
            raise ValueError("Destination cannot be None")
        elif destination == self.name:
            return 0
        for distance_dict in self.distance_vector:
            if distance_dict["node"] == destination:
                return distance_dict["distance"]
        raise ValueError(f"Destination {destination} not found in the distance vector")


    def _build_input_features(self, request):
        """
        Build the input features for the Q-routing algorithm

        Parameters
        ----------
        request : EntanglementRequestPacket
            The request for which the features have to be built

        Returns
        -------
        dict
            The input features for the Q-routing algorithm
        """
        # get the queue length
        q_length = self.req_queue.length()

        # get the distance to the destination
        destination = request.final_destination
        distance = self.distance_to_destination(destination)

        # check if the final destination is reachable through the neighbors
        candidate_neighbors = []
        candidate_ports = []
        for port_name in self.ports:
            port_idx = int(port_name[1:])
            for rout_dict in self.routing_table:
                if rout_dict["port"] == port_idx and (rout_dict["dest"] == "default" or destination in rout_dict["dest"]):
                    candidate_neighbors.append(self._get_neighbor(port_name))
                    candidate_ports.append(port_name)
                    break

        # get the neighbor queue info
        neighbor_queues = [self.peek_neighbor_queue(port_name) for port_name in candidate_ports]
        neighbor_min_q_length = min([q.length() for q in neighbor_queues])
        neighbor_max_q_length = max([q.length() for q in neighbor_queues])
        neighbor_mean_q_length = sum([q.length() for q in neighbor_queues]) / len(neighbor_queues)

        # get the neighbor distance info
        neighbor_distances = [self.peek_neighbor_distance(port_name, destination) for port_name in candidate_ports]
        neighbor_min_distance = min(neighbor_distances)
        neighbor_max_distance = max(neighbor_distances)
        neighbor_mean_distance = sum(neighbor_distances) / len(neighbor_distances)

        timestep = int(self.sim_context.time() / 100)

        fidelity = request.meta["qstate"].a

        return {
            "TIMESTEP": timestep,
            "EPR_ID": request.req_id,
            "PREV_TIMESTEP": timestep - 1,
            "FIDELITY": fidelity,
            "Q_LENGTH": q_length,
            "DISTANCE": distance,
            "NEIGHBOR_MIN_Q_LENGTH": neighbor_min_q_length,
            "NEIGHBOR_MAX_Q_LENGTH": neighbor_max_q_length,
            "NEIGHBOR_MEAN_Q_LENGTH": neighbor_mean_q_length,
            "NEIGHBOR_MIN_DISTANCE": neighbor_min_distance,
            "NEIGHBOR_MAX_DISTANCE": neighbor_max_distance,
            "NEIGHBOR_MEAN_DISTANCE": neighbor_mean_distance
        }

    def _route_request_with_agent(self, request):

        # build the input features
        features = self._build_input_features(request)

        # import routing function from routing_agent
        from projects.Qrouting.routing_agent import route

        # get the action (next hop)
        action = route(features, self.name)

        # emit features
        self.emit_metric("features", features)

        # get the out port
        out_port, next_hop = self._route_shortest_path(action)

        return out_port, next_hop

    def route_request(self, request):
        if self.should_use_agent:
            return self._route_request_with_agent(request=request)
        else:
            # build the input features
            features = self._build_input_features(request)
            # emit features
            self.emit_metric("features", features)
            return self._route_shortest_path(request.final_destination)





