# Copyright 2020 enviPath UG & Co. KG
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import json
from abc import ABC, abstractmethod
from collections import namedtuple
from io import BytesIO
from typing import List, Optional, Union
from enviPath_python.enums import Endpoint, ClassifierType, FingerprinterType, AssociationType, EvaluationType, \
    Permission


class enviPathObject(ABC):
    """
    Base class for an enviPath object.
    """

    def __init__(self, requester, *args, **kwargs):
        """
        Constructor for any instance derived from enviPathObject.
        :param requester: The enviPathRequester used for getting this object.
        :param args: additional positional arguments.
        :param kwargs: additional named arguments. 'name' and 'id' are mandatory.
        """
        self.requester = requester
        # Make name optional to allow object creation with id only
        if 'name' in kwargs:
            self.name = kwargs['name']
        self.id = kwargs['id']
        self.loaded = False

    def get_type(self):
        """
        Gets the class name as string.
        :return: The class name as string. E.g. 'Package'
        """
        return type(self).__name__

    def __str__(self):
        """
        Simple string representation including type, name and id.
        :return: The object as string.
        """
        return '{}: {} ({})'.format(self.get_type(), self.get_name(), self.id)

    def __repr__(self):
        """
        Same as __str__.
        :return: same as __str__.
        """
        return str(self)

    def _get(self, field):
        """
        Tries to get a field of the object. As objects are only initialized with 'name' and 'id' all other
        fields must be fetched from the enviPath instance. This fetches data only once.
        If the field is missing after getting the data from the enviPath instance an exception is risen.
        Should only be called by 'public' functions as they should implement appropriate object creation if value
        of requested field is an enviPathObject instance again.
        :param field: The field of interest.
        :return: The value of the field.
        """
        if not self.loaded and not hasattr(self, field):
            obj_fields = self._load()
            for k, v in obj_fields.items():
                setattr(self, k, v)
                self.loaded = True

        if not hasattr(self, field):
            raise ValueError('{} has no property {}'.format(self.get_type(), field))

        return getattr(self, field)

    def get_id(self):
        return self.id

    def __eq__(self, other):
        if type(other) is type(self):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)

    def get_name(self):
        return self._get('name')

    def get_description(self):
        return self._get('description')

    def _load(self):
        """
        Fetches data from the enviPath instance via the enviPathRequester provided at objects creation.
        :return: json containing the server response.
        """
        res = self.requester.get_request(self.id).json()
        return res

    def get_json(self):
        """
        Returns the objects plain JSON fetched from the instance.
        :return: A JSON object returned by the API.
        """
        return self.requester.get_json(self.id)

    def _create_from_nested_json(self, member_name: str, nested_object_type):
        res = []
        plain_objs = self._get(member_name)
        for plain_obj in plain_objs:
            res.append(nested_object_type(self.requester, **plain_obj))
        return res

    def delete(self):
        """
        Deletes the object denoted by the internally maintained field `id`.
        :return:
        """
        if not hasattr(self, 'id') or self.id is None:
            raise ValueError("Unable to delete object due to missing id!")
        self.requester.delete_request(self.id)
        self.id = None
        # Removed potential cached members
        for key in self.__dict__:
            self.__delattr__(key)


class ReviewableEnviPathObject(enviPathObject, ABC):

    def get_aliases(self) -> List[str]:
        return self._get('aliases')

    def get_review_status(self) -> str:
        return self._get('reviewStatus')

    def is_reviewed(self) -> bool:
        return 'reviewed' == self.get_review_status()

    def get_scenarios(self) -> List['Scenario']:
        res = []
        plain_scenarios = self._get('scenarios')
        for plain_scenario in plain_scenarios:
            res.append(Scenario(self.requester, **plain_scenario))
        return res


