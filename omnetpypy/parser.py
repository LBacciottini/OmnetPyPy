r"""This module provides the tools to parse the YAML configuration and topology files"""
import importlib

import yaml

from omnetpypy.front_end import CompoundModule
from omnetpypy.front_end.channel import Channel


def parse_simple_modules(simple_descriptors):
    r"""
    Parse the simple modules from raw parsed data

    Parameters
    ----------
    simple_descriptors : list
        A list containing the simple modules' data as dictionaries with two keys "name" and "package"

    Returns
    -------
    list of :class:`~omnetpypy.front_end.simple_module.SimpleModule`
        A list of the simple module classes
    """

    # sanity check. Check that the dict has only one key "simple", the value of which is a list,
    # and each element of the list is a dict containing only the keys "name" and "package"
    for entry_dict in simple_descriptors:
        if (not isinstance(entry_dict, dict) or len(entry_dict) != 2 or
                "name" not in entry_dict or "package" not in entry_dict):
            raise ValueError("Invalid simple module format. Each module should have only the keys 'name' and 'package'")

    module_classes = []
    for module_data in simple_descriptors:
        name = module_data['name']
        package = module_data.get('package', None)
        # Import module dynamically
        # import with importlib
        imported = importlib.import_module(name=package)
        module_class = getattr(imported, name)

        module_classes.append(module_class)
    return module_classes


def parse_channels(channel_descriptors):
    r"""
    Parse the channels from raw parsed data

    Parameters
    ----------
    channel_descriptors : list
        A list of dictionaries containing the channel data

    Returns
    -------
    list of :class:`~omnetpypy.front_end.channel.Channel`
        A list of the channel classes
    """

    # sanity check. Check that the dict has only one key "simple", the value of which is a list,
    # and each element of the list is a dict containing only the keys "name" and "package"
    for entry_dict in channel_descriptors:
        if (not isinstance(entry_dict, dict) or len(entry_dict) != 2 or
                "name" not in entry_dict or "package" not in entry_dict):
            raise ValueError("Invalid channel format. Each module should have only the keys 'name' and 'package'")

    channel_classes = []
    for channel_descriptors in channel_descriptors:
        name = channel_descriptors['name']
        package = channel_descriptors['package']
        # Import channel dynamically if not already imported
        imported = importlib.import_module(name=package)
        channel_class = getattr(imported, name)
        channel_classes.append(channel_class)
    return channel_classes


def parse_connection(connection_data, compound_module, channel_classes, next_channel_id):
    r"""
    Parse a connection from raw parsed data and entity classes within a compound module

    Parameters
    ----------
    connection_data : dict
        A dictionary containing the connection data
    compound_module : :class:`~omnetpypy.front_end.compound_module.CompoundModule`
        The compound module instance
    channel_classes : list
        A list of the channel classes, already imported
    next_channel_id : int
        The current next channel identifier, used to generate unique identifiers for channels

    Returns
    -------
    int
        The new next channel identifier

    Raises
    ------
    Exception
        If the connection data is invalid
    """
    source = connection_data['source']
    target = connection_data['target']
    source_module, source_port = source.split('.')
    target_module, target_port = target.split('.')
    if source_module == "self":
        source_module = compound_module
    else:
        source_module = compound_module.sub_modules[source_module]
    if target_module == "self":
        target_module = compound_module
    else:
        target_module = compound_module.sub_modules[target_module]

    # check if the "type" field is present

    if "type" in connection_data and connection_data["type"] == "forward input":
        source_module.ports[source_port].forward_input(target_module.ports[target_port])

    elif "type" in connection_data and connection_data["type"] == "forward output":
        source_module.ports[source_port].forward_output(target_module.ports[target_port])

    elif "type" in connection_data and connection_data["type"] == "subscribed":
        target_module.ports[target_port].subscribe_to(source_module.ports[source_port])

    elif "type" not in connection_data and "channel" not in connection_data:
        channel = None
        source_module.connect(local_port=source_port, remote_entity=target_module, remote_port=target_port,
                              channel=channel)

    elif "type" not in connection_data and "channel" in connection_data:
        if connection_data["channel"] == "default":
            # in this case we gather the parameters and instantiate a default channel
            parameters = connection_data.get("parameters", {}).copy()
            parameters["name"] = "channel_" + str(next_channel_id)
            parameters["identifier"] = next_channel_id
            next_channel_id += 1
            channel = Channel(**parameters)
        else:
            # in this case we have to instantiate the channel
            channel_classname = connection_data["channel"]
            # find the channel class iterating over the module_classes and looking for the class with the same name
            channel_class = None
            for channel_class in channel_classes:
                if channel_class.__name__ == channel_classname:
                    channel_class = channel_class
                    break
            parameters = connection_data.get("parameters", {})
            parameters["name"] = f"{channel_class}_" + str(next_channel_id)
            parameters["identifier"] = next_channel_id
            next_channel_id += 1
            channel = channel_class(**parameters)

        # the channel is added to the compound module as a sub entity
        compound_module.add_sub_module(channel)

        source_module.connect(local_port=source_port, remote_entity=target_module, remote_port=target_port,
                              channel=channel)
    else:
        raise Exception(f"Invalid connection: {connection_data}")

    return next_channel_id


