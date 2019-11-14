import numpy as np
import networkx as nx
import random


def generate_network(name: str, **kwargs) -> nx.Graph:
    """
    This is the factory method that returns a specific network.

    :param name: A string with the name of the network type.
        Possible options:
        "spatial_random_graph", "ring", "grid"
    :param kwargs: A dictionary containing the parameter names as keys and their respective values
        as values to be passed to the function that produces the network.
    :raises: ValueError if not one of the possible network topologies is selected.
    :returns: A NetworkX Graph object.
    """
    if name == "grid":
        network = _produce_grid_network(**kwargs)
    elif name == "spatial_random_graph":
        network = _produce_spatial_random_graph(**kwargs)
    elif name == "ring":
        network = _produce_ring_network(**kwargs)
    else:
        network = _produce_networkx_graph(name,**kwargs)
    #else:
    #    raise ValueError("Can only select from the options ['grid', 'spatial_random_graph', 'ring']")

    if 'ms_rewiring' in kwargs:
        network = execute_ms_rewiring(network,kwargs['ms_rewiring'])

    return network


def read_network(network_input: np.ndarray or str):
    """
    This function takes the structure of an empirically measured network, provided as an adjacency matrix,
    and creates a network graph object out of it.

    :param network_input: Either an adjacency matrix where the entry (i,j) represents whether an edge between
        i and j exists or if applicable, its strength,
        or the path to a file containing an edge list
    """
    if isinstance(network_input, np.ndarray):
        return nx.from_numpy_matrix(network_input)
    else:
        with open(network_input, "rb") as edge_list:
            return nx.read_edgelist(edge_list)