class Package(enviPathObject):

    def set_description(self, desc: str) -> None:
        payload = {
            'packageDescription': (None, desc),
        }
        self.requester.post_request(self.id, files=payload)
        setattr(self, "description", desc)

    def add_compound(self, smiles: str, name: str = None, description: str = None, inchi: str = None) -> 'Compound':
        return Compound.create(self, smiles, name=name, description=description, inchi=inchi)

    def get_compounds(self) -> List['Compound']:
        """
        Gets all compounds of the package.
        :return: List of Compound objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.COMPOUND)
        return res

    def add_simple_rule(self, smirks: str, name: str = None, description: str = None,
                        reactant_filter_smarts: str = None, product_filter_smarts: str = None,
                        immediate: str = None) -> 'SimpleRule':
        return SimpleRule.create(self, smirks, name=name, description=description,
                                 reactant_filter_smarts=reactant_filter_smarts,
                                 product_filter_smarts=product_filter_smarts, immediate=immediate)

    def add_sequential_composite_rule(self, simple_rules: List['SimpleRule'], name: str = None, description: str = None,
                                      reactant_filter_smarts: str = None, product_filter_smarts: str = None,
                                      immediate: str = None) -> 'SequentialCompositeRule':
        return SequentialCompositeRule.create(self, simple_rules, name=name, description=description,
                                              reactant_filter_smarts=reactant_filter_smarts,
                                              product_filter_smarts=product_filter_smarts, immediate=immediate)

    def add_parallel_composite_rule(self, simple_rules: List['SimpleRule'], name: str = None, description: str = None,
                                    reactant_filter_smarts: str = None, product_filter_smarts: str = None,
                                    immediate: str = None) -> 'ParallelCompositeRule':
        return ParallelCompositeRule.create(self, simple_rules, name=name, description=description,
                                            reactant_filter_smarts=reactant_filter_smarts,
                                            product_filter_smarts=product_filter_smarts, immediate=immediate)

    def get_rules(self) -> List['Rule']:
        """
        Gets all rules of the package.
        :return: List of Rule objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.RULE)
        return res

    def add_reaction(self, smirks: str = None, educt: 'CompoundStructure' = None, product: 'CompoundStructure' = None,
                     name: str = None, description: str = None, rule: 'Rule' = None):
        return Reaction.create(self, smirks, educt, product, name, description, rule)

    def get_reactions(self) -> List['Reaction']:
        """
        Gets all reactions of the package.
        :return: List of Reaction objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.REACTION)
        return res

    def add_pathway(self, smiles: str, name: str = None, description: str = None,
                    root_node_only: bool = False, setting: 'Setting' = None) -> 'Pathway':
        """

        :param smiles:
        :param name:
        :param description:
        :param root_node_only:
        :param setting:
        :return:
        """
        return Pathway.create(self, smiles, name, description, root_node_only, setting)

    def predict(self, smiles: str, name: str = None, description: str = None,
                root_node_only: bool = False, setting: 'Setting' = None) -> 'Pathway':
        """
        Alias for add_pathway()
        :param smiles:
        :param name:
        :param description:
        :param root_node_only:
        :param setting:
        :return:
        """
        return self.add_pathway(smiles, name, description, root_node_only, setting)

    def get_pathways(self) -> List['Pathway']:
        """
        Gets all pathways of the package.
        :return: List of Pathway objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.PATHWAY)
        return res

    def add_relative_reasoning(self, packages: List['Package'], classifer_type: ClassifierType,
                               eval_type: EvaluationType, association_type: AssociationType,
                               evaluation_packages: List['Package'] = None,
                               fingerprinter_type: FingerprinterType = FingerprinterType.ENVIPATH_FINGERPRINTER,
                               quickbuild: bool = True, use_p_cut: bool = False, cut_off: float = 0.5,
                               evaluate_later: bool = True, name: str = None) -> 'RelativeReasoning':
        return RelativeReasoning.create(self, packages, classifer_type, eval_type, association_type,
                                        evaluation_packages=evaluation_packages, fingerprinter_type=fingerprinter_type,
                                        quickbuild=quickbuild, use_p_cut=use_p_cut, cut_off=cut_off,
                                        evaluate_later=evaluate_later, name=name)

    def get_relative_reasonings(self) -> List['RelativeReasoning']:
        """
        Gets all relative reasonings of the packages.
        :return: List of RelativeReasoning objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.RELATIVEREASONING)
        return res

    def get_scenarios(self) -> List['Scenario']:
        """
        Gets all scenarios of the package.
        :return: List of Scenario objects.
        """
        res = self.requester.get_objects(self.id + '/', Endpoint.SCENARIO)
        return res

    def export_as_json(self) -> dict:
        """
        Exports the entire package as json.
        :return: A dictionary containing all data stored in this package.
        """
        params = {
            'exportAsJson': 'true',
        }
        raw_content = self.requester.get_request(self.id, params=params, stream=True).content
        buffer = BytesIO(raw_content)
        buffer.seek(0)
        return json.loads(buffer.read().decode())

    def set_access_for_user(self, obj: Union['Group', 'User'], perm: Permission) -> None:
        payload = {
            'permissions': 'change',
            'ppsURI': obj.get_id(),
        }

        if perm == Permission.READ:
            payload['read'] = 'on'

        if perm == Permission.WRITE:
            payload['write'] = 'on'

        self.requester.post_request(self.id, payload=payload, allow_redirects=False)

    @staticmethod
    def create(ep, group: 'Group', name: str = None, description: str = None) -> 'Package':
        # TODO add type hint for ep and get rid of cyclic import
        package_payload = dict()
        package_payload['groupURI'] = group.get_id()
        if name:
            package_payload['packageName'] = name
        if description:
            package_payload['packageDescription'] = description

        url = '{}{}'.format(ep.get_base_url(), Endpoint.PACKAGE.value)
        res = ep.requester.post_request(url, payload=package_payload, allow_redirects=False)
        res.raise_for_status()
        return Package(ep.requester, id=res.headers['Location'])


class Scenario(enviPathObject):

    @staticmethod
    def create(**kwargs):
        pass


class Compound(ReviewableEnviPathObject):

    def add_structure(self, smiles, name=None, description=None, inchi=None, mol_file=None) -> 'CompoundStructure':
        return CompoundStructure.create(self, smiles, name=name, description=description, inchi=inchi,
                                        mol_file=mol_file)

    def get_structures(self) -> List['CompoundStructure']:
        """
        Gets all structures of this compound.
        :return: List of Structure objects.
        """
        res = []
        plain_structures = self._get('structures')
        for plain_structure in plain_structures:
            res.append(CompoundStructure(self.requester, **plain_structure))
        return res

    @staticmethod
    def create(parent: Package, smiles: str, name=None, description=None, inchi=None) -> 'Compound':
        if not isinstance(parent, Package):
            raise ValueError("The parent of a compound has to be a package!")

        compound_payload = dict()
        compound_payload['compoundSmiles'] = smiles
        if name:
            compound_payload['compoundName'] = name
        if description:
            compound_payload['compoundDescription'] = description
        if inchi:
            compound_payload['inchi'] = inchi

        url = '{}/{}'.format(parent.get_id(), Endpoint.COMPOUND.value)
        res = parent.requester.post_request(url, payload=compound_payload, allow_redirects=False)
        res.raise_for_status()
        return Compound(parent.requester, id=res.headers['Location'])

    def get_default_structure(self) -> 'CompoundStructure':
        for structure in self.get_structures():
            if structure.is_default_structure():
                return structure
        raise ValueError("The compound does not have a default structure!")

    def get_smiles(self) -> str:
        return self.get_default_structure().get_smiles()


class CompoundStructure(ReviewableEnviPathObject):

    def get_charge(self) -> float:
        return float(self._get('charge'))

    def get_formula(self) -> str:
        return self._get('formula')

    def get_mass(self):
        return self._get('mass')

    def get_svg(self) -> str:
        return self.requester.get_request(self._get('image')).text

    def is_default_structure(self):
        return self._get('isDefaultStructure')

    def get_smiles(self) -> str:
        return self._get('smiles')

    def get_inchi(self) -> str:
        return self._get('InChI')

    def get_pathways(self) -> List['Pathway']:
        return self._create_from_nested_json('pathways', Pathway)

    def get_reactions(self) -> List['Reaction']:
        return self._create_from_nested_json('reactions', Reaction)

    def get_halflifes(self) -> List['HalfLife']:
        res = []
        for hl in self._get('halflifes'):
            res.append(HalfLife(scenarioId=hl['scenarioId'], scenarioName=hl['scenarioName'], hl=hl['hl'],
                                hl_comment=hl['hlComment'], hl_fit=hl['hlFit'], hl_model=hl['hlModel'],
                                source=hl['source']))
        return res

    @staticmethod
    def create(parent: Compound, smiles, name=None, description=None, inchi=None, mol_file=None) -> 'CompoundStructure':
        if not isinstance(parent, Compound):
            raise ValueError("The parent of a structure has to be a compound!")

        structure_payload = dict()
        structure_payload['smiles'] = smiles
        if name:
            structure_payload['name'] = name
        if description:
            structure_payload['description'] = description
        if inchi:
            structure_payload['inchi'] = inchi
        if mol_file:
            structure_payload['molfile'] = mol_file

        url = '{}/{}'.format(parent.get_id(), Endpoint.COMPOUNDSTRUCTURE)
        res = parent.requester.post_request(url, payload=structure_payload, allow_redirects=False)
        res.raise_for_status()
        return CompoundStructure(parent.requester, id=res.headers['Location'])


class Reaction(enviPathObject):

    def is_multistep(self) -> bool:
        return "true" == self._get('multistep')

    def get_ec_numbers(self) -> List['ECNumber']:
        ec_numbers = self._get('ecNumbers')
        res = []
        for ec_number in ec_numbers:
            pathways = [Pathway(self.requester, id=pw['id']) for pw in ec_number['pathways']]
            res.append(ECNumber(ec_number['ecNumber'], ec_number['ecName'], pathways))
        return res

    def get_smirks(self) -> str:
        return self._get('smirks')

    def get_pathways(self) -> List['Pathway']:
        return self._get('pathways')

    def get_medline_references(self) -> List[object]:
        return self._get('medlineRefs')

    def get_educts(self) -> List['CompoundStructure']:
        return self._create_from_nested_json('educts', CompoundStructure)

    def get_products(self):
        return self._create_from_nested_json('products', CompoundStructure)

    def get_rule(self) -> Optional['Rule']:
        try:
            rules = self._get('rules')
            if len(rules) == 0:
                return None
            if len(rules) > 1:
                raise Exception("More than one rule attached to reaction!")
            rule_type = Rule.get_rule_type(rules[0])
            return rule_type(self.requester, **rules[0])
        except ValueError:
            return None

    @staticmethod
    def create(package: Package, smirks: str = None, educt: CompoundStructure = None, product: CompoundStructure = None,
               name: str = None, description: str = None, rule: 'Rule' = None):

        if smirks is None and (educt is None or product is None):
            raise ValueError("Neither SMIRKS or educt/product must be provided")

        if smirks is not None and (educt is not None and product is not None):
            raise ValueError("SMIRKS and educt/product provided!")

        payload = {}

        if smirks:
            payload['smirks'] = smirks
        else:
            payload['educt'] = educt.get_id()
            payload['product'] = product.get_id()

        if rule:
            payload['rule'] = rule.get_id()

        if name:
            payload['reactionName'] = name

        if description:
            payload['reactionDescription'] = description

        url = '{}/{}'.format(package.get_id(), Endpoint.REACTION.value)
        res = package.requester.post_request(url, payload=payload, allow_redirects=False)
        res.raise_for_status()
        return Reaction(package.requester, id=res.headers['Location'])


class Rule(ReviewableEnviPathObject, ABC):

    def get_ec_numbers(self) -> List[object]:
        return self._get('ecNumbers')

    def included_in_composite_rule(self) -> List['Rule']:
        res = []
        for rule in self._get('includedInCompositeRule'):
            res.append(Rule(self, requester=self.requester, id=rule['id']))
        return res

    def is_composite_rule(self) -> bool:
        return self._get('isCompositeRule')

    def get_transformations(self) -> str:
        return self._get('transformations')

    def get_reactions(self) -> List['Reaction']:
        return self._create_from_nested_json('reactions', Reaction)

    def get_pathways(self) -> List['Pathway']:
        return self._create_from_nested_json('pathways', Pathway)

    def get_reactant_filter_smarts(self) -> str:
        return self._get('reactantFilterSmarts')

    def get_reactant_smarts(self) -> str:
        return self._get('reactantsSmarts')

    def get_product_filter_smarts(self) -> str:
        return self._get('productFilterSmarts')

    def get_product_smarts(self) -> str:
        return self._get('productsSmarts')

    def apply_to_compound(self, compound: Compound) -> List[str]:
        return self.apply_to_smiles(compound.get_default_structure().get_smiles())

    def apply_to_smiles(self, smiles) -> List[str]:
        payload = {
            'hiddenMethod': 'APPLYRULES',
            'compound': smiles
        }
        res = self.requester.post_request(self.get_id(), payload=payload)
        res.raise_for_status()
        result = []
        splitted = res.text.split()
        for split in splitted:
            if split:
                result.append(split)
        return result

    @staticmethod
    def get_rule_type(obj: dict):
        if obj['identifier'] == Endpoint.SIMPLERULE.value:
            return SimpleRule
        elif obj['identifier'] == Endpoint.SEQUENTIALCOMPOSITERULE.value:
            return SequentialCompositeRule
        elif obj['identifier'] == Endpoint.PARALLELCOMPOSITERULE.value:
            return ParallelCompositeRule
        else:
            raise ValueError("Unknown rule type {}".format(obj['identifier']))

    @staticmethod
    @abstractmethod
    def create(package: Package, smirks: str, name: str = None, description: str = None,
               reactant_filter_smarts: str = None, product_filter_smarts: str = None):
        pass


class SimpleRule(Rule):

    @staticmethod
    def create(package: Package, smirks: str, name: str = None, description: str = None,
               reactant_filter_smarts: str = None, product_filter_smarts: str = None,
               immediate: str = None) -> 'SimpleRule':
        rule_payload = {
            'smirks': smirks,
        }

        if name:
            rule_payload['name'] = name

        if description:
            rule_payload['description'] = description

        if reactant_filter_smarts:
            rule_payload['reactantFilterSmarts'] = reactant_filter_smarts

        if product_filter_smarts:
            rule_payload['productFilterSmarts'] = product_filter_smarts

        if immediate:
            rule_payload['immediaterule'] = immediate

        url = '{}/{}'.format(package.get_id(), Endpoint.SIMPLERULE.value)
        res = package.requester.post_request(url, payload=rule_payload, allow_redirects=False)
        res.raise_for_status()
        return SimpleRule(package.requester, id=res.headers['Location'])

    def get_smirks(self) -> str:
        return self._get('smirks')


class SequentialCompositeRule(Rule):
    @staticmethod
    def create(package: Package, simple_rules: List[SimpleRule], name: str = None, description: str = None,
               reactant_filter_smarts: str = None, product_filter_smarts: str = None,
               immediate: str = None) -> 'SequentialCompositeRule':

        rule_payload = {
            'simpleRules[]': [r.get_id() for r in simple_rules],
        }

        if name:
            rule_payload['name'] = name

        if description:
            rule_payload['description'] = description

        if reactant_filter_smarts:
            rule_payload['reactantFilterSmarts'] = reactant_filter_smarts

        if product_filter_smarts:
            rule_payload['productFilterSmarts'] = product_filter_smarts

        if immediate:
            rule_payload['immediaterule'] = immediate

        url = '{}/{}'.format(package.get_id(), Endpoint.SEQUENTIALCOMPOSITERULE.value)
        res = package.requester.post_request(url, payload=rule_payload, allow_redirects=False)
        res.raise_for_status()
        return SequentialCompositeRule(package.requester, id=res.headers['Location'])

    def get_simple_rules(self):
        return self._create_from_nested_json('simpleRules', SimpleRule)


class ParallelCompositeRule(Rule):
    @staticmethod
    def create(package: Package, simple_rules: List[SimpleRule], name: str = None, description: str = None,
               reactant_filter_smarts: str = None, product_filter_smarts: str = None,
               immediate: str = None) -> 'ParallelCompositeRule':

        rule_payload = {
            'simpleRules[]': [r.get_id() for r in simple_rules],
        }

        if name:
            rule_payload['name'] = name

        if description:
            rule_payload['description'] = description

        if reactant_filter_smarts:
            rule_payload['reactantFilterSmarts'] = reactant_filter_smarts

        if product_filter_smarts:
            rule_payload['productFilterSmarts'] = product_filter_smarts

        if immediate:
            rule_payload['immediaterule'] = immediate

        url = '{}/{}'.format(package.get_id(), Endpoint.PARALLELCOMPOSITERULE.value)
        res = package.requester.post_request(url, payload=rule_payload, allow_redirects=False)
        res.raise_for_status()
        return ParallelCompositeRule(package.requester, id=res.headers['Location'])

    def get_simple_rules(self):
        return self._create_from_nested_json('simpleRules', SimpleRule)


class RelativeReasoning(ReviewableEnviPathObject):

    @staticmethod
    def create(package: Package, packages: List[Package], classifer_type: ClassifierType,
               eval_type: EvaluationType, association_type: AssociationType,
               evaluation_packages: List[Package] = None,
               fingerprinter_type: FingerprinterType = FingerprinterType.ENVIPATH_FINGERPRINTER,
               quickbuild: bool = True, use_p_cut: bool = False, cut_off: float = 0.5,
               evaluate_later: bool = True, name: str = None) -> 'RelativeReasoning':

        payload = {
            'fpType': fingerprinter_type.value,
            'clfType': classifer_type.value,
            'assocType': association_type.value,
            'quickBuild': 'on' if quickbuild else 'off',
            'evalLater': 'on' if evaluate_later else 'off',
            'evalType': eval_type.value,
            'packages': [p.get_id() for p in packages],
            'cut-off': cut_off,
        }

        if use_p_cut:
            payload['p-cut'] = 'on'

        if evaluation_packages:
            payload['evalPackages'] = [p.get_id() for p in evaluation_packages]

        if name:
            payload['modelName'] = name

        url = '{}/{}'.format(package.get_id(), Endpoint.RELATIVEREASONING.value)
        res = package.requester.post_request(url, payload=payload, allow_redirects=False)
        res.raise_for_status()
        return RelativeReasoning(package.requester, id=res.headers['Location'])

    def download_arff(self) -> str:
        params = {
            'downloadARFF': 'ILikeCats'
        }
        return self.requester.get_request(self.id, params=params).text

    def get_model_status(self) -> 'ModelStatus':
        params = {
            'status': "true",
        }
        return ModelStatus(**self.requester.get_request(self.id, params=params).json())

    def classify_structure(self, structure: CompoundStructure):
        return self.classify_smiles(structure.get_smiles())

    def classify_smiles(self, smiles: str):
        # TODO
        raise NotImplementedError("Not (yet) implemented!")


class Node(ReviewableEnviPathObject):

    def get_smiles(self):
        return self.get_default_structure().get_smiles()

    def get_halflifes(self) -> List['HalfLife']:
        #  TODO are they equal to HLs attached to CompoundStructure?
        res = []
        for hl in self._get('halflifes'):
            res.append(HalfLife(scenarioId=hl['scenarioId'], scenarioName=hl['scenarioName'], hl=hl['hl'],
                                hl_comment=hl['hlComment'], hl_fit=hl['hlFit'], hl_model=hl['hlModel'],
                                source=hl['source']))
        return res

    def get_proposed_values_scenarios(self) -> List['Scenario']:
        return self._create_from_nested_json('proposedValues', Scenario)

    def get_confidence_scenarios(self) -> List['Scenario']:
        return self._create_from_nested_json('confidenceScenarios', Scenario)

    def get_structures(self) -> List['CompoundStructure']:
        return self._create_from_nested_json('structures', CompoundStructure)

    def get_default_structure(self) -> CompoundStructure:
        return CompoundStructure(self.requester, id=self._get('defaultStructure')['id'])

    def get_svg(self) -> str:
        return self.get_default_structure().get_svg()

    def get_depth(self) -> int:
        return self._get('depth')

    def create(self, **kwargs):
        pass


class Edge(ReviewableEnviPathObject):

    def get_start_nodes(self) -> List['Node']:
        return self._create_from_nested_json('startNodes', Node)

    def get_end_nodes(self) -> List['Node']:
        return self._create_from_nested_json('endNodes', Node)

    def get_reaction(self) -> Reaction:
        return Reaction(self.requester, id=self._get('reactionURI'))

    def get_reaction_name(self) -> str:
        return self._get('reactionName')

    def get_ec_numbers(self) -> List['ECNumber']:
        return self.get_reaction().get_ec_numbers()

    def get_rule(self) -> Optional['Rule']:
        return self.get_reaction().get_rule()

    def create(self, **kwargs):
        pass


class Setting(enviPathObject):

    @staticmethod
    def create(ep, packages: List[Package], name: str = None, depth_limit: int = None, node_limit: int = None,
               relative_reasoning: RelativeReasoning = None, cut_off: float = 0.5,
               evaluation_type: EvaluationType = None, min_carbon: int = None,
               terminal_compounds: List[Compound] = None):

        payload = {
            'packages[]': [p.get_id() for p in packages]
        }

        if name:
            payload['settingName'] = name

        if depth_limit:
            payload['limdepth'] = "true"
            payload['depthNumber'] = depth_limit

        if node_limit:
            payload['limnode'] = "true"
            payload['nodeNumber'] = node_limit

        if min_carbon:
            payload['mincarbons'] = "true"
            payload['carbonNumber'] = min_carbon

        if relative_reasoning:
            payload['modelUri'] = relative_reasoning.get_id()
            payload['cutoff'] = cut_off
            payload['evalType'] = evaluation_type.value

        if terminal_compounds:
            payload['terminalcompounds[]'] = [c.get_id() for c in terminal_compounds]

        url = '{}{}'.format(ep.get_base_url(), Endpoint.SETTING.value)
        res = ep.requester.post_request(url, payload=payload, allow_redirects=False)
        res.raise_for_status()
        return Setting(ep.requester, id=res.headers['Location'])

    def set_name(self, name: str) -> None:
        payload = {
            'settingName': name
        }
        self.requester.post_request(self.id, payload=payload)
        setattr(self, "settingName", name)

    def get_included_packages(self) -> List['Package']:
        return self._create_from_nested_json('includedPackages', Package)

    def get_truncationstrategy(self) -> Optional['TruncationStrategy']:
        return TruncationStrategy(self.requester, self._get("truncationstrategy"))

    def add_package(self, package: 'Package'):
        return self.add_packages([package])

    def add_packages(self, packages: List['Package']):
        payload = {
            'addedPackages[]': [p.id for p in packages]
        }
        self.requester.post_request(self.id, payload=payload)
        # TODO modify local state

    def remove_package(self, package: 'Package'):
        return self.remove_packages([package])

    def remove_packages(self, packages: List['Package']):
        payload = {
            'removedPackages[]': [p.id for p in packages]
        }
        self.requester.post_request(self.id, payload=payload)
        # TODO modify local state

    def get_normalization_rules(self) -> List['NormalizationRule']:
        return self._create_from_nested_json('normalizationRules', NormalizationRule)

    def add_normalization_rule(self, smirks: str, name: str = None, description: str = None):
        NormalizationRule.create(self, smirks, name=name, description=description)
        if not smirks:
            raise ValueError("SMIRKS not set!")

        payload = {
            'smirks': smirks
        }

        if name:
            payload['ruleName'] = name

        if description:
            payload['ruleDesc'] = description

        self.requester.post_request(self.id, payload=payload)
        # TODO modify local state


class TruncationStrategy(enviPathObject):
    pass


class NormalizationRule(ReviewableEnviPathObject):

    @staticmethod
    def create(setting: 'Setting', smirks: str, name: str = None, description: str = None):
        if not smirks:
            raise ValueError("SMIRKS not set!")

        payload = {
            'smirks': smirks
        }

        if name:
            payload['ruleName'] = name

        if description:
            payload['ruleDesc'] = description

        setting.requester.post_request(setting.id, payload=payload)

    # TODO
    # {
    #   "aliases" : [ ] ,
    #   "description" : "no description" ,
    #   "ecNumbers" : [ ] ,
    #   "id" : "http://localhost:8080/setting/fc0d27ee-23bc-479c-96aa-06a05d0d92b4/simple-rule/ae1f5b7d-36d4-4309-9437-4fce69a35e83" ,
    #   "identifier" : "simple-rule" ,
    #   "includedInCompositeRule" : [ ] ,
    #   "isCompositeRule" : false ,
    #   "name" : "cyanate" ,
    #   "pathways" : [ ] ,
    #   "productFilterSmarts" : "" ,
    #   "productsSmarts" : "[#8-:1][C:2]#[N:3]" ,
    #   "reactantFilterSmarts" : "" ,
    #   "reactantsSmarts" : "[H][#8:1][C:2]#[N:3]" ,
    #   "reactions" : [ ] ,
    #   "reviewStatus" : "undefined" ,
    #   "scenarios" : [ ] ,
    #   "smirks" : "[H][#8:1][C:2]#[N:3]>>[#8-:1][C:2]#[N:3]" ,
    #   "transformations" : "Mappings:\nMap #1     at# 1  Charge = 0   -->  at# 0  Charge = -1         pIndex = 0\nMap #2     at# 2  Charge = 0   -->  at# 1  Charge = 0         pIndex = 1\nMap #3     at# 3  Charge = 0   -->  at# 2  Charge = 0         pIndex = 2\n"
    # }
    pass


class Pathway(ReviewableEnviPathObject):

    def get_nodes(self) -> List[Node]:
        return self._create_from_nested_json('nodes', Node)

    def get_edges(self) -> List[Edge]:
        return self._create_from_nested_json('links', Edge)

    def get_name(self) -> str:
        return self._get('pathwayName')

    def is_up_to_date(self) -> bool:
        return self._get('upToDate')

    def lastmodified(self) -> int:
        return self._get('lastModified')

    def is_completed(self) -> bool:
        return "true" == self._get('completed')

    def has_failed(self) -> bool:
        return "error" == self._get('completed')

    @staticmethod
    def create(package: Package, smiles: str, name: str = None, description: str = None,
               root_node_only: bool = False, setting: Setting = None):
        payload = {
            'smilesinput': smiles
        }

        # TODO the API allows creation of Setting on the fly. Should we support that here?

        if name:
            payload['name'] = name

        if description:
            payload['description'] = description

        if root_node_only:
            payload['rootOnly'] = "true"

        if setting:
            payload['selectedSetting'] = setting.get_id()

        res = package.requester.post_request(package.id + '/' + Endpoint.PATHWAY.value, params=None,
                                             payload=payload, allow_redirects=False)
        res.raise_for_status()
        return Pathway(package.requester, id=res.headers['Location'])


class User(enviPathObject):

    def get_email(self) -> str:
        return self._get('email')

    def get_forename(self) -> str:
        return self._get('forename')

    def get_surname(self) -> str:
        return self._get('surname')

    def get_default_group(self) -> 'Group':
        return Group(self.requester, id=self._get("defaultGroup")['id'])

    def get_groups(self) -> List['Group']:
        return self._create_from_nested_json('groups', Group)

    def get_default_package(self) -> 'Package':
        return Package(self.requester, id=self._get("defaultPackage")['id'])

    def get_default_setting(self) -> Optional['Setting']:
        try:
            return Setting(self.requester, id=self._get("defaultSetting")['id'])
        except ValueError:
            return None

    def get_settings(self) -> List['Setting']:
        return self._create_from_nested_json('settings', Setting)

    @staticmethod
    def create(ep, email: str, username: str, password: str):
        payload = {
            'username': username,
            'email': email,
            'password': password
        }
        raise NotImplementedError("Not (yet) implemented!")

    @staticmethod
    def register(ep, email: str, username: str, password: str):
        """
        Alias for 'create()'.
        :return:
        """
        return User.create(ep, email, username, password)

    @staticmethod
    def activate(ep, username, token) -> bool:
        params = {
            'username': username,
            'token': token
        }
        activation_url = '{}activation'.format(ep.BASE_URL)
        res = ep.requester.get_request(activation_url, params=params, allow_redirects=False)
        res.raise_for_status()
        return 'activationSuccessful' in res.headers['Location']


class Group(enviPathObject):

    def create(self, **kwargs):
        raise NotImplementedError("Not (yet) implemented!")


##################
# Helper Classes #
##################

HalfLife = namedtuple('HalfLife', 'scenarioName, scenarioId, hl, hl_comment, hl_fit, hl_model, source')
ModelStatus = namedtuple('ModelStatus', 'progress, status, statusMessage')


class ECNumber(object):

    def __init__(self, ec_number: str, ec_name: str, pathways: List['Pathway']):
        self.ec_number = ec_number
        self.ec_name = ec_name
        self.pathways = pathways
