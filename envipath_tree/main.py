import json
import copy
import pandas as pd
from tree import Tree


if __name__ == "__main__":
    # execute only if run as a script
    with open('output.json') as json_file:
        json_data = json.load(json_file)

    links = json_data["links"]
    nodes = json_data["nodes"]

    # Load dataframe of eawag rules called "paths"
    df_paths = pd.read_pickle('paths.pkl')

    tree = Tree(nodes, links, df_paths)
    tree.build_tree()
    print(tree.root_node)