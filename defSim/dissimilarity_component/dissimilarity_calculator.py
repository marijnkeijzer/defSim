from abc import ABC, abstractmethod
import networkx as nx
import math
import numpy as np


class DissimilarityCalculator(ABC):
    """
    This class is responsible for determining the distance between nodes, either from one node to another,
    or for every agent in the network to another. The distance could be based on their attributes or actual geodesic
    distance.
    """

    @staticmethod
    @abstractmethod
    def calculate_dissimilarity(network: nx.Graph, agent1_id: int, agent2_id: int, **kwargs) -> float:
        """
        This function calculates how dissimilar two agents are based on their attributes and/or their distance in
        the network.
        Can for example be used to determine whether a neighbor is selected for the influence process.

        :param network: The network in which the agents exist.
        :param agent1_id: The index of the first agent.
        :param agent2_id: The index of the agent to compare with.

        :returns a float value, representing the distance between the two agents
        """
        pass

    @staticmethod
    @abstractmethod
    def calculate_dissimilarity_networkwide(network: nx.Graph, **kwargs):
        """
        Calculates the distance from each agent to each other and sets that distance as an attribute on the edge
        between them.

        :param network: The network that is modified.
        """
        pass


def select_calculator(realization: str) -> DissimilarityCalculator:
    """
    This function works as a factory method for the dissimilarity_component.
    It returns an instance of the Calculator that is asked for.

    :param realization: The type of DissimilarityCalculator. Possible options are ["hamming", "euclidean"]
    :return: An instance of a DissimilarityCalculator
    """
    from .HammingDistance import HammingDistance
    from .EuclideanDistance import EuclideanDistance

    if realization == "hamming":
        return HammingDistance()
    elif realization == "euclidean":
        return EuclideanDistance()
    else:
        raise ValueError("Can only select from the options ['hamming', 'euclidean']")
