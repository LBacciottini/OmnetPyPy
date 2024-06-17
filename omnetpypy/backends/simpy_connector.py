"""This module implements the connector to the SimPy simulation engine."""
from omnetpypy.backends.connector import Connector
import simpy

__all__ = ["SimPyConnector"]


class SimPyConnector(Connector):
    r"""
    This class is a connector to the SimPy simulation engine.

    See Also
    --------
    :class:`~omnetpypy.backends.connector.Connector`
    """

    def __init__(self, simulation, metrics=None, output_dir=None, repetition=0):
        super().__init__(simulation, metrics, output_dir, repetition)
        self.env = simpy.Environment()
        self.entities = {}
        self._wrappers = {}

    def start_simulation(self, until=None):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.start_simulation`
        """
        # we load a process that calls initialize for each entity
        self.env.process(initialize_entity(self.simulation.network))
        if until is not None:
            self.env.run(until=until)
        else:
            self.env.run()

    def add_entity(self, entity):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.add_entity`
        """
        # entity is a simple module
        # we need to implement the module as a process
        # and add it to the environment
        super().add_entity(entity)

        self.entities[entity.name] = entity

        if entity.is_listening:
            self._wrappers[entity.identifier] = ModuleProcessWrapper(entity, self.env)

    def get_time(self):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.get_time`
        """
        return self.env.now

    def schedule_port_input(self, port, message):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.schedule_port_input`
        """
        # put the message in the store of the module wrapper
        self._wrappers[port.parent.identifier].put(message, port.name)

    def schedule_self_message(self, message, entity, at=None, delay=None):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.schedule_self_message`
        """
        if not entity.is_listening:
            raise Exception(f"Entity {entity} is not listening. Cannot schedule a self message.")
        # create a process using the schedule_message function
        process = self.env.process(schedule_message(message, self._wrappers[entity.identifier], at, delay))
        # put the message and the process in the scheduled messages list
        self._wrappers[entity.identifier].scheduled_messages.append((message, process))

    def is_scheduled(self, message, entity):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.is_scheduled`
        """
        # check if the message is in the scheduled messages list
        for m, p in self._wrappers[entity.identifier].scheduled_messages:
            if m == message:
                return True
        return False

    def cancel_scheduled(self, message, entity):
        r"""
        See Also
        --------
        :meth:`~omnetpypy.backends.connector.Connector.cancel_scheduled`
        """
        # cancel the scheduled message
        for m, p in self._wrappers[entity.identifier].scheduled_messages:
            if m == message:
                p.interrupt()
                self._wrappers[entity.identifier].scheduled_messages.remove((m, p))


class ModuleProcessWrapper:

    def __init__(self, module, env):
        self.module = module
        # define a store for the messages
        self.store = simpy.Store(env)
        # define a process for the module
        self.process = env.process(self.run())

        self.env = env

        self.scheduled_messages = []

    def run(self):
        while True:
            try:
                message, port_name = yield self.store.get()
                self.module.handle_message(message, port_name)
            except simpy.Interrupt:
                break

    def put(self, message, port_name):
        self.store.put((message, port_name))


def schedule_message(message, wrapper, at=None, delay=None):
    # wait for a given time (either at or delay) and then put a message in the store
    try:
        if at:
            yield wrapper.env.timeout(at - wrapper.env.now)
        elif delay:
            yield wrapper.env.timeout(delay)
        wrapper.put(message=message, port_name=None)
        # remove the message from the scheduled messages list
        for m, p in wrapper.scheduled_messages:
            if m == message:
                wrapper.scheduled_messages.remove((m, p))
    except simpy.Interrupt:
        pass


def initialize_entity(entity):
    for step in range(0, 6):
        yield entity.sim_context.connector.env.timeout(0)
        initialize_entity_with_step(entity, step)


def initialize_entity_with_step(entity, step):
    if hasattr(entity, "sub_modules"):
        for sub_entity in entity.sub_modules.values():
            initialize_entity_with_step(sub_entity, step)
    entity.initialize(step)
