Welcome to omnetpypy docs (alpha-0.1.3)
========================================

Welcome to the omnetpypy package documentation!
This package implements a Pythonic network simulation framework for
discrete event simulation inspired in concepts by OMNeT++.

You can download and install the omnetpypy package by
simply using pip:

.. code-block:: bash

    pip install omnetpypy

The package is aimed for those who appreciate the modular structure of
OMNeT++, but want Python's simplicity and flexibility.

OmnetPyPy is open-source and the source code is on `GitHub <https://github.com/LBacciottini/OmnetPyPy>`_.
Everyone is welcome to contribute to the project!

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

**Check out a mini tutorial on how to setup a simple simulation**
:ref:`here <yaml_formats>` **.** You will also find detailed documentation on all
the yaml files that are used to configure the experiment.

Below, you find the documentation tree of the package.

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
   yaml_formats/yaml_formats

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`