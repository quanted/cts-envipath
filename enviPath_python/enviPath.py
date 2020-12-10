# -*- coding: utf-8 -*-

from enviPath_python.utils import Endpoint
from requests import Session
from requests.adapters import HTTPAdapter
from enviPath_python.objects import *


class enviPath(object):
    """
    Object representing enviPath functionality.
    """

    def __init__(self, base_url, proxies=None):
        """
        Constructor with instance specification.
        :param base_url: The url of the enviPath instance.
        """
        self.BASE_URL = base_url if base_url.endswith('/') else base_url + '/'
        self.requester = enviPathRequester(proxies)

    def login(self, username, password):
        """
        Performs login.
        :param username: The username.
        :param password: The corresponding password.
        :return: None
        """
        self.requester.login(self.BASE_URL, username, password)

    def logout(self):
        """
        Performs logout.
        :return: None
        """
        self.requester.logout(self.BASE_URL)

    def who_am_i(self):
        """
        Method to get the currently logged in user.
        :return: User object.
        """
        params = {
            'whoami': 'true',
        }
        url = self.BASE_URL + Endpoint.USER.value
        user_data = self.requester._get_request(url, params=params).json()[Endpoint.USER.value][0]
        return User(self.requester, **user_data)

    def get_packages(self):
        """
        Gets all packages the logged in user has at least read permissions on.
        :return: List of Package objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.PACKAGE)

    def get_compounds(self):
        """
        Gets all compounds the logged in user has at least read permissions on.
        :return: List of Compound objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.COMPOUND)

    def get_reactions(self):
        """
        Gets all reactions the logged in user has at least read permissions on.
        :return: List of Reaction objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.REACTION)

    def get_rules(self):
        """
        Gets all rules the logged in user has at least read permissions on.
        :return: List of Reaction objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.RULE)

    def get_pathways(self):
        """
        Gets all pathways the logged in user has at least read permissions on.
        :return: List of Pathway objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.PATHWAY)

    def get_scenarios(self):
        """
        Gets all scenarios the logged in user has at least read permissions on.
        :return: List of Scenario objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.SCENARIO)

    def get_setting(self):
        """
        Gets all settings the logged in user has at least read permissions on.
        :return: List of Settings objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.SETTING)

    def get_users(self):
        """
        Gets all users the logged in user has at least read permissions on.
        :return: List of User objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.USER)

    def get_groups(self):
        """
        Gets all groups the logged in user has at least read permissions on.
        :return: List of Group objects.
        """
        return self.requester._get_objects(self.BASE_URL, Endpoint.GROUP)


class enviPathRequester(object):
    """
    Class performing all requests to the enviPath instance.
    """
    header = {'Accept': 'application/json'}

    ENDPOINT_OBJECT_MAPPING = {
        Endpoint.USER: User,
        Endpoint.PACKAGE: Package,
        Endpoint.COMPOUND: Compound,
        Endpoint.PATHWAY: Pathway,
        Endpoint.REACTION: Reaction,
        Endpoint.SCENARIO: Scenario,
        Endpoint.SETTING: Setting,
        Endpoint.RULE: Rule,
        Endpoint.NODE: Node,
        Endpoint.EDGE: Edge,
        Endpoint.STRUCTURE: Structure,
        Endpoint.GROUP: Group,
    }

    def __init__(self, proxies=None):
        """
        Setup session for cookies as well as avoiding unnecessary ssl-handshakes.
        """
        self.session = Session()
        self.session.mount('http://', HTTPAdapter())
        self.session.mount('https://', HTTPAdapter())
        if proxies:
            self.session.proxies = proxies

    def _get_request(self, url, params=None, payload=None):
        """
        Convenient method to perform GET request to given url with optional query parameters and data.
        :param url: The url to retrieve data from.
        :param params: Dictionary containing query parameters as key, value.
        :param payload: Data send within the body.
        :return: response object.
        """
        return self._request('GET', url, params, payload)

    def _post_request(self, url, params=None, payload=None):
        """
        Convenient method to perform POST request to given url with optional query parameters and data.
        :param url: The url for object creation, object manipulation.
        :param params: Dictionary containing query parameters as key, value.
        :param payload: Data send within the body.
        :return: response object.
        """
        return self._request('POST', url, params, payload)

    def _request(self, method, url, params=None, payload=None):
        """
        Method performing the actual request.
        :param method: HTTP method.
        :param url: url for request.
        :param params: parameters to send.
        :param payload: data to send.
        :return: response object.
        """
        response = self.session.request(method, url, params=params, data=payload, headers=self.header)
        response.raise_for_status()
        return response

    def get_json(self, id):
        return self._get_request(id)

    def login(self, url, username, password):
        """
        Performs login,
        :param url: Can be any valid enviPath url.
        :param username: The username.
        :param password: The corresponding password.
        :return: None
        """
        data = {
            'hiddenMethod': 'login',
            'loginusername': username,
            'loginpassword': password,
        }
        self._post_request(url, payload=data)

    def logout(self, url):
        """
        Performs logout.
        :param url: Can be any valid enviPath url.
        :return: None
        """
        data = {
            'hiddenMethod': 'logout',
        }
        self._post_request(url, payload=data)

    def _get_objects(self, base_url, endpoint):
        """
        Generic get method to retrieve objects.
        :param endpoint: Enum of Endpoint.
        :return: List of objects denoted by endpoint.
        """
        url = base_url + endpoint.value
        objs = self._get_request(url).json()[endpoint.value]
        return [self.ENDPOINT_OBJECT_MAPPING[endpoint](self, **obj) for obj in objs]

