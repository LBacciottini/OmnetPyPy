"""
This module implements the :class:`~omnetpypy.front_end.message.Message` class,
representing a message in the simulation.
"""

__all__ = ['Message']


class Message:
    r"""
    This class is a wrapper for messages exchanged between entities in a simulation.

    Parameters
    ----------
    fields : list
        The fields of the message.
    meta : dict, optional
        Additional metadata to be stored with the message. A typical use case is to store a "header".

    Attributes
    ----------
    fields : list
        The fields of the message.
    meta : dict
        Additional, editable metadata stored with the message.
    """

    def __init__(self, fields, **meta):
        self.fields = fields
        self.meta = meta
        if meta is None:
            self.meta = {}

    def __str__(self):
        return f"Message(fields={self.fields}, meta={self.meta})"

    def __copy__(self):
        """
        Return a shallow copy of the message.
        """
        new_meta = self.meta.copy()
        return Message(fields=self.fields[:], **new_meta)
