.. _compound_modules:

Compound Modules YAML file
====================================

The "compound.yaml" file is **optional**. It is used to specify the
compound modules that are going to be used in the simulation.

Differently from simple modules and channels, compound modules are not associated to a Python class.
Instead, they are used to group simple modules and/or other compound modules together in complex structures.

This file thus describes every compound module that is going to be used in the simulation by
defining the following information:

    - The name of the compound module.
    - The list of simple modules and/or other compound modules that are part of the compound module.
    - The connections between the simple modules and/or other compound modules that are part of the compound module.

More technically, the file is a dictionary with one key "compound" that contains a list of dictionaries.
Each dictionary in the list represents a compound module to be imported.

The dictionaries describing the compound modules must have the following keys:

        - "name": the name of the compound module.
        - "ports": a list of strings, each entry is the name of a port of the compound module.
        - "submodules": a list of dictionaries, each one representing a submodule.
        - "connections": a list of dictionaries, each one representing a connection between two submodules.

For example, the structure of the "compound.yaml" file could be as follows

    .. code-block:: yaml

        compound:
          - name: "LocalAreaNetwork1"
            ports:
              - "lan0"
            submodules:
              [...]  # submodules definition
            connections:
              [...]  # connections definition
          - name: "LocalAreaNetwork2"
            ports:
              - "lan0"
            submodules:
              [...]  # submodules definition
            connections:
              [...]  # connections definition

The dictionaries describing the **submodules** must have the following keys:

        - "name": the name of the instance of the submodule. Must be unique within the compound module.
          The name "self" can't be used as a submodule name, because it is reserved to refer to the compound module
          itself in the rest of the file.
        - "type": the type of the submodule, i,e, its class name if its a simple module. If it is a compound module,
          it must also be defined somewhere in the "compound.yaml" file. If it is a simple module class,
          it must be specified in the "simple.yaml" file. Omnetpypy detects and prevents dependency loops between
          compound modules.
        - "parameters" (optional): a dictionary containing the actual parameters that are going to be passed to the submodule
          constructor. If the submodule is a simple module, the parameters must be compatible with the constructor
          of the simple module class.

For example, the structure of a submodule definition in "compound.yaml" could look like this:

    .. code-block:: yaml

        compound:
          - name: "LocalAreaNetwork1"
            [...]
            submodules:
              - name: "client"  # name of the submodule, unique within the compound module
                type: "ClientModule"  # type of the submodule. In this case, it is the class name of a simple module
                parameters:  # parameters to be passed to the constructor of the simple module
                  server_addresses:  # IP addresses of the servers that this client knows
                    - "192.168.1.1"
                    - "10.0.0.1"
            [...]

The dictionaries describing the **connections** have the following keys:

        - "source": the source submodule and its port as a string in the format "submodule_name.port_name". The source
          module name can also be set "self" to refer to the compound module itself.
        - "target": the target submodule and its port as a string in the format "submodule_name.port_name". The target
          module name can also be set "self" to refer to the compound module itself.
        - "channel": A dictionary with "type" and "parameters" keys for the channel to be used, or the string "default",
          if the default channel class should be used. The channel "type" must be defined in the "channels.yaml" file.
        - "delay" (optional): the fixed delay of the connection in the simulation time unit, applied to all messages.
          Only used if the channel is "default". Defaults to 0.
        - "loss_prob" (optional): the loss probability of the channel, applied to all messages.
          Only used if the channel is "default". Defaults to 0.
        - "type" (optional): The kind of connection. If not specified, the connection uses the
          :meth:`~omnetpypy.front_end.port.Port.connect` method. Other types of connection are "forward_input",
          "forward_output", "subscribed". See the class :class:`~omnetpypy.front_end.port.Port` for more details.
          if the type field is specified, the channel is ignored.

          Sometimes there are many connections that are similar, but with different indexes. In this case, the user can
          use a Python-like syntax to define multiple connections with the same structure. For example,
          the two following snippets are equivalent:

            .. code-block:: yaml

                connections:
                  - source: "client0.lan0"
                    target: "router.lan0"
                    channel: "default"
                    delay: 10  # [ms]
                  - source: "client1.lan0"
                    target: "router.lan1"
                    channel: "default"
                    delay: 10  # [ms]

            .. code-block:: yaml

                connections:
                  - for i in 0 to 1:
                      source: "client{i}.lan0"
                      target: "router.lan{i}"
                      channel: "default"
                      delay: 10  # [ms]

Let's now put all the pieces together. Here is an example of a full "compound.yaml" file with two compound modules
modelling two different local area networks:

        .. code-block:: yaml

            compound:
              - name: "LocalAreaNetwork1"  # a client connected to a server
                ports:
                  - "lan0"  # exposed by the server
                submodules:
                  - name: "client"
                    type: "ClientModule"
                    parameters:
                      server_addresses:
                      - "192.168.1.1"
                      - "10.0.0.1"
                  - name: "server"
                    type: "ServerModule"
                    parameters:
                      address: "192.168.1.1"
                      num_ports: 2  # lan0 and lan1
                connections:
                  - source: "client.lan0"
                    target: "server.lan0"
                    channel: "default"
                    delay: 10  # [ms]
                  - source: "server.lan1"
                    target: "*this.lan0"
                    type: "forward_output"
                  - source: "*this.lan0"
                    target: "server.lan1"
                    type: "forward_input"

                - name: "LocalAreaNetwork2"  # two clients connected to a server through a router
                  ports:
                    - "lan0"  # exposed by the router
                  submodules:
                    - name: "client0"
                      type: "ClientModule"
                      parameters:
                        server_addresses: "10.0.0.1"
                    - name: "client1"
                      type: "ClientModule"
                      parameters:
                      server_addresses: "10.0.0.1"
                    - name: "server"
                      type: "ServerModule"
                      parameters:
                      address: "10.0.0.1"
                    - name: "router"
                      type: "RouterModule"
                      num_ports: 100
                  connections:
                    - for i in 0 to 1:
                        source: "client{i}.lan0"
                        target: "router.lan{i}"
                        channel: "default"
                        delay: 10  # [ms]
                    - source: "router.lan2"
                      target: "server.lan0"
                      channel: "default"
                      delay: 10  # [ms]
                    - source: "router.lan3"
                      target: "*this.lan0"
                      type: "forward_output"
                    - source: "*this.lan0"
                      target: "router.lan3"
                      type: "forward_input"











