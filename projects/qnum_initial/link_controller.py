from discrete_sim import SimpleModule


class LinkController(SimpleModule):
    """
    This class models a Link Controller, placed in the middle of a link.
    """

    def __init__(self, name, identifier):
        port_names = ["lc0", "lc1"]

        super().__init__(name, identifier, port_names)
        self.qubit = None

    def initialize(self, step=0):
        if step == 0:
            # TODO: Write here things to be initialized at the beginning of the simulation
            # usually you can retrieve parameters by looking at self.parent attributes (parent is the compound module
            # containing this module)
            pass

    def handle_message(self, message, port_name):
        # TODO: Write here the code to handle the messages received by the module (also scheduled self messages)
        pass