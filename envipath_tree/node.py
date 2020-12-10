import json

class Node:

    def __init__(self, node_num, node=None):
        self.smiles = ""
        self.gen = None
        self.genKey = None
        self.type = None
        self.node_num = node_num                
        self.link_desc = None

        #Root node won't have reaction rules or likelihood
        self.rule = None
        self.rule_url = None
        self.likelihood = None

        self.metabolites = list()                    

        #EnviPath node values
        self.atomCount = None
        self.depth = None
        self.dt50s = None
        self.id = None
        self.idcomp = None
        self.idreact = None
        self.image = None
        self.imageSize = None
        self.name = None
        self.proposed = None
        self.smiles = None

        if node is not None:
            self.set_node_values(node)

    def set_node_values(self, node):

        try:
            if (node is not None):
                if "depth" in node:
                    self.depth = node["depth"]
                if "atomCount" in node:
                    self.atomCount = node["atomCount"]
                if "dt50s" in node:
                    self.dt50s = node["dt50s"]
                if "id" in node:
                    self.id = node["id"]
                if "idcomp" in node:
                    self.idcomp = node["idcomp"]
                if "idreact" in node:
                    self.idreact = node["idreact"]
                if "image" in node:
                    self.image = node["image"]
                if "imageSize" in node:
                    self.imageSize = node["imageSize"]
                if "name" in node:
                    self.name = node["name"]
                if "proposed" in node:
                    self.proposed = node["proposed"]
                if "pseudo" in node:
                    self.pseudo = node["pseudo"]
                if "smiles" in node:
                    self.smiles = node["smiles"]

        except Exception as e:
            print("Error: " + str(e))
            print("Error: " + repr(e))

        finally:
            print("Done")

    def __str__(self, level=0):
        ret = "\t"*level+repr(self.smiles)+"\n"
        for child in self.metabolites:
            ret += child.__str__(level+1)
        return ret

    def __repr__(self):
        return '<tree node representation>'

