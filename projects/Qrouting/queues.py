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
        self._requests = []

    def add_request(self, request, next_hop, time):
        """
        Add a request to the queue

        Parameters
        ----------
        request : EntanglementRequestPacket
            The request to add
        next_hop : str
            The name of the next hop for the request
        time : float
            The simulation time the request was added to the queue
        """
        self._requests.append((request, next_hop, time))

    def pop_request(self, next_hop, policy=OLDEST):
        """
        Remove and return the first request in the queue

        Parameters
        ----------
        next_hop : str
            The name of the next hop for the request
        policy : int
            The policy to use when popping the request. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request for that flow
            id was found
        """
        queue = self._requests
        if policy == self.OLDEST:
            # pop the oldest request
            for i, (req, nxt_hp, time) in enumerate(queue):
                if nxt_hp == next_hop:
                    queue.pop(i)
                    return req, time
        else:
            # pop the youngest request
            for i, (req, nxt_hp, time) in enumerate(queue[::-1]):
                if nxt_hp == next_hop:
                    queue.pop(-i - 1)
                    return req, time
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

        queue = self._requests
        for i, (req, nxt_hp, time) in enumerate(queue):
            if req.lle_id == lle.lle_id:
                queue.pop(i)
                return req, time

        if raise_error:
            raise ValueError("No request found for the given LLE")
        return None, None

    def peek_request(self, next_hop=None, policy=OLDEST):
        """
        Return the first request in the queue without removing it

        Parameters
        ----------
        next_hop : str or None, optional
            The name of the next hop for the request. If None, the method will return the first request in the queue.
        policy : int
            The policy to use when peeking the request. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the request and the time it was added to the queue, or (None, None) if no request for that flow
            id was found
        """
        queue = self._requests
        if policy == self.OLDEST:
            # pop the oldest request
            for i, (req, nxt_hp, time) in enumerate(queue):
                if nxt_hp == next_hop:
                    return req, time
        else:
            # pop the youngest request
            for i, (req, nxt_hp, time) in enumerate(queue[::-1]):
                if nxt_hp == next_hop:
                    return req, time
        return None, None

    def is_empty(self, next_hop=None):
        """
        Check whether the queue is empty for a given (optional) next_hop

        Parameters
        ----------
        next_hop : str or None, optional
            The next hop to check for requests. If None, the method will check if the queue is empty. Default is None.

        Returns
        -------
        bool
            True if there are no requests for the given next_hop, False otherwise. If no next hop is given, return True if
            there are no requests in the queue, False otherwise.
        """
        if next_hop is not None:
            return len([req for req, nxt_hp, time in self._requests if nxt_hp == next_hop]) == 0
        else:
            return len(self) == 0

    def __len__(self):
        return len(self._requests)

    def length(self, next_hop=None):
        """
        Return the total number of requests in the queue for a given flow id and/or port name

        Parameters
        ----------
        next_hop : str or None, optional
            The name of the next hop to check for requests. If None, the method will return the total number of requests

        Returns
        -------
        int
            The total number of requests in the queue for the given flow id
        """
        if next_hop is not None:
            return len([req for req, nxt_hp, time in self._requests if nxt_hp == next_hop])
        else:
            return len(self)

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
                if lle.lle_id == request.lle_id:
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
                if lle.lle_id == request.lle_id:
                    return lle, time
        if raise_error:
            raise ValueError("No LLE found for the given request")
        return None, None

    def pop_lle(self, port_name, policy=OLDEST):
        r"""
        Pop an LLE from the manager available on the given port, according to the given policy

        Parameters
        ----------
        port_name : str
            The name of the port where the LLE is available
        policy : int
            The policy to use when popping the LLE. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found

        """

        if policy == self.OLDEST:
            for i, (lle, time) in enumerate(self._lles[port_name]):
                return self._lles[port_name].pop(i)
        elif policy == self.YOUNGEST:
            for i, (lle, time) in enumerate(self._lles[port_name][::-1]):
                return self._lles[port_name].pop(-i - 1)
        else:
            raise ValueError("Invalid policy")

        return None, None

    def peek_lle(self, port_name, policy=OLDEST):
        """
        Peek at an LLE from the manager available on the given port, according to the given policy

        Parameters
        ----------
        port_name : str
            The name of the port where the LLE is available
        policy : int
            The policy to use when popping the LLE. It can be either OLDEST (0) or YOUNGEST (1)

        Returns
        -------
        tuple
            A tuple with the LLE and the time it was added to the manager, or (None, None) if no LLE was found

        """

        if policy == self.OLDEST:
            for lle, time in self._lles[port_name]:
                return lle, time
        elif policy == self.YOUNGEST:
            for lle, time in self._lles[port_name][::-1]:
                return lle, time
        else:
            raise ValueError("Invalid policy")

        return None, None

    def is_empty(self, port_name):
        """
        Check whether the manager is empty for a given (optional) flow identifier

        Parameters
        ----------
        port_name : str
            The name of the port to check for LLEs

        Returns
        -------
        bool
            True if there are no LLEs for a given flow, False otherwise. If no flow id is given, return True if
            there are no LLEs in the manager, False otherwise.
        """

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
