.. _yaml_formats:

Format and purpose of YAML files
=================================

YAML files are used to configure the simulated experiment in a human-readable format
that can be automatized if needed.

In a nutshell, omnetpypy uses YAML files to specify the following information:

 - What modules are going to be used in the simulation.
 - How modules are interconnected to form the network.
 - What parameters characterize the experiment.

Except for the main configuration file, all the other YAML files should be placed in the same
directory, whose path is specified in the main configuration file itself.


To design a simulation, you can just follow these steps:

1. Create a yaml file, named as you want, that contains
   the global experiment configuration. Example:

    .. code-block:: yaml

            repetitions: 35 # number of independent runs
            num_rngs: 50 # number of independent random number generators for each run
            time_unit: "us" # time unit for the simulation, in this case microseconds
            simulate_until: 1000000
            yaml_directory: "./"  # directory where all other yaml files are located, relative to this file
            output_dir: "./out" # directory where the simulation output will be stored, relative to this file
            engine: "simpy" # simulation engine to use, only simpy is supported for now
            num_processes: 8 # number of parallel Python processes

            metrics: # metrics to collect
              - name: "queuing_time"
                type: ["vector", "mean"] # we want the whole vector of samples and the mean

            global_params: # global parameters that can be accessed by any entity in the simulation
              num_servers: 2
              num_clients: 5

    See the :ref:`configuration file format page <config_file>` for details.

2.  Determine the simple modules that will be part of the simulation. If you need custom
    behavior, you can create a custom simple module by subclassing `SimpleModule`.

3. Create a yaml file called `simple.yaml` that lists all the simple module classes
   that will be part of the simulation. They are dynamically loaded by the simulation engine.
   Example:

    .. code-block:: yaml

        simple:
            - name: ClientModule
              package: my_package
            - name: ServerModule
              package: another_package

   See  the :ref:`"simple.yaml" format page <simple_yaml>` for details.

4. (optional) Create a yaml file called `channels.yaml` that lists all the custom channel classes
   that will be part of the simulation. They are dynamically loaded by the simulation engine.

   See the :ref:`"channels.yaml" format page <channels>` for details.

5. (optional) Determine the compound modules that will be part of the simulation. You define compound modules
   in another yaml file called `compound.yaml`. Example:

    .. code-block:: yaml

        compound:
            - name: ClientServerModule
              submodules:
                  - type: "ClientModule"
                    name: "client_1"
                    parameters: # class parameters that will be passed to the constructor
                        num_requests: 100
                        send_rate: 10
                  - type: "ClientModule"
                    name: "client_2"
                    parameters: # class parameters that will be passed to the constructor
                        num_requests: 150
                        send_rate: 8
                  - type: "ServerModule"
                    name: "server"
                    parameters:
                        service_rate: 20
              connections:
                  - source: "client_1.lan" # port with format module_name.port_name
                    target: "server.lan0"
                    channel: "default" # use the default channel, otherwise specify the channel name
                    parameters:
                      delay: 10
                  - source: "client_2.lan" # port with format module_name.port_name
                    target: "server.lan1"
                    channel: "default" # use the default channel, otherwise specify the channel name
                    parameters:
                      delay: 20

    See the :ref:`"compound.yaml" format page <compound_modules>` for details.

6. Create yet another yaml file (it's the last one, we promise!) called `network.yaml` that describes the network to simulate. In practice,
   the network is the top-level compound module. Example:

    .. code-block:: yaml

        network:
            - name: MyNetwork
              submodules:
                  - type: "ClientServerModule"
                    name: "client_server"

    See the :ref:`"network.yaml" format page <network_yaml>` for details.

7. Run the simulation by instantiating an `Experiment` object and calling its `run_experiments` method. Example:

    .. code-block:: python

        from omnetpypy.simulation import Experiment

        experiment = Experiment(config_file="./config.yaml")
        experiment.run_experiments()



For reference, here are all the documentation pages that describe the format of each YAML file:

    .. toctree::
       :maxdepth: 2
       :caption: YAML files formats

       channels
       compound
       configuration
       network
       simple




