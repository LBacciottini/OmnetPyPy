r"""
This file contains tests for the qnum simulation.
"""

import unittest
import os
from omnetpypy import Experiment

class TestQNUM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set the working directory to the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(project_root)

    def test_ping_pong(self):
        config_file = "./omnetpypy/examples/qnum_congestion_ctrl_aqm_bidir/config.yaml"
        experiment = Experiment(config_file=config_file)
        experiment.run_simulations()


if __name__ == '__main__':
    unittest.main()
