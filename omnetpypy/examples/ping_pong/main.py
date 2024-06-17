"""
Main file for the ping pong simulation example.
"""

from omnetpypy import Experiment

if __name__ == '__main__':

    config_file = "ping_pong_config.yaml"

    experiment = Experiment(config_file=config_file)
    experiment.run_simulations()
