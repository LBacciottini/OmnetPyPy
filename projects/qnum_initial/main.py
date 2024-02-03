"""
Main file of the project
"""

from discrete_sim import Experiment

if __name__ == '__main__':

    config_file = "qnum_initial_config.yaml"
    topology_file = "qnum_initial_topology.yaml"

    experiment = Experiment(config_file=config_file)
    experiment.run_simulations()
