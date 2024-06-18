.. _simple_yaml:

Simple Modules YAML file
====================================

The "simple.yaml" file is **mandatory**. It is used to specify the
simple modules classes that are going to be used in the simulation.

The file is a dictionary with one key "simple" that contains a list of dictionaries.
Each dictionary in the list represents a simple module class to be imported.

The dictionaries describing the simple modules must have the following keys:

        - "name": the name of the simple module class to be imported.
        - "package": the package where the simple module class is located.

Example of a "simple.yaml" file:

        .. code-block:: yaml

            simple:
            - name: "ClientModule"
                package: "my_simulation.simple_modules"
            - name: "ServerModule"
                package: "my_simulation.simple_modules"
            - name: "RouterModule"
                package: "my_simulation.simple_modules"
            # More simple modules can be added here

