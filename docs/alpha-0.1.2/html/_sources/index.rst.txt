omnetpypy package docs
====================================

Welcome to the omnetpypy package documentation.
This package implements a Pythonic network simulation framework for
discrete event simulation inspired in concepts by OMNeT++.

You can download and install the omnetpypy package by
simply using pip:

.. code-block:: bash

    pip install omnetpypy

The package is aimed for those who appreciate the modular structure of
OMNeT++, but want Python's simplicity and flexibility.

The main players within the package are the following:

1. **Simple Modules**: These are the basic building blocks of the simulation.
   They are the entities that interact with each other by sending messages
   and processing them. The behavior of a custom simple module is defined by the
   user by implementing its `handle_message` method.

2. **Compound Modules**: These are non-atomic modules that contain
   other interconnected submodules. They are used to structure the
   simulation model in a hierarchical way and make complex systems
   easier to model. The behavior of a custom compound module is fully
   defined by its submodules and how they are connected to each other.

3. **Ports**: These are how modules interact with the outside world.
   Ports of two different modules can be connected so that messages
   can be exchanged between them. You can also forward the input (output) of a
   port to the input (output) of another module port. This port forwarding is
   crucial to bind compound modules' ports to their submodules ports.

4. **Channels**: When two ports are connected, they are connected through a channel.
   Channels are used to define the communication medium between two modules.
   The channel can be used to model different communication media, such as
   wired or wireless communication, with noise, delay, or loss operations.
   Omnetpypy comes with a default bidirectional channel that can be used for simple simulations.
   It supports fixed delay and fixed loss probability.

5. **Events**: These are the messages that are exchanged between modules. The simulation
   time is advanced by processing events.


To design a simulation, you just follow these steps:

1.
    Determine the simple modules that will be part of the simulation. If you need custom
    behavior, you can create a custom simple module by subclassing `SimpleModule`.

2. Create a yaml file called `simple.yaml` that lists all the simple module classes
   that will be part of the simulation. They are dynamically loaded by the simulation engine.
   Example:

    .. code-block:: yaml

        simple:
            - name: ClientModule
              package: my_package
            - name: ServerModule
              package: another_package

3. (optional) Create a yaml file called `channels.yaml` that lists all the custom channel classes
   that will be part of the simulation. They are dynamically loaded by the simulation engine.

4. (optional) Determine the compound modules that will be part of the simulation. You define compound modules
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

5. Create a yaml file called `network.yaml` that describes the network to simulate. In practice,
   the network is the top-level compound module. Example:

    .. code-block:: yaml

        network:
            - name: MyNetwork
              submodules:
                  - type: "ClientServerModule"
                    name: "client_server"

6. Create yet another yaml file (it's the last one, we promise) named as you want, that contains
   the simulation configuration. Example:

    .. code-block:: yaml

            repetitions: 1 # number of independent runs
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


7. Run the simulation by instantiating an `Experiment` object and calling its `run_experiments` method. Example:

    .. code-block:: python

        from omnetpypy.simulation import Experiment

        experiment = Experiment(config_file="./config.yaml")
        experiment.run_experiments()


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   omnetpypy/backends/backends
   omnetpypy/examples/examples
   omnetpypy/front_end/front_end
   omnetpypy/parser
   omnetpypy/sim_log
   omnetpypy/simulation
   omnetpypy/utilities


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`