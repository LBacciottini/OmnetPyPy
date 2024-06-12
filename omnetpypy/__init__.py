r"""
An omnet++-like, user-friendly simulation package fully implemented on Python,
with the possibility to support different simulation backends such as SimPy or PyDynaa while keeping the same front-end.

The package is designed to be as similar in concept and usage to the omnet++ simulation framework, but with the
advantages of being written in Python, which makes it more flexible and easy to use.
"""

from omnetpypy.front_end import SimpleModule, Message, CompoundModule, Channel
from omnetpypy.simulation import Experiment

__all__ = ["SimpleModule", "Message", "CompoundModule", "Channel", "Experiment"]
