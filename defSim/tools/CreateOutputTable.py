from abc import ABC, abstractmethod
import networkx as nx
from typing import List

class OutputTableCreator(ABC):
    """
    This class is responsible for creating the output table.
    """
    @staticmethod
    @abstractmethod
    def create_output(network: nx.Graph, **kwargs) -> int:
        """
        This method receives a NetworkX object, performs some calculation, and outputs a cell for the output table.

        :param network: A NetworkX graph object.

        :returns: #todo: a tuple?
        """
        pass

def create_output_table(network: nx.Graph, realizations: List[str or OutputTableCreator]=[], colnames: List[str]=[],
                        agents: List[int]=[], settings_dict: dict={}, tickwise_output: dict={}, **kwargs) -> int:
    """
    This function works as a factory method for the OutputTableCreator component.
    It calls the create_output function of a specific implementation of the OutputTableCreator and passes to it
    the kwargs dictionary.

    :param network: A NetworkX object from which the focal agent will be selected
    :param realizations: The specific OutputTableCreator that will be used. Currently, the options are:

        * Basic: Returns the realizations Regions, Zones, Isolates, Homogeneity, AverageDistance
        * ClusterFinder: Method to find clusters based on minimal allowed distance between network neighbors as
          defined by the user in the kwargs dictionary. Default is to return the same output as the Regions realization
        * RegionsList:
        * Regions:
        * ZonesList:
        * Zones:
        * Isolates: Reports the number of isolates as found in the ClusterFinder method, based on minimal allowed
          distance between network network neighbors as defined by the user in the kwargs dictionary. Default is to
          return the same output as the Regions realization
        * Homogeneity:
        * AverageDistance:
        * AverageOpinion: REPORTS AVERAGE OPINION (REQUIRES A LIST OF FEATURES FOR WHICH THIS NEEDS TO BE CALCULATED IF
          F>1: passed in the kwargs dictionary as AverageOpinionFeatures)

    :param agents: A list of the indices of all agents that will be considered by the output table.
    :param settings_dict: A dictionary of column names and values that will be added to the output table. Can be used
        to merge output with parameter setting values.
    :param tickwise_output: A dictionary with a list of lists with values of agents on some given feature at each tick
        during the simulation run. This function will create a column for each key in the dictionary.

    :returns: A dictionary.
    """
    if agents != []:
        removenodes = list(set(list(network.nodes())) - set(agents))
        for i in removenodes:
            network.remove_node(i)

    from .OutputMeasures import ClusterFinder

    output = settings_dict

    # workaround to call the ClusterFinder method only once
    if "ClusterFinder" or "ClusterFinderList" or "Basic" or "Isolates" or "Homogeneity" in realizations:
        clusterlist = ClusterFinder.create_output(network, **kwargs)

    if "ClusterFinderList" in realizations:
        output['ClusterFinderList'] = clusterlist
    if "ClusterFinder" in realizations:
        output['ClusterFinder'] = len(clusterlist)
    if "RegionsList" in realizations:
        output['RegionsList'] = ClusterFinder.create_output(network)
    if any([i in realizations for i in ["Regions", "Basic"]]):
        output['Regions'] = len(ClusterFinder.create_output(network))
    if "ZonesList" in realizations:
        output['ZonesList'] = ClusterFinder.create_output(network, strict_zones=True)
    if any([i in realizations for i in ["Zones", "Basic"]]):
        output['Zones'] = len(ClusterFinder.create_output(network, strict_zones=True))
    if "Isolates" in realizations:
        output['Isolates'] = clusterlist.count(1)
    if any([i in realizations for i in ["Homogeneity", "Basic"]]):
        output['Homogeneity'] = clusterlist[0] / len(network.nodes())
    if any([i in realizations for i in ["AverageDistance", "Basic"]]):
        output['AverageDistance'] = sum(nx.get_edge_attributes(network, 'dist').values()) / len(network.edges())
    if any([i in realizations for i in ["AverageOpinion", "Basic"]]):
        opinionfeatures = kwargs.get("AverageOpinionFeatures", ['f01'])
        for i in opinionfeatures:
            output['AverageOpinion'] = sum(nx.get_node_attributes(network, i).values()) / len(network.edges())

    if tickwise_output:
        for f in tickwise_output.keys():
            output['Tickwise_' + str(f)] = tickwise_output[f]

    if colnames != []:
        for i in colnames:
            output[i] = output.pop(realizations[colnames.index(i)])

    return output