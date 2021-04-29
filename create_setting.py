import requests
import json
import time
from enviPath_python.enviPath import *
from enviPath_python.objects import *

if __name__ == "__main__":

    INSTANCE_HOST = 'https://envipath.org/'
    eP = enviPath(INSTANCE_HOST)
    eP.login('kurtw555', '9Gr0uper0')
    EAWAG_BBD = '{}package/32de3cf4-e3e6-4168-956e-32fa5ddb0ce1'.format(INSTANCE_HOST)
    package = eP.get_package(EAWAG_BBD)
    packages = [package]

    setting = Setting.create(eP, packages,name='cts-d3-n128',depth_limit=3, node_limit=128)

    print('Success')
