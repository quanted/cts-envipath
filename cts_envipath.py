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
        #Package: EAWAG-BBD
        self.package_id = INSTANCE_HOST + 'package/' + '650babc9-9d68-4b73-9332-11972ca26f7b'
        self.settings = dict()
        self.settings["ctsd1n16"] = INSTANCE_HOST + 'setting/' + 'bf06f794-b04a-48af-8c0f-f94a59fd235d'
        self.settings["ctsd1n32"] = INSTANCE_HOST + 'setting/' + '05532922-1274-4752-a579-bf36d0b72b12'
        self.settings["ctsd2n16"] = INSTANCE_HOST + 'setting/' + '945a3d6e-52bf-4475-bede-5bf81fe8bbc3'
        self.settings["ctsd2n32"] = INSTANCE_HOST + 'setting/' + 'd0300ae9-f642-40f9-b72f-ba6a6466b596'
        self.settings["ctsd2n64"] = INSTANCE_HOST + 'setting/' + 'a22b1109-fcdb-4d9e-a6af-744a5cd83044'
        self.settings["ctsd3n32"] = INSTANCE_HOST + 'setting/' + 'e2d40d60-9c61-4808-af2d-03f02cdd0c61'
        self.settings["ctsd3n64"] = INSTANCE_HOST + 'setting/' + '706da657-3b6b-47de-9cb8-dfe2c0b48a3b'
        self.settings["ctsd3n128"] = INSTANCE_HOST + 'setting/' + 'b3c4ddca-053d-4c2c-8dfc-42e1a5d89e4d'


    def get_envipath_tree(self, smiles):
        try:

            ep = enviPath(INSTANCE_HOST)

            setting_id = self.settings["ctsd2n32"]
            setting = Setting(ep.requester, id=setting_id)

            # Create package object
            p = Package(ep.requester, id=self.package_id)
            print("calling predict")
            pw = p.predict(smiles, name='Pathway via REST', description='A pathway created via REST', setting=setting)
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
    