import json
import time
import logging
import pandas as pd
import requests
from pprint import pprint
from enviPath_python.enviPath import *
from enviPath_python.objects import *
from envipath_tree.tree import Tree

# Define the instance to use
INSTANCE_HOST = 'https://envipath.org/'

class CTSEnvipath:
    def __init__(self):
        #We can pass this in or read from file if needed
        self.package_id = INSTANCE_HOST + 'package/' + '650babc9-9d68-4b73-9332-11972ca26f7b'

    def get_envipath_tree(self, smiles):
        try:

            ep = enviPath(INSTANCE_HOST)

            # Create package object
            p = Package(ep.requester, id=self.package_id)
            print("calling predict")
            pw = p.predict(smiles, name='Pathway via REST', description='A pathway created via REST')
            print("finished calling predict")

            json_retval = pw.get_json()
            idx = 0
            # Loop until completed flag switches
            while json_retval['completed'] == 'false':
                # Sleep for 10 seconds
                idx = idx + 1
                print("step: " + str(idx))
                time.sleep(10)
                json_retval = pw.get_json()                
            
            nodes = json_retval['nodes']
            links = json_retval['links']

            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            for link in links:
                if link['pseudo'] == False:
                    idreaction = link['idreaction']
                    response = requests.get(idreaction, headers=headers)
                    reaction = response.text
                                    
                    reaction = response.json()
                    rules = reaction['rules']
                    rule = rules[0]['name']
                    link["rule"] = rule         
                    #with open("link" + ".json", "w") as text_file:
                    #    text_file.write(json.dumps(link)) 

            retval = json.dumps(json_retval)
            envipath_data = retval.replace("'", '"')
            #pprint(envipath_data)

            #with open(smiles + ".json", "w") as text_file:
            #    text_file.write(retval)

            # Load dataframe of eawag rules called "paths"
            df_paths = pd.read_pickle('paths.pkl')

            cts_envipath_tree = Tree(nodes, links, df_paths)
            cts_envipath_tree.build_tree()

            return_val = json.dumps(cts_envipath_tree.root_node, default=lambda o: o.__dict__)
            

        except Exception as e:
            msg = e.args[0]
            logging.warning(msg)
            err_msg = {"error" : msg}
            return_val = json.dumps(err_msg)

        finally:
            return return_val
        
if __name__ == "__main__":

    smiles = 'c1ccccc1'
    ctsenvipath = CTSEnvipath()
    return_val = ctsenvipath.get_envipath_tree(smiles)
    