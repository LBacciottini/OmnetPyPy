r"""
This module implements the :meth:`~omnetpypy.front_end.channel.Channel` class,
which implements advanced connectivity between ports in the simulation.
"""
from omnetpypy.front_end import Message
from omnetpypy.front_end.sim_entity import SimulatedEntity


class Channel(SimulatedEntity):
    r"""
    Channels are used to apply operations on messages travelling between connected ports.
    They can apply noise, delays, losses, and other custom operations to the messages.

    Channels always have two ports, named "A" and "B". The channel forwards messages
    from port "A" to port "B", and vice versa, after applying the specified delay and loss probability.

    Subclasses can override the methods :meth:`~omnetpypy.front_end.channel.Channel.process_message` to apply more
    complex and asymmetric operations on the messages passing through the channel.

    Parameters
    ----------
    name : str
        The name of the channel. This name should be unique within the simulation.
    identifier : int or None, optional
        The identifier of the channel. This identifier should be unique within the simulation.
        If ``None``, the identifier will be automatically generated.
    delay : float or None, optional
        The delay to be applied to the messages passing through the channel. If ``None``, no delay is applied.
    loss_prob : float or None, optional
        The probability of loss to be applied to the messages passing through the channel.
        If ``None``, no loss is applied.

    Attributes
    ----------
    delay : float or None
        The delay to be applied to the messages passing through the channel.
        If ``None``, no delay is applied.
    loss_prob : float or None
        The probability of loss to be applied to the messages passing through the channel.
        If ``None``, no loss is applied.
    """

    def __init__(self, name, identifier=None, delay=None, loss_prob=None):
        super().__init__(name, identifier, port_names=["A", "B"])
        self.is_listening = True
        self.delay = delay
        self.loss_prob = loss_prob

    def handle_message(self, message, port_name):
        r"""
        Handle a message received from a port. First, it processes the message  by calling the method
        :meth:`~omnetpypy.front_end.channel.Channel.process_message`, then it applies the
        optional delay and loss probability, and finally it sends the message out of the other port (if not lost).

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
        r"""
        Process a message received from a port. By default, this method does nothing and returns the message as is.
        Subclasses can override this method to apply more complex operations on the messages passing through the
        channel.

        Parameters
        ----------
        message : :meth:`~omnetpypy.front_end.message.Message`
            The message to be processed.
        port_name : str
            The port from which the message was received.

        Returns
        -------
        :meth:`~omnetpypy.front_end.message.Message` or None
            The message to be sent to the connected port, or ``None`` if the message should be dropped.
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