def _produce_grid_network(**kwargs) -> nx.Graph:
    """
    This method produces a grid graph, connected to itself as a torus. Each agent on the grid is
    connected to its neighborhood depending on the parameters "neighborhood" and "radius".

    :param int=49 num_agents: How many agents the network contains.
    :param String=moore neighborhood: Either "von_neumann" or "moore". Von Neumann connects each agent to its 4 neighbors
        in each cardinal direction. In a Moore neighborhood, each agent is connected to their 8 immediate neighbors.
    :param int=1 radius: Increases the number of connections further than the immediate neigbourhood.
        An agent in a Moore neighborhood with radius 2 has 24 connections.
    :returns: A NetworkX Graph object.
    """
    # todo: put in maslov sneppen rewiring here as well?

    # check the parameters or initialize default values
    try:
        num_agents = kwargs["num_agents"]
    except KeyError:
        # print("Number of agents was not specified, default value 49 is used.")
        num_agents = 49
    try:
        neighborhood = kwargs["neighborhood"]
    except KeyError:
        # print("neighborhood type was not specified, default value 'moore' is used.")
        neighborhood = "moore"
    try:
        radius = kwargs["radius"]
    except KeyError:
        # print("Radius was not specified, default value 1 is used.")
        radius = 1
    G = nx.grid_2d_graph(int(num_agents ** (1 / 2)), int(num_agents ** (1 / 2)), periodic=True, create_using=None)
    if neighborhood == "moore":
        for i in G.nodes():  # for each agent
            #    east,  west,  north,  south
            lst = [i[0] + 1, i[0] - 1, i[1] + 1, i[1] - 1]  # get a list of the grid neighbor indices
            for n, j in enumerate(lst):  # n is the index "index" j is the index itself
                # if the index is outside of the range of possible values
                if j == -1: lst[n] = max(G.nodes())[0]  # connect the most southern (?) node with the most northern (?)
                if j == max(G.nodes())[0] + 1: lst[
                    n] = 0  # or connect the most northern (?) node to the most southern (?)
            nneigh = [(lst[1], lst[2]), (
                lst[0], lst[2])]  # list of two tuples, one for each neighbor, change only the northern neighbors
            for k in nneigh:
                G.add_edge(i, k)
        if num_agents <= 100:
            G = nx.relabel_nodes(G, dict(zip(G.nodes(), [j[0] * 10 + j[1] for j in [list(i) for i in G.nodes()]])),
                                 copy=False)
            # the mapping here makes sure that nodes get assigned an integer label that corresponds to their original
            # positioning tuple (i.e. (3,4) becomes 34)
        else:
            G = nx.convert_node_labels_to_integers(G)
        return G
    elif neighborhood == "von_neumann":
        if radius == 1:
            return nx.convert_node_labels_to_integers(G)
        elif radius == 1.5:
            # this is moore
            for i in G.nodes():  # for each agent
                #     #    east,  west,  north,  south
                lst = [i[0] + 1, i[0] - 1, i[1] + 1, i[1] - 1]  # get a list of the grid neighbor indices
                for n, j in enumerate(lst):  # n is the index "index" j is the index itself
                    # if the index is outside of the range of possible values
                    if j == -1:
                        lst[n] = max(G.nodes())[0]  # connect the most southern (?) node with the most northern (?)
                    if j == max(G.nodes())[0] + 1:
                        lst[n] = 0  # or connect the most northern (?) node to the most southern (?)
                nneigh = [(lst[1], lst[2]), (
                    lst[0], lst[2])]  # list of two tuples, one for each neighbor, change only the northern neighbors
                for k in nneigh:
                    G.add_edge(i, k)
            return nx.convert_node_labels_to_integers(G)
        if radius == 2:
            for i in G.nodes():  # for each agent
                # diagonal neighbors
                lst = [i[0] + 1, i[0] - 1, i[1] + 1]  # get a list of the grid neighbor indices
                for n, j in enumerate(lst):  # n is the index "index" j is the index itself
                    # if the index is outside of the range of possible values
                    if j == -1:
                        lst[n] = max(G.nodes())[0]  # connect the most southern (?) node with the most northern (?)
                    if j == max(G.nodes())[0] + 1:
                        lst[n] = 0  # or connect the most northern (?) node to the most southern (?)
                # radius neighbors
                extended = [i[1] + 2, i[0] + 2]
                for n, j in enumerate(extended):  # n is the index "index" j is the index itself
                    # if the index is outside of the range of possible values
                    if j == max(G.nodes())[0] + 1:
                        extended[n] = 0  # or connect the most northern (?) node to the most southern (?)
                    if j == max(G.nodes())[0] + 2:
                        extended[n] = 1
                nneigh = [(lst[1], lst[2]), (lst[0], lst[2]), (i[0], extended[0]), (
                    extended[1],
                    i[1])]  # list of two tuples, one for each neighbor, change only the northern neighbors
                for k in nneigh:
                    G.add_edge(i, k)
            return nx.convert_node_labels_to_integers(G)


def _produce_ring_network(**kwargs) -> nx.Graph:
    """
    This method produces a ring network with varying number of neighbors.

    :param int=49 num_agents: The number of agents the network should contain.
    :param int=2 num_neighbors: The number of neighbors per agent. Must be an even number.
    :returns: A NetworkX Graph object.
    """
    #todo: properly cite MS

    # check the parameters or initialize default values
    try:
        num_agents = kwargs["num_agents"]
    except KeyError:
        # print("Number of agents was not specified, default value 49 is used.")
        num_agents = 49
    try:
        num_neighbors = kwargs["num_neighbors"]
    except KeyError:
        # print("Number of neighbors was not specified, default value 2 is used.")
        num_neighbors = 2

    # todo: decide about adding seed
    return nx.watts_strogatz_graph(num_agents, num_neighbors, 0)


