"""
This module is responsible for parsing the YAML configuration file and returning
the compound module containing the whole simulation topology.
"""
import importlib

import yaml

from discrete_sim.front_end import CompoundModule
from discrete_sim.front_end.channel import Channel


def parse_simple_modules(simple_data):
    module_classes = []
    for module_data in simple_data:
        name = module_data['name']
        package = module_data.get('package', None)
        # Import module dynamically
        # import with importlib
        imported = importlib.import_module(name=package)
        module_class = getattr(imported, name)

        module_classes.append(module_class)
    return module_classes


def parse_channels(channel_data):
    channel_classes = []
    for channel_data in channel_data:
        name = channel_data['name']
        package = channel_data['package']
        # Import channel dynamically if not already imported
        imported = importlib.import_module(name=package)
        channel_class = getattr(imported, name)
        channel_classes.append(channel_class)
    return channel_classes


def parse_compound_modules(compound_data, module_classes, channel_classes):
    compound_modules = []
    next_simple_id = 10100
    next_compound_id = 1111100000
    next_channel_id = 2222200000
    for compound_mod in compound_data:
        name = compound_mod['name']
        ports = [port['name'] for port in compound_mod.get('ports', [])]
        parameters = {'name': name, 'identifier': next_compound_id, 'port_names': ports, 'parent': None}
        kwargs = compound_mod.get('parameters', {})
        parameters.update(kwargs)
        next_compound_id += 1
        submodules = []
        compound_module = CompoundModule(**parameters)
        compound_modules.append(compound_module)
        for submodule_data in compound_mod.get('submodules', []):
            type_name = submodule_data['type']
            # find the submodule class iterating over the module_classes and looking for the class with the same name
            submodule_class = None
            for module_class in module_classes:
                if module_class.__name__ == type_name:
                    submodule_class = module_class
                    break
            if submodule_class is None:
                raise Exception(f"Module class {type_name} not found")

            sub_name = submodule_data['name']
            parameters = submodule_data.get('parameters', {})
            parameters['name'] = sub_name
            parameters['identifier'] = next_simple_id
            next_simple_id += 1
            submodule_instance = submodule_class(**parameters)
            compound_module.add_sub_entity(submodule_instance)
            submodules.append(sub_name)

        for connection_data in compound_mod.get('connections', []):
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
                        new_data = {}
                        for k, v in conn_data.items():
                            new_data[k] = v.replace("{"+var_name+"}", str(i))

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
                                number = int(match[3:])
                                # we have to replace the match in the string
                                if operator == "+":
                                    new_data[k] = new_data[k].replace(match, str(i+number))
                                else:
                                    new_data[k] = new_data[k].replace(match, str(i-number))

                        # parse the connection
                        next_channel_id = parse_connection(new_data, compound_module, channel_classes,
                                                           next_channel_id)
                        loop_found = True

            if not loop_found:
                next_channel_id = parse_connection(connection_data, compound_module, channel_classes,
                                                   next_channel_id)

    return compound_modules


def parse_connection(connection_data, compound_module, channel_classes, next_channel_id):
    source = connection_data['source']
    target = connection_data['target']
    source_module, source_port = source.split('.')
    target_module, target_port = target.split('.')
    if source_module == "self":
        source_module = compound_module
    else:
        source_module = compound_module.sub_entities[source_module]
    if target_module == "self":
        target_module = compound_module
    else:
        target_module = compound_module.sub_entities[target_module]

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
            parameters = connection_data.get("parameters", {})
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
        compound_module.add_sub_entity(channel)

        source_module.connect(local_port=source_port, remote_entity=target_module, remote_port=target_port,
                              channel=channel)
    else:
        raise Exception(f"Invalid connection: {connection_data}")

    return next_channel_id


# Parse the YAML configuration
def parse_topology(config_file, sim_context):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        simple_modules = parse_simple_modules(config.get('simple', []))
        channels = parse_channels(config.get('channels', []))
        compound_modules = parse_compound_modules(config.get('network', []), simple_modules, channels)
        if len(compound_modules) == 0 or len(compound_modules) > 1:
            raise Exception("Only one compound module is allowed in the network for the moment")
        sim_context.connector.add_entity(compound_modules[0])

    return compound_modules[0]


def parse_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config
