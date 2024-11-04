from enviPath_python.enviPath import enviPath
from enviPath_python.objects import Pathway
from enviPath_python.objects import Setting
from envipath_tree.tree import Tree
import json
import time
import logging
import pandas as pd
import requests
import os
from pprint import pprint


class CTSEnvipath:
    def __init__(self):
        self.INSTANCE_HOST = 'https://envipath.org/'

    def get_envipath_tree(self, smiles, gen_limit=None):
        # try:
        # #These are for the enviPath user account
        # username = os.environ['USERNAME']
        # pwd = os.environ['PASSWORD']
        
        eP = enviPath(self.INSTANCE_HOST)

        eP.login(os.getenv("CTS_ENVIPATH_USERNAME"), os.getenv("CTS_ENVIPATH_PASSWORD"))
        
        # obtain the currently logged in user
        me = eP.who_am_i()

        pkg_bbd = eP.get_package('https://envipath.org/package/32de3cf4-e3e6-4168-956e-32fa5ddb0ce1')
        pkg_sludge = eP.get_package('https://envipath.org/package/7932e576-03c7-4106-819d-fe80dc605b8a')
        pkg_soil = eP.get_package('https://envipath.org/package/5882df9c-dae1-4d80-a40e-db4724271456')

        packages = [pkg_bbd, pkg_sludge, pkg_soil]
        setting = Setting.create(eP, packages=packages, name='cts')

        # get the package the pathway should be stored in
        pkg = me.get_default_package()

        # will trigger the pathway prediction
        # pw = Pathway.create(pkg_bbd, smiles=smiles, setting=setting)
        pw = Pathway.create(pkg, smiles=smiles, setting=setting)


        #pw = pkg_bbd.predict('c1ccccc1')
        #pw = Pathway.create(pkg_bbd, smiles='c1ccccc1')


        # wait until the prediction finished
        while pw.is_running():
            print("Sleeping for three secs...")
            time.sleep(3)

        # check result
        if pw.has_failed():
            raise Exception("enviPath prediction failed")
        
        json_retval = pw.get_json()
        nodes = json_retval['nodes']
        links = json_retval['links']

        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        for link in links:
            if link['pseudo'] == False:
                idreaction = link['idreaction']

                # Method 1: Original way to set link rules.
                # NOTE: Returning 401 (10/30/24)
                # response = requests.get(idreaction, headers=headers)
                # reaction = response.text                                
                # reaction = response.json()
                # print("Reaction: {}".format(reaction))
                # rules = reaction['rules']
                # rule = rules[0]['name']
                # link["rule"] = rule         

                # Method 2: New atttempt at setting link rules. Throwing KeyError in pandas.
                # reaction = eP.get_reaction(idreaction)
                # link["rule"] = reaction.name

                # Method 3: Not setting the link rules returns a tree but is probably
                # missing info (like the rule/reaction/pathway names).

                retval = json.dumps(json_retval)
                envipath_data = retval.replace("'", '"')

                # Load dataframe of eawag rules called "paths"
                df_paths = pd.read_pickle('paths.pkl')

                cts_envipath_tree = Tree(nodes, links, df_paths)
                cts_envipath_tree.build_tree()

                return_val = json.dumps(cts_envipath_tree.root_node, default=lambda o: o.__dict__)
                    
        return return_val

        # except Exception as e:
        #     msg = e.args[0]
        #     logging.warning(msg)
        #     err_msg = {"error" : msg}
        #     return_val = json.dumps(err_msg)

        # finally:
        #     return return_val
    
if __name__ == "__main__":
        
    smiles = 'c1ccccc1'
    ctsenvipath = CTSEnvipath()
    #setting_id = 'cts-d3-n64'
    return_val = ctsenvipath.get_envipath_tree(smiles, )

    print("Tree structure: {}".format(return_val))