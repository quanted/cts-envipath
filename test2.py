import requests
import json
import time
from enviPath_python.enviPath import *
from enviPath_python.objects import *
from envipath_tree.tree import Tree


def test():

    INSTANCE_HOST = 'https://envipath.org/'
    eP = enviPath(INSTANCE_HOST)
    smiles = 'c1ccccc1'
    p = Package(eP.requester,id='https://envipath.org/package/650babc9-9d68-4b73-9332-11972ca26f7b')
    #setting = Setting.create(eP, name='ctsd3n128',
    #                depth_limit=3, node_limit=128,
    #                packages=[p])
    setting_id = INSTANCE_HOST + 'setting/' + 'bf06f794-b04a-48af-8c0f-f94a59fd235d'
    setting = Setting(eP.requester, id=setting_id)

    pw = p.predict(smiles, name='Pathway via REST', description='A pathway created via REST', setting=setting)

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




if __name__ == "__main__":
    test()