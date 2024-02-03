"""
Main test file
"""

from discrete_sim import simulation

if __name__ == '__main__':

    config_file = "ping_pong_config.yaml"
    topology_file = "ping_pong_net.yaml"

    experiment = simulation.Experiment(config_file=config_file)
    experiment.run_simulations()
