from omnetpypy import SimpleModule, Message
from omnetpypy import sim_log

__all__ = ["PingPongModule"]

class PingPongModule(SimpleModule):
    """
    The Ping Pong Module. The behavior between the Ping and Pong modules is the same except for
    who sends the first message (Ping). This differentiation is handled in the initialize method through the name.

    Parameters
    ----------
    name : str
        The name of the module. Either "ping" or "pong".
    identifier : int
        The identifier of the module. This identifier should be unique within the simulation.
    delay : int, optional
        The delay in seconds between receiving and sending a message. The default is 5s.
    """

    def __init__(self, name, identifier, delay=5):
        port_names = ["in_out"]
        self.delay = delay
        super().__init__(name, identifier, port_names)

    def initialize(self, step=0):
        if step == 0:
            if self.name == "ping":
                sim_log.info(message="I am the Pinger, generating the first message!", time=self.sim_context.time())

                message = Message(fields=["PING PONG"], header="PING PONG MSG")

                self.schedule_message(message, delay=self.delay)

    def handle_message(self, message, port_name):

        if port_name is None: # self message
            sim_log.info(message=f"{self.name}: Sending the first Message!", time=self.sim_context.time())
            self.send(message, port_name="in_out")
        else:
            sim_log.info(message=f"{self.name}: Received the Message: {message.fields[0]}", time=self.sim_context.time())
            self.send(message, port_name="in_out")
            self.emit_metric("Throughput", 1)
