import json
import copy
from typing import List
from typing import TypeVar
from .node import Node
from .link import Link

#PandasDataFrame = TypeVar('pandas.core.frame.DataFrame')

class Tree:

    #def __init__(self, nodes: List[Node], links: List[Link], pd):
    def __init__(self, nodes, links, df_paths):
        self.nodes = list()
        self.links = list()
        self.df_paths = df_paths
        self.max_depth = 0
        self.root_node = None
        self.build_node_list(nodes)
        self.build_link_list(links)

    #Build list of nodes, find max depth, set root node
    def build_node_list(self, nodes):
        for idx in range(len(nodes)):
            node = Node(idx, nodes[idx])
            self.nodes.append(node)
            if node.depth > self.max_depth:
                self.max_depth = node.depth
            if node.depth == 0:
                self.root_node = node


    def build_link_list(self, links):
        for idx in range(len(links)):
            link = Link(links[idx])
            #rules = reaction['rules']
            #rule = rules[0]['name']
            #link.rule = rule       
            link.set_reaction_info(self.df_paths)
            self.links.append(link)

    def find_source_links(self, node_num):
        lst_source = list()
        for link in self.links:
            if link.source == node_num:
                lst_source.append(link)

        return lst_source

    def find_target_links(self, source_num, target_num):
        lst_target = list()
        for link in self.links:
            if link.source == source_num and link.target == target_num:
                lst_target.append(copy.deepcopy(link))
        return lst_target

    def build_tree(self):
        self.recurse_nodes(self.root_node)

    #recursive function to build metabolite tree
    def recurse_nodes(self, node):
        lst_child_nodes = list()
        source_links = self.find_source_links(node.node_num) 

        #This should be a terminal node - should not be a pseudo node
        if len(source_links) == 0:
            return lst_child_nodes

        for link in source_links:
            #Get the target of the pseudo link
            if link.pseudo == True:
                target_links = self.find_source_links(link.target)
                for target_link in target_links:
                    pseudo_target_links = self.find_target_links(target_link.source, target_link.target)  
                    for pseudo_target_link in pseudo_target_links:
                        lst_child_nodes.append(copy.deepcopy(self.nodes[pseudo_target_link.target]))
            else:
                target_links = self.find_target_links(link.source, link.target)
                for target_link in target_links:
                        lst_child_nodes.append(copy.deepcopy(self.nodes[target_link.target]))

        for child_node in lst_child_nodes:            
            self.recurse_nodes(child_node)
            
        node.metabolites.extend(lst_child_nodes)    
                  
        return lst_child_nodes

    

#recursive function to build metabolite tree
    def recurse_nodes2(self, node):
        lst_child_nodes = list()
        source_links = self.find_source_links(node.node_num)
        #target_links = self.find_target_links(node.node_num)

        #This should be a terminal node - should not be a pseudo node
        if len(source_links) == 0:
            lst_child_nodes.append(node)
            return lst_child_nodes
        
        for link in source_links:
            #have to deal with these pseudo links                         
            lst_child_nodes = self.recurse_nodes(self.nodes[link.target])
            for child_node in lst_child_nodes:                
                node.metabolites.append(child_node)                        
            
        return lst_child_nodes

        








