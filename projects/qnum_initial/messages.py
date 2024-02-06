from discrete_sim import Message


class MyProtocolSpecificPacket(Message):

    HEADER = "MY PROTOCOL SPECIFIC HEADER"

    def __init__(self, mandatory_field_1, mandatory_field_2, optional_field=None, **meta):
        meta["header"] = MyProtocolSpecificPacket.HEADER
        fields = [mandatory_field_1, mandatory_field_2]
        if optional_field is not None:
            fields.append(optional_field)
        super().__init__(fields, **meta)

        # We can define any kind of custom packet types to make code cleaner and more readable


class FlowsInformationPacket(Message):
    r"""
    This class models a message that carries information about the flows in the network.

    Parameters
    ----------

    flows : list
        Flow descriptors, each one containing the following fields:
        <ul>
            <li>flow_id</li>
            <li>source_id</li>
            <li>destination_id</li>
            <li>path (list of node identifiers)</li>
            <li>success_probs (list of success probabilities for each link in the path)</li>
            <li>request_rate (average, Poisson process)</li>
        </ul>
    """

    HEADER = "FLOWS INFORMATION"

    def __init__(self, flows, **meta):
        meta["header"] = FlowsInformationPacket.HEADER
        fields = [flows]
        super().__init__(fields, **meta)

    @property
    def flows(self):
        return self.fields[0]


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


class EntanglementRequestPacket(RoutablePacket):

    HEADER = "ENTANGLEMENT REQUEST"

    def __init__(self, destination, flow_id):
        super().__init__(destination, fields=[flow_id], header=EntanglementRequestPacket.HEADER)

    @property
    def flow_id(self):
        return self.fields[0]


class EntanglementGenPacket(Message):
    """
    This class models the message sent by link controllers to nodes, encapsulating the entanglement generation
    for a given flow
    """

    HEADER = "ENTANGLEMENT GENERATION"

    def __init__(self, flow_id, lle_id, **meta):
        meta["header"] = EntanglementGenPacket.HEADER
        fields = [flow_id, lle_id]
        super().__init__(fields, **meta)

    @property
    def flow_id(self):
        return self.fields[0]

    @property
    def lle_id(self):
        return self.fields[1]


