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

    def pop_request(self, flow_id, policy=OLDEST):
        """
        Remove and return the first request in the queue

        Parameters
        ----------
        flow_id : int
            The flow id of the request to pop
        policy : int
            The policy to use when popping the request. It can be either OLDEST (0) or YOUNGEST (1)

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
                if req.flow_id == flow_id:
                    return queue.pop(i)
        else:
            # pop the youngest request
            for i, (req, time) in enumerate(queue[::-1]):
                if req.flow_id == flow_id:
                    return queue.pop(-i - 1)
        return None, None

    def peek_request(self, flow_id, policy=OLDEST):
        """
        Return the first request in the queue without removing it

        Parameters
        ----------
        flow_id : int
            The flow id of the request to peek
        policy : int
            The policy to use when peeking the request. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request for that flow
            id was found
        """
        queue = self._requests[flow_id]
        if policy == self.OLDEST:
            # peek the oldest request
            for req, time in queue:
                if req.flow_id == flow_id:
                    return req, time
        elif policy == self.YOUNGEST:
            # peek the youngest request
            for req, time in queue[::-1]:
                if req.flow_id == flow_id:
                    return req, time
        else:
            raise ValueError("Invalid policy")
        return None, None

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
