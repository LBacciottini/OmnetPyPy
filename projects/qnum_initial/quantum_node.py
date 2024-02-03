from discrete_sim import SimpleModule


class QuantumNode(SimpleModule):
    """
    This class models a Quantum Router along a repeater chain
    """

    def __init__(self, name, identifier):

        port_names = ["q0", "q1", "c0", "c1", "rg0"]
        # first dilemma: do we use separate channels for classical packets  (c0, c1 ports) ?
        # rg0 is used to attach the RequestGenerator

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