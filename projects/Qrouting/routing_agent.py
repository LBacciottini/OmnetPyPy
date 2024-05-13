

def route(input_features, current_node):
    """
    Determine the next hop for a request, based on the input features.
    Also updates the input features by adding the following output feature fields:
    - "ACTION_NODE_ID": the name of the chosen next hop
    - "ACTION_DISTANCE": the classical routing distance from the chosen next hop to the destination
    - "ACTION_MIN_Q_LENGTH"
    - "ACTION_MAX_Q_LENGTH"
    - "ACTION_MEAN_Q_LENGTH"
    - "ACTION_MIN_DISTANCE"
    - "ACTION_MAX_DISTANCE"
    - "ACTION_MEAN_DISTANCE"
    - "REWARD": the reward for the current routing decision
    - "TARGET"


    Parameters
    ----------
    input_features : dict
        The input features for the routing decision. The keys are as follows:
        - "TIMESTEP": the current simulation timestep
        - "EPR_ID": the ID of the request
        - "PREV_TIMESTEP": TIMESTEP - 1
        - "FIDELITY": the current fidelity of the pair
        - "Q_LENGTH": the length of the queue at the current node
        - "DISTANCE": the classical routing distance to the request destination
        - "NEIGHBOR_MIN_Q_LENGTH": the minimum queue length among the neighbors
        - "NEIGHBOR_MAX_Q_LENGTH": the maximum queue length among the neighbors
        - "NEIGHBOR_MEAN_Q_LENGTH": the average queue length among the neighbors
        - "NEIGHBOR_MIN_DISTANCE": the minimum classical routing from neighbors to destination
        - "NEIGHBOR_MAX_DISTANCE": the maximum classical routing from neighbors to destination
        - "NEIGHBOR_MEAN_DISTANCE": the average classical routing from neighbors to destination


    Returns
    -------
    str
        The name of the next hop for the request.

    """
    pass