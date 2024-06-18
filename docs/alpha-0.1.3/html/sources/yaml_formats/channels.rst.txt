.. _channels:

Channels YAML file
====================================

The "channels.yaml" file is **optional**. It is used to specify what custom channels classes
should be dynamically imported for the experiments.

The file is a dictionary with one key "channels" that contains a list of dictionaries.
Each dictionary in the list represents a custom channel class to be imported.

The dictionaries describing the channels must have the following keys:

    - "name": the name of the channel class to be imported.
    - "package": the package where the channel class is located.

Usually, users define their own classes and import them in the "channels.yaml" file.

Example of a "channels.yaml" file:

    .. code-block:: yaml

        channels:
          - name: "FibreChannel"
            package: "my_simulation.channels"
          - name: "OpenSpaceChannel"
            package: "my_simulation.channels"
        # More channels can be added here

In many cases, omnetpypy users do not need to create custom channels, as the package already provides
a built-in :class:`~omnetpypy.front_end.channel.Channel` class that can be used to model simple
bidirectional channels with fixed delay and loss rate.