def sanitize_compound_descriptors(compound_descriptors):
    r"""
    Sanitize the compound descriptors to ensure there is no submodule dependency loop that would cause endless
    recursion.

    Parameters
    ----------
    compound_descriptors : list
        The list of compound module descriptors

    Raises
    -------
    ValueError
        If a dependency loop is detected
    """

    def check_dependencies(compound_descriptor, stack):
        if compound_descriptor['name'] in stack:
            raise ValueError(f"Dependency loop detected in compound module {compound_descriptor['name']}")
        stack.append(compound_descriptor['name'])
        for submodule in compound_descriptor.get('submodules', []):
            type_name = submodule['type']
            for desc in compound_descriptors:
                if desc['name'] == type_name:
                    check_dependencies(desc, stack)
        stack.pop()

    for descriptor in compound_descriptors:
        check_dependencies(descriptor, [])


def instantiate_compound_module(name, module_classes, channel_classes, compound_descriptors,
                                next_module_id, next_channel_id):
    r"""
    Instantiate a compound module from its yaml descriptor. The function is recursive, as a compound module can contain
    other compound modules. In such case, inner compound modules are fully initialized first.

    Parameters
    ----------
    name : str
        The name of the compound module
    module_classes : list
        A list of the simple module classes, already imported
    channel_classes : list
        A list of the channel classes, already imported
    compound_descriptors : list
        The list of compound module descriptors, used to instantiate the compound modules when needed
    next_module_id : int
        The current next simple module identifier
    next_channel_id : int
        The current next channel identifier

    Returns
    -------
    tuple
        The compound module instance (:class:`~omnetpypy.front_end.compound_module.CompoundModule`), the new next simple
        module identifier, the new next channel identifier, and the new next compound module identifier

    Raises
    ------
    ValueError
        If the compound module name is not found in the descriptors or one of its submodules was not defined
    """

    descriptor = None
    for desc in compound_descriptors:
        if desc['name'] == name:
            descriptor = desc
            break
    if descriptor is None:
        raise ValueError(f"Compound module {name} not found in the descriptors")

    ports = [port['name'] for port in descriptor.get('ports', [])]
    parameters = {'name': name, 'identifier': next_module_id, 'port_names': ports, 'parent': None}
    kwargs = descriptor.get('parameters', {})
    parameters.update(kwargs)
    next_module_id += 1
    compound_module = CompoundModule(**parameters)
    for submodule_data in descriptor.get('submodules', []):
        type_name = submodule_data['type']
        # find the submodule class iterating over the module_classes and looking for the class with the same name
        submodule_instance = None
        # first look for a simple module with that name
        for module_class in module_classes:
            if module_class.__name__ == type_name:
                submodule_class = module_class

                sub_name = submodule_data['name']
                parameters = submodule_data.get('parameters', {})
                parameters['name'] = sub_name
                parameters['identifier'] = next_module_id
                next_module_id += 1
                submodule_instance = submodule_class(**parameters)

                break
        # if not found, look for a compound module with that name
        for compound_desc in compound_descriptors:
            if compound_desc['name'] == type_name:

                submodule_instance, next_module_id, next_channel_id = instantiate_compound_module(type_name,
                                                                                                  module_classes,
                                                                                                  channel_classes,
                                                                                                  compound_descriptors,
                                                                                                  next_module_id,
                                                                                                  next_channel_id)

                break

        # if still not found, raise an exception
        if submodule_instance is None:
            raise ValueError(f"No simple or compound module with name {type_name} was found")

        compound_module.add_sub_module(submodule_instance)

    connections = descriptor.get('connections', [])

    for connection_data in connections:
        # we check whether there is a field name "for i in x to y"
        # if so, we have to create a connection for iteration
        # get the keys of the dictionary and check if one starts with "for"
        keys = connection_data.keys()
        loop_found = False
        for key in keys:
            if key.startswith("for"):
                # get the range of the iteration
                bottom = int(key.split(" ")[3])
                top = int(key.split(" ")[5])
                # get the name of the variable
                var_name = key.split(" ")[1]
                # get the connection data
                conn_data = connection_data[key]
                # iterate over the range
                for i in range(bottom, top + 1):
                    # format conn_data['source'] and conn_data['target'] by replacing the variable name
                    new_data = conn_data.copy()
                    for k, v in new_data.items():
                        if k == "source" or k == "target":
                            new_data[k] = v.replace("{" + var_name + "}", str(i))

                            # there might also occur "{i+l}" or "{i-l}" in the string
                            # we have to replace these as well using pattern matching
                            # we can use the re module for this
                            # we have to import the re module
                            import re
                            # we have to find all occurences of "{i+l}" and "{i-l}" in the string, for any l
                            # we can use the findall method of the re module
                            # we have to define the pattern first
                            pattern = r"{i[+-]\d+}"
                            # then we can use the findall method
                            matches = re.findall(pattern, new_data[k])
                            # we have to iterate over the matches and replace them in the string
                            for match in matches:
                                # we have to extract the number and the operator from the match
                                operator = match[2]
                                number = int(match[3:-1])
                                # we have to replace the match in the string
                                if operator == "+":
                                    new_data[k] = new_data[k].replace(match, str(i + number))
                                else:
                                    new_data[k] = new_data[k].replace(match, str(i - number))

                    # parse the connection
                    next_channel_id = parse_connection(new_data, compound_module, channel_classes,
                                                       next_channel_id)
                    loop_found = True

        if not loop_found:
            next_channel_id = parse_connection(connection_data, compound_module, channel_classes,
                                               next_channel_id)

    return compound_module, next_module_id, next_channel_id


