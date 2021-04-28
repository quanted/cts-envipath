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
        #Package: Anonymous
        self.package_id = INSTANCE_HOST + 'package/' + '650babc9-9d68-4b73-9332-11972ca26f7b'

        self.settings = dict()
        self.settings["cts-d1-n16"] = INSTANCE_HOST + 'setting/' + 'e24258e2-f426-41c2-bdbb-b658c41e60c1'
        self.settings["cts-d1-n32"] = INSTANCE_HOST + 'setting/' + 'd243e2c0-d40f-4601-a8c0-103e563f4a89'
        self.settings["cts-d2-n16"] = INSTANCE_HOST + 'setting/' + '709fe0e0-43d7-4a70-a426-402fea69e7ee'
        self.settings["cts-d2-n32"] = INSTANCE_HOST + 'setting/' + '91017264-5132-4abb-aa03-885f127bf526'
        self.settings["cts-d2-n64"] = INSTANCE_HOST + 'setting/' + 'fa7cee2e-a6af-4023-986c-afeff46ec940'
        self.settings["cts-d3-n16"] = INSTANCE_HOST + 'setting/' + '1931a08d-9f2f-4d50-a4e9-c9370c44dbbd'
        self.settings["cts-d3-n32"] = INSTANCE_HOST + 'setting/' + '17970a8f-aafc-499a-aa16-50904c682276'
        self.settings["cts-d3-n64"] = INSTANCE_HOST + 'setting/' + 'b84c521c-a9cf-4f91-8eff-fd990edc4c34'
        self.settings["cts-d3-n128"] = INSTANCE_HOST + 'setting/' + '069ecbcf-1eb7-4ea5-8e53-08df41e6a871'


    def get_envipath_tree(self, smiles, setting_id):
        try:

            ep = enviPath(INSTANCE_HOST)
            ep.login('kurtw555', '9Gr0uper0')

            # Get package object
            p = ep.get_package(self.package_id)
            print("calling predict")
            setting_url = self.settings[setting_id]
            setting = Setting(ep.requester, id=setting_url)
            #setting = ep.get_setting(self.settings[setting_id])
            pw = p.predict(smiles, name='Pathway via REST', setting=setting, description='A pathway created via REST')
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
            print("NumNode: " + str(len(nodes)))
            print("NumLinks: " + str(len(links)))

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
    setting_id = 'cts-d3-n64'
    return_val = ctsenvipath.get_envipath_tree(smiles, setting_id)
    