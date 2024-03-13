"""
Main file of the project
"""

from discrete_sim import Experiment

if __name__ == '__main__':

    config_file = "config.yaml"
    topology_file = "topology.yaml"

    experiment = Experiment(config_file=config_file)
    experiment.run_simulations()
