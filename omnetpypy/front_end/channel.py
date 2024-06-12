"""
This module implements the Channel class, which implements advanced connectivity between modules in the simulation.
"""
from omnetpypy.front_end import Message
from omnetpypy.front_end.sim_entity import SimulatedEntity


class Channel(SimulatedEntity):

    def __init__(self, name, identifier=None, delay=None, loss_prob=None):
        super().__init__(name, identifier, port_names=["A", "B"])
        self.is_listening = True
        self.delay = delay
        self.loss_prob = loss_prob

    def handle_message(self, message, port_name):
        """
        Process a message received from a port. First, it processes the message, then it applies
        optional delay, and finally it sends the message out of the other port.

        Parameters
        ----------
        message : Message
            The message to be handled.
        port_name : str
            The port from which the message was received.
        """

        if port_name is None:  # this is a self message, should be immediately sent to the other port
            port = message.meta["port_noneshouldusethiskey"]
            del message.meta["port_noneshouldusethiskey"]
            self.send(message, port)
            return

        post_processed_message = self.process_message(message, port_name)

        should_drop = self.apply_loss(message, port_name) or post_processed_message is None
        out_port = "B" if port_name == "A" else "A"
        if not should_drop and (self.delay is None or self.delay <= 0):
            self.send(post_processed_message, out_port)
        elif not should_drop:
            post_processed_message.meta["port_noneshouldusethiskey"] = out_port
            self.schedule_message(post_processed_message, delay=self.generate_delay(message, port_name))

    def process_message(self, message, port_name):
        """
        Process a message received from a port.

        Parameters
        ----------
        message : Message
            The message to be processed.
        port_name : str
            The port from which the message was received.

        Returns
        -------
        Message or None
            The message to be sent to the connected port, or None if the message should be dropped for any reason.
        """

        # default behavior
        return message

    def generate_delay(self, message, port_name):
        """
        Generate a delay for the message, based on an arbitrary delay distribution.

        Parameters
        ----------
        message : Message
            The message to be delayed.
        port_name : str
            The port from which the message was received.

        Returns
        -------
        float or None
            The delay to be applied to the message. If None or zero, the message will be sent immediately.
        """

        # default behavior
        return self.delay

    def apply_loss(self, message, port_name):
        """
        Apply loss to the message, based on an arbitrary loss probability distribution.

        Parameters
        ----------
        message : Message
            The message to be delayed.
        port_name : str
            The port from which the message was received.

        Returns
        -------
        bool
            True if the message should be lost, False otherwise.
        """

        # default behavior
        if self.loss_prob is not None:

            # we use the default rng in the sim_context
            return self.sim_context.rng.random() < self.loss_prob

        return False

