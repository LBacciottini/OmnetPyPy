r"""
The omnetpupy backends sub-package is responsible for the connection between the user API
and discrete event simulation engines.

The user API is defined in the front end sub-package, and is independent of the simulation engine used.
The backends sub-package provides the necessary tools to connect the user API to the simulation engine,
and to run the simulation.
"""

from omnetpypy.backends.connector import Connector

__all__ = ["Connector"]