def _produce_spatial_random_graph(**kwargs) -> nx.Graph:
    """
    This method produces a Spatial Random Graph.

    :param int=49 num_agents: How many agents the network contains.
    :param int=8 min_neighbors: How many neighborhood each agent should have at least.
    :param float=1 proximity_weight: Determines how much spatial distance in the grid matters in the rewiring process.
    :returns: A networkx Graph object.
    """
    #todo: description

    # check the parameters or initialize default values
    num_agents = kwargs.get("num_agents", 49)
    min_neighbors = kwargs.get("min_neighbors", 8)
    proximity_weight = kwargs.get("proximity_weight", 1)
    return_positions = kwargs.get('return_positions', False)

    xypos = np.column_stack((np.random.uniform(0, 100, num_agents), np.random.uniform(0, 100, num_agents)))

    def dist(posA, posB, proximity_weight):  # returns the probability as a function of distance
        return np.exp(-proximity_weight * np.sqrt(np.sum((posA - posB) ** 2)))

    distmatrix = np.zeros((num_agents, num_agents))

    for i in range(num_agents):
        for j in range(num_agents):
            if i == j:
                distmatrix[i, j] = 0  # later turned to 0!
            else:
                distmatrix[i, j] = dist(xypos[i], xypos[j],proximity_weight)

    # pick min_neighbors neighbors with a probability equal to their relative euclidean distance
    edgelist = []
    degreelist = []
    for i in range(num_agents):
        distp = distmatrix[i]

        for one, two in edgelist:
            if two == i: distp[one] = 0  # prevents creating links that already exist
        distp /= distp.sum()  # normalizing the probabilities

        if degreelist.count(i) < min_neighbors:  # give i up to min_neighbors new neighbors.
            # Does not prevent i (as j) from getting > min_neighbors links

            try:
                alters = np.random.choice(num_agents, min_neighbors - degreelist.count(i), replace=False, p=distp)
                for j in alters:
                    edgelist.append([i, j])
                    degreelist.append(i)
                    degreelist.append(j)
            except(ValueError):
                print(
                    "Please pick a lower value for the proximity weight. This value creates too many probability values of 0")

    G = nx.Graph()
    G.add_nodes_from([i for i in range(num_agents)])
    G.add_edges_from(edgelist)

    if return_positions:
        return G, distmatrix
    else:
        return G


def _produce_networkx_graph(name: str,**kwargs):
    """
    This method allows for passing on the graph generation to one of the generators included in the
    `NetworkX package <https://networkx.github.io/documentation/stable/reference/generators.html>`__. Provide the name
    of the method as the first argument here, and pass all (required) arguments for the NetworkX function in the kwargs
    dictionary.

    :param name: Name of the NetworkX graph generator to be used
    :param kwargs: A dictionary containing the parameter names as keys and their respective values as values to be
        passed to the function that produces the network.
    :return: A NetworkX Graph object.
    """
    graph_generator = getattr(nx,name)

    import inspect
    graph_generator_arguments = inspect.getfullargspec(graph_generator)
    intersection_dict = {k: kwargs[k] for k in kwargs if k in graph_generator_arguments.args}

    return graph_generator(**intersection_dict)


def execute_ms_rewiring(network: nx.Graph, rewiring_prop: float):
    """
    This method executes Maslov Sneppen rewiring (Maslov & Sneppen, 2002). Until a given proportion of the network
    edges is rewired, the algorithm will pick two edges at random, remove them, and construct an edge between a
    different combination of nodes that have just lost an edge. Effectively, this introduces randomization of network
    structure, while leaving the degree distribution unchanged. Because the parameter `rewiring_prop` functions as a
    threshold for number of rewiring iterations that need to be executed, it can exceed 1. Actually, to achieve a
    random network starting from a network with structure, the rewiring proportion should exceed 1.

    :param network: NetworkX Graph object
    :param rewiring_prop: A threshold for the minimum proportion of edges in the graph object that need to be rewired.
        Sampling these edges happens with replacement, so rewiring_prop may exceed 1.
    :return: NetworkX Graph object
    """
    ticker = 0
    while rewiring_prop * network.number_of_edges() > ticker:
        agentA, agentB = random.choice(list(network.edges()))
        agentC, agentD = random.choice(list(network.edges()))
        if((agentA != agentC) & (agentA != agentD) & (agentB != agentC) & (agentB != agentD) &
           (network.has_edge(agentA,agentC)==False) & (network.has_edge(agentB,agentD)==False)):
            network.remove_edge(agentA,agentB)
            network.remove_edge(agentC,agentD)
            network.add_edge(agentA,agentC)
            network.add_edge(agentB,agentD)
            ticker += 1
    return network

