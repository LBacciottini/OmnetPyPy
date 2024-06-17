"""
This toy simulation module implements a simple ping-pong protocol.
The simulation consists of two modules, a `PingModule` and a `PongModule`,
which send messages to each other in a ping-pong fashion. The `PingModule` sends a message to the `PongModule`,
which then sends a message back to the `PingModule`. This process is repeated for a specified number of times.
"""

from omnetpypy.examples.ping_pong.ping_pong_simple import PingPongModule

__all__ = ["PingPongModule"]
