import json

class Link:

    def __init__(self, link=None):
        self.base_url = 'http://umbbd.ethz.ch/servlets/rule.jsp?rule='
        
        self.rule_url = None
        self.likelihood = None
        self.rule_description = None

        #These values come from the passed in link object
        self.rule = None
        self.id = None
        self.idreaction = None
        self.multistep = None
        self.name = None
        self.pseudo = None
        self.scenarios = None
        self.source = None
        self.target = None

        if link is not None:
            self.set_link_values(link)

    def set_link_values(self, link):
        if link is not None:
            if "id" in link:
                self.id = link["id"]
            if "idreaction" in link:
                self.idreaction = link["idreaction"]
            if "multistep" in link:
                self.multistep = link["multistep"]
            if "name" in link:
                self.name = link["name"]
            if "pseudo" in link:
                self.pseudo = link["pseudo"]
            if "rule" in link:
                self.rule = link["rule"]
            if "scenarios" in link:
                self.scenarios = link["scenarios"]
            if "source" in link:
                self.source = link["source"]
            if "target" in link:
                self.target = link["target"]

            #self.get_rule()

    def get_rule(self):
        if self.name is not None:
            tokens = self.name.split(' ')
            self.rule = tokens[-1] #Eawag's BBD rule number, in form of "btXXXX"
            self.rule_url = self.base_url + self.rule

    def set_reaction_info(self, df_paths):
        #Not much we can do in this case
        if (self.rule is None) or (df_paths is None):
            return

        self.likelihood = df_paths.loc[self.rule]['Likelihood'] #Rule likelihood
        self.rule_description = df_paths.loc[self.rule]['Description'] #Rule description
        self.rule_url = self.base_url + self.rule  #Rule url
