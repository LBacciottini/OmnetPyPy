"""
This module implements the Message class, representing a message in the simulation.
"""

__all__ = ['Message']


class Message:
    r"""
    This class represents the messages exchanged between modules in a simulation.
    """

    def __init__(self, fields, **meta):
        self.fields = fields
        self.meta = meta
        if meta is None:
            self.meta = {}

    def __str__(self):
        return f"Message(fields={self.fields}, meta={self.meta})"

    def __copy__(self):
        new_meta = self.meta.copy()
        return Message(fields=self.fields[:], **new_meta)
