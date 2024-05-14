"""
In this module we implement the RequestQueue class, which is a simple wrapper around a list of requests. It is used to
store the requests that are waiting to be processed by QuantumNodes.
"""


class RequestQueue:
    """
    This class is a simple wrapper around a list of requests. It is used to store the requests that are waiting to be
    processed by QuantumNodes.
    """

    # create an enumerator for the popping policy (oldest or youngest)
    OLDEST = 0
    YOUNGEST = 1

    def __init__(self):
        self._requests = {}

    def add_request(self, request, time):
        """
        Add a request to the queue

        Parameters
        ----------
        request : EntanglementRequestPacket
            The request to add
        time : float
            The simulation time the request was added to the queue
        """
        if request.flow_id not in self._requests:
            self._requests[request.flow_id] = []

        self._requests[request.flow_id].append((request, time))

    def pop_request(self, flow_id, policy=OLDEST, direction="any"):
        """
        Remove and return the first request in the queue

        Parameters
        ----------
        flow_id : int
            The flow id of the request to pop
        policy : int
            The policy to use when popping the request. It can be either OLDEST (0) or YOUNGEST (1)
        direction : str
            The direction of the request to pop. It can be either "upstream", "downstream" or "any"

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request for that flow
            id was found
        """
        queue = self._requests[flow_id]
        if policy == self.OLDEST:
            # pop the oldest request
            for i, (req, time) in enumerate(queue):
                if req.flow_id == flow_id and (direction == "any" or req.direction == direction):
                    return queue.pop(i)
        else:
            # pop the youngest request
            for i, (req, time) in enumerate(queue[::-1]):
                if req.flow_id == flow_id and (direction == "any" or req.direction == direction):
                    return queue.pop(-i - 1)
        return None, None

    def pop_from_lle(self, lle, raise_error=False):
        """
        Remove and return the request in the queue associated with the LLE

        Parameters
        ----------
        lle : EntanglementGenPacket
            The LLE to satisfy
        raise_error : bool, optional
            Whether to raise an error if no request is found. Default is False.

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request was found
            and raise_error is False
        """
        flow_id = lle.flow_id
        if flow_id not in self._requests:
            if raise_error:
                raise ValueError("No request found for the given LLE")
            return None, None

        queue = self._requests[flow_id]
        for i, (req, time) in enumerate(queue):
            if req.lle_id == lle.lle_id:
                return queue.pop(i)

        if raise_error:
            raise ValueError("No request found for the given LLE")
        return None, None

    def peek_request(self, flow_id=None, port_name=None, policy=OLDEST):
        """
        Return the first request in the queue without removing it

        Parameters
        ----------
        flow_id : int
            The flow id of the request to peek. If None, any flow id will be considered. Default is None.
        port_name : str
            The name of the port to peek the request from. If None, any port will be considered. Default is None.
        policy : int
            The policy to use when peeking the request. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request for that flow
            id was found
        """
        if flow_id is not None:
            queue = self._requests[flow_id]
        else:
            queue = []
            for q in self._requests.values():
                queue.extend(q)
        if policy == self.OLDEST or policy == "OLDEST":
            # peek the oldest request
            oldest = float("inf")
            oldest_req = None
            for req, time in queue:
                if port_name is not None and ((req.direction == "upstream" and port_name == "q1") or
                                              (req.direction == "downstream" and port_name == "q0")):
                    if time < oldest:
                        oldest = time
                        oldest_req = req
                elif port_name is None:
                    if time < oldest:
                        oldest = time
                        oldest_req = req
            if oldest_req is not None:

                return oldest_req, oldest
        elif policy == self.YOUNGEST or policy == "YOUNGEST":
            # peek the youngest request
            youngest = 0
            youngest_req = None
            for req, time in queue[::-1]:
                if port_name is not None and ((req.direction == "upstream" and port_name == "q1") or
                                              (req.direction == "downstream" and port_name == "q0")):
                    if time > youngest:
                        youngest = time
                        youngest_req = req
                elif port_name is None:
                    if time > youngest:
                        youngest = time
                        youngest_req = req
            if youngest_req is not None:
                return youngest_req, youngest
        else:
            raise ValueError("Invalid policy")
        return None, None

    def delete_requests(self, flow_id):
        """
        Delete all requests for a given flow id

        Parameters
        ----------
        flow_id : int
            The flow id of the requests to delete
        """

        if flow_id in self._requests:
            del self._requests[flow_id]

    def is_empty(self, flow_id=None):
        """
        Check whether the queue is empty for a given (optional) flow identifier

        Parameters
        ----------
        flow_id : int or None, optional
            The flow id to check for requests. If None, the method will check if the queue is empty. Default is None.

        Returns
        -------
        bool
            True if there are no requests for a given flow, False otherwise. If no flow id is given, return True if
            there are no requests in the queue, False otherwise.
        """
        if flow_id is not None:
            if flow_id not in self._requests:
                return True
            return len(self._requests[flow_id]) == 0
        else:
            for queue in self._requests.values():
                if len(queue) > 0:
                    return False
            return True

    def __len__(self):
        tot_len = 0
        for queue in self._requests.values():
            tot_len += len(queue)
        return tot_len

    def length(self, flow_id=None, port_name=None):
        """
        Return the total number of requests in the queue for a given flow id and/or port name

        Parameters
        ----------
        flow_id : int or None, optional
            The flow id of the requests to count. If None, all requests will be counted. Default is None.
        port_name : str or None, optional
            The name of the port to count the requests from. If None, all ports will be considered. Default is None.

        Returns
        -------
        int
            The total number of requests in the queue for the given flow id
        """

        if flow_id is not None:
            if flow_id not in self._requests:
                return 0
            return len(self._requests[flow_id])
        elif port_name is not None:
            tot_len = 0
            for queue in self._requests.values():
                for req, time in queue:
                    if (req.direction == "upstream" and port_name == "q1" or
                            req.direction == "downstream" and port_name == "q0"):
                        tot_len += 1
            return tot_len
        else:
            return len(self)

    def weighted_length(self, direction):
        """
        Get the total number of requests belonging to any flow with the specified direction.
        The weight of each request is 1/success_prob.

        Parameters
        ----------
        direction : string
            The direction of the flow. Either "upstream" or "downstream".

        Returns
        -------
        float
            The weighted queue length for the given direction
        """
        tot_len = 0.
        tot_len_unweighted = 0
        for flow_id, queue in self._requests.items():
            for req, time in queue:
                if req.meta["direction"] == direction:
                    tot_len += 1/req.meta["success_probs"][0]
                    tot_len_unweighted += 1
                else:  # all requests for the flow will have the same direction
                    break
        return tot_len

