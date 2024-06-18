.. _network_yaml:

Network YAML file
==================

The "network.yaml" file is **mandatory**. It is used to specify the network module.


The network module is simply a compound module with no ports that represents the whole network
topology to be simulated in the experiments.

The file is a dictionary with one key "network" that contains a list with **one** dictionary.
The dictionary in the list represents the network module to be generated.

The format of this file is as follows:

    .. code-block:: yaml

        network:
          - name: "Network"
            submodules:
              [...]  # submodules definition
            connections:
              [...]  # connections definition

As you can already imagine, it is very similar to the :ref:`"compound.yaml" file format <compound_modules>`. Thus,
we won't repeat the explanation of all the keys here.

Let's proceedby showing how a "network.yaml" file looks like. We continue the example from the "compound.yaml" file:
The network connects the two Local Area Networks (LANs) together through a router:

    .. code-block:: yaml

        network:
          - name: "Network"  # any name can be used
            submodules:
              - name: "router"
                type: "RouterModule"
                parameters:
                  num_ports: 100
              - name: "subnet1"
                type: "LocalAreaNetwork1"
              - name: "subnet2"
                type: "LocalAreaNetwork2"
            connections:
              - source: "router.lan0"
                target: "subnet1.lan0"
                channel: "default"
                delay: 10  # [ms]
              - source: "router.lan1"
                target: "subnet2.lan0"
                channel: "default"
                delay: 5  # [ms]

