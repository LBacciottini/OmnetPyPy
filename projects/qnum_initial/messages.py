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
