from discrete_sim import Message


class RoutablePacket(Message):
    """
    This class models a classical packet that can be routed through a network.

    The only constraint to the packet is that it must have a specified destination in its meta.
    """

    def __init__(self, destination, fields, **meta):
        meta["destination"] = destination
        super().__init__(fields, **meta)

    @property
    def destination(self):
        return self.meta["destination"]

    @destination.setter
    def destination(self, value):
        self.meta["destination"] = value


class EntanglementRequestPacket(RoutablePacket):

    HEADER = "ENTANGLEMENT REQUEST"

    def __init__(self, req_id, next_hop, final_destination, lle_id, gen_time, wait_times=None, **meta):
        if wait_times is None:
            wait_times = []
        super().__init__(next_hop, fields=[req_id,  lle_id, gen_time, wait_times, final_destination],
                         header=EntanglementRequestPacket.HEADER, **meta)

    @property
    def req_id(self):
        return self.fields[0]

    @property
    def lle_id(self):
        return self.fields[1]

    @lle_id.setter
    def lle_id(self, value):
        self.fields[1] = value

    @property
    def gen_time(self):
        return self.fields[2]

    @property
    def wait_times(self):
        return self.fields[3]

    @property
    def final_destination(self):
        return self.fields[4]

    @property
    def next_hop(self):
        return self.destination

    @next_hop.setter
    def next_hop(self, value):
        self.destination = value

    def append_wait_time(self, wait_time):
        self.wait_times.append(wait_time)

    def __copy__(self):
        new_meta = self.meta.copy()
        del new_meta["destination"]
        del new_meta["header"]
        fields_cpy = self.fields[:]
        ret = EntanglementRequestPacket(req_id=fields_cpy[0], destination=self.destination,
                                         flow_id=fields_cpy[1], lle_id=fields_cpy[2], wait_times=fields_cpy[3][:],
                                         **new_meta)

        return ret

    def update_request(self, lle_id=None, wait_time=None, next_hop=None):
        """
        Update the request with the new lle_id, wait_time and destination. Usually done right before forwarding the
        request to the next node.

        Parameters
        ----------
        lle_id : int or None, optional
            The new lle_id
        wait_time : float or None, optional
            The wait time for the last swapped lle, appended to the wait_times list
        next_hop : str or None, optional
            The new destination for the request (next hop)
        """
        if lle_id is not None:
            self.lle_id = lle_id
        if wait_time is not None:
            self.append_wait_time(wait_time)
        if next_hop is not None:
            self.next_hop = next_hop


class EntanglementGenPacket(Message):
    """
    This class models the message sent by link controllers to nodes, encapsulating the entanglement generation
    for a given flow
    """

    HEADER = "ENTANGLEMENT GENERATION"

    def __init__(self, lle_id, sender_name, **meta):
        meta["header"] = EntanglementGenPacket.HEADER
        fields = [lle_id, sender_name]
        super().__init__(fields, **meta)

    @property
    def lle_id(self):
        return self.fields[0]

    @property
    def sender_name(self):
        return self.fields[1]


