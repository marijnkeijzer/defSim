import networkx as nx
import numpy as np
from typing import List
import itertools as it

from defSim.network_evolution_sim import network_evolution_sim
from defSim.agents_init import agents_init
from defSim.influence_sim import influence_sim
from defSim.neighbor_selector_sim import neighbor_selector_sim
from defSim.focal_agent_sim import focal_agent_sim
from defSim.dissimilarity_component import dissimilarity_calculator
from defSim.network_init import network_init
from defSim.Simulation import Simulation
import multiprocessing as mp
import random
import pandas as pd
import time
import os
import pickle
from defSim.tools import ClusterExecutionScript
import shutil


class Experiment:
    """
    The main class for creating and running experiments. Each simulation consists of 7 modular components, where
    each component is independent from the others and can thus be replaced by a different implementation of that
    component.
    These components are:

    The network structure - Can either be loaded from empirical data or initialized with the NetworkGenerator.

    The AttributesInitializer - This component initializes the attributes of each agent in the network and can also be used to add attributes during the simulation.

    The FocalAgentSelector - Each simulation step, this component picks an agent from the network, either randomly or based on their characteristics.

    The neighborhoodSelector - Selects a subset of the agents in the network based on the focal agent given by the FocalAgentSelector

    The InfluenceFunction - Determines how the selected agent and the selected neighborhood influence each other.

    The NetworkModifier - Changes the structure of the network during the simulation.

    The DissimilarityCalculator - Determines how the dissimilarity/distance between two agents is calculated

    These components have different concrete implementations that might take specific parameters that are passed as a
    dictionary. In these dictionaries, the keys are the names of the parameters and the values their respective value.
    It is also possible to pass a list of values as the dictionary value, which then creates a simulation for each value,
    making it possible to easily compare simulation runs with e.g. different number of agents.

    Args:
        network(nx.Graph, np.array or String): This is either a preloaded networkx graph, an adjacency matrix as a numpy array, or the full path to a file with and edge list.
        communication_regime (List or String = "one-to-one"): Options are "one-to-one", "one-to-many" and "many-to-one". For this parameter, it is possible to pass a list of multiple of these options.
        topology (String = "grid"): Options are "grid", "ring" and "spatial_random_graph".
        network_parameters (dict = {}): This dictionary should contain all optional parameters for creating the network structure. Refer to the specific documentation of the network types to see what can be modified.
        attributes_initializer (String = "random_categorical" or :class:`AttributesInitializer`): Either be a custom AttributesInitializer or a string that selects from the predefined choices: ["random_categorical", "random_continuous"...]
        attribute_parameters (dict = {}): Optional dictionary that includes the name of attributes you want to set and a list of possible values for each.
        focal_agent_selector (str = "random" or :class:`FocalAgentSelector`): Either a custom FocalAgentSelector or a string that selects from the predefined options ["random", ...]
        focal_agent_parameters (dict = {}): Optional dictionary that includes the parameters for the FocalAgentSelector.
        neighbor_selector (str = "random" or :class:`NeighborSelector`): Either a custom NeighborSelector or a string that selects from the predefined options ["random", "similar", ...}
        neighbor_parameters (dict = {}): Optional dictionary that includes the parameters for the NeighborSelector.
        influence_function (str = "axelrod" or :class:`InfluenceOperator`): Either a custom influence function or a string that selects from the predefined options ["axelrod", "bounded_confidence", "weighted_linear", ...}
        influence_parameters (dict = {}): Optional dictionary that includes the parameters for the InfluenceFunction.
        influenceable_attributes (list = []): With this list you select all attributes that are allowed to be changed by the influence function. If the list is empty, all attributes are affected by influence.
        network_modifier: (String = "random" or :class:`NetworkModifier`) Either a custom NetworkModifier or a string selecting from the predefined options ["random", ...]
        dissimilarity_measure (String = "hamming" or :class:`DissimilarityCalculator`): Either a custom DissimilarityCalculator or a string that selects from the predefined options ["hamming", "euclidean", ...}
        tickwise (List = []): A list containing the names of all agent attributes that should be recorded at every timestep.
        stop_condition (String = "pragmatic_convergence"): Determines at what point a simulation is supposed to stop. Options include "strict_convergence", which means that it is theoretically not possible anymore for any agent to influence another, "pragmatic_convergence", which means that it is assumed that little change is possible anymore, and "max_iteration" which just stops the simulation after a certain amount of time steps.
        stop_condition_parameters (dict = {}): This dictionary should contain all optional parameters that influence how convergence is determined.
        max_iterations (int = 100000): The maximum number of iterations a Simulation should run.
        output_parameters (dict = {}): This dictionary should contain all optional parameters that influence the generated output.
        repetitions (int = 1): How often each simulation should be repeated.
        seed (int = random.randint(10000, 99999)): Optionally set seed for replicability.
    """

    def __init__(self,
                 network: nx.Graph or np.array or str = None,
                 communication_regime: List or str = "one-to-one",
                 topology: str = "grid",
                 network_parameters: dict = {},
                 attributes_initializer: str = "random_categorical" or agents_init.AttributesInitializer,
                 attribute_parameters: dict = {},
                 focal_agent_selector: str = "random" or focal_agent_sim.FocalAgentSelector,
                 focal_agent_parameters: dict = {},
                 neighbor_selector: str = "random" or neighbor_selector_sim.NeighborSelector,
                 neighbor_parameters: dict = {},
                 influence_function: str = "axelrod" or influence_sim.InfluenceOperator,
                 influence_parameters: dict = {},
                 influenceable_attributes: list = None,  # the list that is passed to the influence function
                 network_modifier: str = "random" or network_evolution_sim.NetworkModifier,
                 network_modifier_parameters: dict = {},
                 dissimilarity_measure: str = "hamming" or dissimilarity_calculator,
                 tickwise: List = [],
                 stop_condition: str = "max_iteration",
                 stop_condition_parameters: dict = {},
                 max_iterations: int = 100000,
                 output_parameters: dict = {},
                 repetitions: int = 1,
                 seed: int = random.randint(10000, 99999)):
        self.network = network
        self.communication_regime = {"communication_regime": communication_regime}
        self.topology = topology
        self.network_parameters = network_parameters
        self.attributes_initializer = attributes_initializer
        self.attribute_parameters = attribute_parameters
        self.focal_agent_selector = focal_agent_selector
        self.focal_agent_parameters = focal_agent_parameters
        self.neighbor_selector = neighbor_selector
        self.neighbor_parameters = neighbor_parameters
        self.influence_function = influence_function
        self.influence_parameters = influence_parameters
        self.influencable_attributes = influenceable_attributes
        self.network_modifier = "random"  # todo: implement a dummy network modifier
        self.network_modifier_parameters = network_modifier_parameters
        self.dissimilarity_measure = dissimilarity_measure
        self.tickwise = tickwise
        self.stop_condition = stop_condition
        self.stop_condition_parameters = stop_condition_parameters
        self.max_iterations = max_iterations
        self.output_parameters = output_parameters
        self.repetitions = repetitions
        self.seed = seed
        self.parameter_dict_list = []  # this is the internal dictionary that is created by permuting all parameters
        random.seed(self.seed)

    def estimate_runtime(self):
        """
        This function creates the parameterDictList if that hasn't happened already and then infers from its
        length the runtime of the whole experiment.

        :returns: estimated time of simulation in seconds
        """

        #todo: obviously the implementation in the current state is a joke. Put something proper in here.
        if len(self.parameter_dict_list) == 0:
            self.parameter_dict_list = self._create_parameter_dictionaries()

        num_simulations = len(self.parameter_dict_list)
        assumed_time_per_simulation = 8
        return num_simulations * assumed_time_per_simulation

    def return_values(self):
        """
        This method returns the values stored in the Experiment object. Both default, and user-specified values are
        returned to the console to make the Experiment object more transparent.

        :return: True
        """
        print("\nParameter values used in the experiment object:\n")

        for i in self.__dict__.keys():
            if type(self.__dict__[i]) == dict:
                print(i + " (dict) {")
                for key, val in self.__dict__[i].items():
                    print("  " + str(key))
                    print("  =  " + str(val))
                print("}")
            else:
                print(i)
                print("=  " + str(self.__dict__[i]))

        return True

    def run(self, parallel: bool = False, num_cores=mp.cpu_count()) -> pd.DataFrame:
        """
        Starts the experiment by first creating the parameter_dict_list if that hasn't happened already and then
        creates a simulation for each parameter combination in the parameter_dict_list.
        If parallel is true, the simulations are run on multiple cores on the machine, their number determined by num_cores.

        :param parallel: Boolean that determines in which mode the simulations will run.
        :param num_cores: Determines the number of cores in the machine that will be utilized for the execution.
        :returns: A dataframe that contains one row per Simulation.

        """
        if not isinstance(self.network, nx.Graph) and self.network is not None:
            self.network = network_init.read_network(self.network)
            # not implemented yet

        # since the creation of the grid network takes awfully long, we don't want to create that in each
        # simulation
        # todo: refactor, cause this won't work if the parameters of the network are variables
        # if self.topology == "grid":
        #    self.network = NetworkBuilder.generate_network("grid", **self.network_parameters)

        if len(self.parameter_dict_list) == 0:
            self.parameter_dict_list = self._create_parameter_dictionaries()
        print("%d different parameter combinations" % len(self.parameter_dict_list))
        if parallel:
            pool = mp.Pool(num_cores)
            results = pool.map_async(self._create_and_run_simulation, self.parameter_dict_list)
            pool.close()
            while 1:
                if results.ready():
                    break
                remaining = results._number_left
                print("Waiting for", remaining, "tasks to complete...")
                time.sleep(2)
            pool.join()
            return pd.concat(results.get())
        else:   # if NOT parallel
            result_list = [self._create_and_run_simulation(parameter_dict) for parameter_dict in
                           self.parameter_dict_list]
            return pd.concat(result_list).reset_index()

    def run_on_cluster(self,
                       chunk_size: int = 2400,
                       batch_path: str = "batchscripts",
                       output_path: str = "output",
                       walltime: str = "30:00",
                       partition: str = "short"):
        """
        This method can be used to execute large Experiments on a SLURM cluster.
        It creates a number of sbatch scripts that are immediatly executed to send jobs to the SLURM job manager.
        To be able to use this method the script with the Experiment must be executed on a SLURM server.

        :param chunk_size: Determines how many Simulations should run per node in the cluster.
        :param batch_path: The path to the folder where the batchscripts will be created. If the folder not exists yet, it will be created.
        :param output_path: The path to the folder where the output will be saved. If the folder not exists yet, it will be created.
        :param walltime: The expected time one node maximally needs for computing its chunk of simulations.
        :param partition: If the SLURM cluster has multiple partitions, it can be decided where to run the jobs with this parameter.
        """
        if not isinstance(self.network, nx.Graph) and self.network is not None:
            self.network = network_init.read_network(self.network)
            # not implemented yet

        if len(self.parameter_dict_list) == 0:
            self.parameter_dict_list = self._create_parameter_dictionaries()
        print("%d different parameter combinations" % len(self.parameter_dict_list))
        random.shuffle(self.parameter_dict_list)
        datachunks = [self.parameter_dict_list[x:x + chunk_size] for x in
                      range(0, len(self.parameter_dict_list), chunk_size)]

        if not os.path.exists(batch_path):
            os.mkdir(batch_path)
        if not os.path.exists("pickles"):
            os.mkdir("pickles")
        if not os.path.exists(output_path):
            os.mkdir(output_path)
        for i, chunk in enumerate(datachunks):
            meta_parameter_dict = {
                "network": self.network,
                "topology": self.topology,
                "initialization": self.attributes_initializer,
                "focal_agent_selector": self.focal_agent_selector,
                "neighbor_selector": self.neighbor_selector,
                "influence_function": self.influence_function,
                "influencable_attributes": self.influencable_attributes,
                "network_modifier": self.network_modifier,
                "dissimilarity_measure": self.dissimilarity_measure,
                "stop_condition": self.stop_condition,
                "max_iterations": self.max_iterations,
                "parameter_dicts": chunk
            }
            with open(os.path.join("pickles", "chunk%d.p" % i), "wb") as parameterFile:
                pickle.dump(meta_parameter_dict, parameterFile)
            batchfile_path = os.path.join(batch_path, "batch_%d.sh" % i)
            with open(batchfile_path, "w") as fh:
                fh.writelines("#!/bin/bash\n")
                fh.writelines("#SBATCH --job-name=simulation_chunk_%d.job\n" % i)
                fh.writelines("#SBATCH --output=%s%s.txt\n" % (os.path.join(output_path, "chunk"), i))
                fh.writelines("#SBATCH --time=%s\n" % walltime)
                fh.writelines("#SBATCH --mem=8000\n")
                fh.writelines("#SBATCH --partition=%s\n" % partition)
                fh.writelines("#SBATCH --cpus-per-task=24\n")
                # todo test whether spaces in path could be a problem
                fh.writelines("python %s %d %s %s\n" % (
                    ClusterExecutionScript.__file__, i, os.path.abspath("pickles"), os.path.abspath(output_path)))
            os.system("sbatch %s" % os.path.abspath(batchfile_path))
            print("script created at %s" % os.path.abspath(batchfile_path))
        #todo: this cannot work, can it? Only when the simulations are actually executed, they need access to the files
        # time.sleep(1)  # probably unncessary, but I don't want to delete the folder to quickly
        # shutil.rmtree("pickles")

    def _create_and_run_simulation(self, parameter_dict):
        simulation = Simulation(network=self.network.copy() if self.network is not None else self.network,
                                topology=self.topology,
                                attributes_initializer=self.attributes_initializer,
                                focal_agent_selector=self.focal_agent_selector,
                                neighbor_selector=self.neighbor_selector,
                                influence_function=self.influence_function,
                                influenceable_attributes= self.influencable_attributes,
                                stop_condition=self.stop_condition,
                                max_iterations=self.max_iterations,
                                communication_regime=parameter_dict["communication_regime"],
                                parameter_dict=parameter_dict,
                                dissimilarity_measure=self.dissimilarity_measure,
                                tickwise=self.tickwise,
                                seed=random.randint(10000, 99999)
                                )
        return simulation.run_simulation()

    def _create_parameter_dictionaries(self) -> List[dict]:
        """
        creates from a set of dictionaries that might contain lists as values another set of dictionaries that
        contain all possible combinations of values for each key.

        """
        dictionaries = [self.network_parameters,
                        self.attribute_parameters,
                        self.communication_regime,
                        self.stop_condition_parameters,
                        self.focal_agent_parameters,
                        self.neighbor_parameters,
                        self.network_modifier_parameters,
                        self.influence_parameters]

        combined_dict = {}
        for dict in dictionaries:
            combined_dict.update(dict)  # first merge all dictionaries
        # then single parameters that are not submitted as a list have to be wrapped in a list
        wrapped_dict_values = [[value] if type(value) is not list else value for value in combined_dict.values()]
        # get the cartesian product (all permutations) of all values
        combinations = it.product(*wrapped_dict_values)
        full_dict_list = []  # this will be the output list of dictionaries
        # create a new dictionary for each of these combinations
        for values in combinations:
            new_dict = {}
            keys = list(combined_dict.keys())
            key_value_pairs = [{keys[i]: values[i]} for i in range(len(values))]
            for pair in key_value_pairs:
                new_dict.update(pair)
            full_dict_list.append(new_dict)  # and add the dictionary to the list of all dictionaries
        # now we want to repeat each parameter combination as often as the number of repetitions
        return list(it.chain.from_iterable(it.repeat(x, self.repetitions) for x in full_dict_list))