def parse_yaml_file(file_path):
    r"""
    Parse the YAML configuration file.

    Parameters
    ----------
    file_path : str
        The path to the YAML configuration file

    Returns
    -------
    dict
        The parsed configuration, as a dictionary directly loaded from the YAML file
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def parse_yaml_directory(directory_path, sim_context):
    r"""
    Parse all the YAML files from the specified directory. Files are parsed in the order listed below.
    The directory should contain:

        - "config.yaml": the configuration file
        - "simple.yaml": the file listing all the simple modules used in the simulation
        - "channels.yaml" (optional): the file listing all the custom channels used in the simulation
        - "compound.yaml" (optional): the file listing all the compound modules used in the simulation
        - "network.yaml": the network topology file

    Parameters
    ----------
    directory_path : str
        The path to the directory containing the YAML files
    sim_context : :class:`~omnetpypy.simulation.Simulation`
        The simulation with its context

    Returns
    -------
    tuple
        A tuple containing the configuration, the simple modules, the channels, and the compound modules

    Raises
    ------
    FileNotFoundError
        If one of the mandatory files is missing
    ValueError
        If one of the files has an invalid format or there is a dependency loop in the compound modules

    """
    initial_module_id = 10100
    initial_channel_id = 2222200000

    # Parse the simple modules
    simple_data = parse_yaml_file(directory_path + "./simple.yaml")
    # sanity check. Check that the dict has only one key "simple", the value of which is a list,
    # and each element of the list is a dict containing only the keys "name" and "package"
    if len(simple_data) != 1 or not isinstance(simple_data["simple"], list):
        raise ValueError("Invalid simple module format. It should have only one key 'simple' with a list of modules")
    simple_descriptors = simple_data.get("simple", [])
    simple_modules = parse_simple_modules(simple_descriptors)

    # Parse the channels
    # checking if the file exists
    try:
        channel_data = parse_yaml_file(directory_path + "./channels.yaml")
        if len(channel_data) != 1 or not isinstance(channel_data["channels"], list):
            raise ValueError(
                "Invalid channel yaml format. It should have only one key 'channels' with a list of channels")
        channel_data = channel_data.get("channels", [])
    except FileNotFoundError:
        channel_data = []
    channel_classes = parse_channels(channel_data)

    # Parse the compound modules
    # checking if the file exists
    try:
        compound_data = parse_yaml_file(directory_path + "./compound.yaml")
        compound_data = compound_data.get("compound", [])
        sanitize_compound_descriptors(compound_data)
    except FileNotFoundError:
        compound_data = []
    compound_descriptors = compound_data

    # Parse the network topology
    network = parse_yaml_file(directory_path + "./network.yaml")
    # sanity check. Check that the dict has only one key "network", the value of which is a list,
    if not isinstance(network["network"], list) or len(network["network"]) != 1:
        raise ValueError("Invalid network format. It should have only one key 'network'")
    network = network["network"]

    network_name = network[0]['name']

    # concatenate
    compound_descriptors += network

    network_module, _, _ = instantiate_compound_module(network_name, simple_modules, channel_classes,
                                                       compound_descriptors, initial_module_id, initial_channel_id)
    sim_context.connector.add_entity(network_module)

    return network_module