class LLEManager:
    """
    This class is a wrapper around a list of LLEs. It is used to store the LLEs that are available to be used by
    QuantumNodes.
    """

    # create an enumerator for the popping policy (oldest or youngest)
    OLDEST = 0
    YOUNGEST = 1

    def __init__(self, port_names):
        self._lles = {port_name: [] for port_name in port_names}

    def add_lle(self, lle, port_name, time):
        """
        Add an LLE to the manager

        Parameters
        ----------
        lle : EntanglementGenPacket
            The LLE to add
        port_name : str
            The name of the port on which the LLE is available
        time : float
            The simulation time the LLE was added to the manager
        """
        self._lles[port_name].append((lle, time))

    def pop_from_req(self, request, raise_error=True):
        """
        Remove and return the LLE in the manager associated with the request

        Parameters
        ----------
        request : EntanglementRequestPacket
            The request to satisfy
        raise_error : bool, optional
            Whether to raise an error if no LLE is found. Default is True.

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found
        """
        for port_name, lles in self._lles.items():
            for i, (lle, time) in enumerate(lles):
                if lle.flow_id == request.flow_id and lle.lle_id == request.lle_id:
                    return self._lles[port_name].pop(i)
        if raise_error:
            raise ValueError("No LLE found for the given request")
        return None, None

    def peek_from_req(self, request, raise_error=True):
        """
        Return the LLE in the manager associated with the request

        Parameters
        ----------
        request : EntanglementRequestPacket
            The request to satisfy
        raise_error : bool, optional
            Whether to raise an error if no LLE is found. Default is True.

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found
        """
        for port_name, lles in self._lles.items():
            for lle, time in lles:
                if lle.flow_id == request.flow_id and lle.lle_id == request.lle_id:
                    return lle, time
        if raise_error:
            raise ValueError("No LLE found for the given request")
        return None, None

    def pop_lle(self, port_name, flow_id=None, policy=OLDEST):
        r"""
        Pop an LLE from the manager available on the given port, according to the given policy

        Parameters
        ----------
        port_name : str
            The name of the port where the LLE is available
        flow_id : int or None, optional
            The flow id of the LLE to pop. If None, the method will pop the first LLE available on the port. Default is
            None.
        policy : int
            The policy to use when popping the LLE. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found

        """

        if policy == self.OLDEST:
            for i, (lle, time) in enumerate(self._lles[port_name]):
                if flow_id is None or lle.flow_id == flow_id:
                    return self._lles[port_name].pop(i)
        elif policy == self.YOUNGEST:
            for i, (lle, time) in enumerate(self._lles[port_name][::-1]):
                if flow_id is None or lle.flow_id == flow_id:
                    return self._lles[port_name].pop(-i - 1)
        else:
            raise ValueError("Invalid policy")

        return None, None

    def peek_lle(self, port_name, flow_id=None, policy=OLDEST):
        """
        Peek at an LLE from the manager available on the given port, according to the given policy

        Parameters
        ----------
        port_name : str
            The name of the port where the LLE is available
        flow_id : int or None, optional
            The flow id of the LLE to pop. If None, the method will pop the first LLE available on the port. Default is
            None.
        policy : int
            The policy to use when popping the LLE. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found

        """

        if policy == self.OLDEST:
            for lle, time in self._lles[port_name]:
                if flow_id is None or lle.flow_id == flow_id:
                    return lle, time
        elif policy == self.YOUNGEST:
            for lle, time in self._lles[port_name][::-1]:
                if flow_id is None or lle.flow_id == flow_id:
                    return lle, time
        else:
            raise ValueError("Invalid policy")

        return None, None

    def delete_lles(self, flow_id):
        """
        Delete all LLEs for a given flow id

        Parameters
        ----------
        flow_id : int
            The flow id of the LLEs to delete
        """

        for port_name in self._lles.keys():
            self._lles[port_name] = [lle for lle in self._lles[port_name] if lle[0].flow_id != flow_id]


    def is_empty(self, port_name, flow_id=None):
        """
        Check whether the manager is empty for a given (optional) flow identifier

        Parameters
        ----------
        port_name : str
            The name of the port to check for LLEs
        flow_id : int or None, optional
            The flow id to check for LLEs. If None, the method will check if the manager is empty. Default is None.

        Returns
        -------
        bool
            True if there are no LLEs for a given flow, False otherwise. If no flow id is given, return True if
            there are no LLEs in the manager, False otherwise.
        """
        if flow_id is not None:
            return len([lle for lle in self._lles[port_name] if lle[0].flow_id == flow_id]) == 0
        else:
            return len(self._lles[port_name]) == 0

    def __len__(self):
        """
        Return the total number of LLEs in the manager

        Returns
        -------
        int
            The total number of LLEs in the manager
        """
        tot_len = 0
        for lles in self._lles.values():
            tot_len += len(lles)
        return tot_len

    def length(self, port_name):
        """
        Return the total number of LLEs in the manager for a given port

        Returns
        -------
        int
            The total number of LLEs in the manager for the given port
        """
        return len(self._lles[port_name])