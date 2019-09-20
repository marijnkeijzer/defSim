import random

import networkx as nx
from .influence_sim import InfluenceOperator
from ..tools.NetworkDistanceUpdater import update_dissimilarity
from defSim.dissimilarity_component.dissimilarity_calculator import DissimilarityCalculator
from typing import List
import numpy as np


class BoundedConfidence(InfluenceOperator):

    @staticmethod
    def spread_influence(network: nx.Graph, agent_i: int, agents_j: List[int] or int,
                         regime: str, dissimilarity_measure: DissimilarityCalculator, attributes: List[str] = None, **kwargs) -> bool:
        """
        The bounded confidence model is from the family of similarity bias models. These models assume that how strongly
        agents influence each other is dependent on how similar they are.
        In the bounded confidence case the influence 'strength' is either the 'convergence-rate' or 0, if the agents are
        more similar than the threshold 'confidence_level' or below it, respectively.
        In the one-to-one communication regime, the agents can also influence each other if the 'bi-directional' parameter
        is set to true.

        :param network: The network in which the agents exist.
        :param agent_i: the index of the focal agent that is either the source or the target of the influence
        :param agents_j: A list of indices of the agents who can be either the source or the targets of the influence. The list can have a
            single entry, implementing one-to-one communication.
        :param attributes: A list of the names of all the attributes that are subject to influence. If an agent has
            e.g. the attributes "Sex" and "Music taste", only supply ["Music taste"] as a parameter for this function.
            The influence function itself can still be a function of the "Sex" attribute.
        :param regime: Either "one-to-one", "one-to-many" or "many-to-one"
        :param dissimilarity_measure: An instance of a :class:`~defSim.dissimilarity_component.DissimilarityCalculator.DissimilarityCalculator`.
        :param kwargs: Additional parameters specific to the implementation of the InfluenceOperator. Possible parameters are the following:
        :param float=0.8 confidence_level: A number between 0 and 1 determining the cutoff value for the dissimilarity at which
            agents do not interact anymore. 1 means that even the most dissimilar agents still interact, 0 means no interaction.Passed as a kwargs argument.
        :param float=0.5 convergence_rate: A number between 0 and 1 determining how much an agent adopts other agents features. If
            it is one, the influenced agent takes the value of the influencing agent. Passed as a kwargs argument.
        :returns: true if agent(s) were successfully influenced
        """
        try:
            confidence_level = kwargs["confidence_level"]
        except KeyError:
            # print("The confidence level was not specified, default value 49 is used.")
            confidence_level = 0.8
        try:
            convergence_rate = kwargs["convergence_rate"]
        except KeyError:
            # print("The confidence level was not specified, default value 49 is used.")
            convergence_rate = 0.5

        try:
            bi_directional = kwargs["bi_directional"]
        except KeyError:
            # show error message only in the relevant case
            # if regime == "one-to-one":
            # print("Bi-directionality was not specified, default value False is used.")
            bi_directional = False

        # in case of one-to-one, j is only one agent, but we still want to iterate over it
        if type(agents_j) != list:
            agents_j = [agents_j]

        if attributes is None:
            # if no specific attributes were given, take all of them
            attributes = list(network.node[agent_i].keys())

        # whether influence was exerted
        success = False

        influenced_feature = random.choice(attributes)

        if regime != "many-to-one":
            for neighbor in agents_j:
                # todo: this will fail in a global communication regime
                if network.edges[agent_i, neighbor]['dist'] < confidence_level:
                    success = True
                    # j - i
                    feature_difference = network.node[neighbor][influenced_feature] - network.node[agent_i][
                        influenced_feature]
                    # j_t+1 = j - (j-i)
                    network.node[neighbor][influenced_feature] = network.node[neighbor][
                                                                      influenced_feature] - convergence_rate * feature_difference
                    if bi_directional == True and regime == "one-to-one":
                        # i_t+1 = i + (j-i)
                        network.node[agent_i][influenced_feature] = network.node[agent_i][
                                                                        influenced_feature] + convergence_rate * feature_difference
                        update_dissimilarity(network, [agent_i, neighbor], dissimilarity_measure)
                    else:
                        update_dissimilarity(network, [neighbor], dissimilarity_measure)
        else:
            # many to one
            close_neighbors = [neighbor for neighbor in agents_j if
                                network.edges[agent_i, neighbor]['dist'] < confidence_level]
            if len(close_neighbors) != 0:
                success = True
                average_value = np.mean([network.node[neighbor][influenced_feature] for neighbor in close_neighbors])
                feature_difference = average_value - network.node[agent_i][influenced_feature]
                network.node[agent_i][influenced_feature] = network.node[agent_i][
                                                                influenced_feature] + convergence_rate * feature_difference
                update_dissimilarity(network, [agent_i], dissimilarity_measure)

        return success